# Python CLI for Parallel EEPROM Programmer
# Colin Maykish
# May 2021

import argparse
import serial
import time


def main():
    parser = argparse.ArgumentParser(description="Parallel EEPROM Programmer")

    parser.add_argument("-d", "--device", action="store", type=str, nargs=1)
    parser.add_argument("-r", "--read", action="store_true")
    parser.add_argument("-w", "--write", action="store_true")
    parser.add_argument("-f", "--file", action="store", type=str, nargs=1)
    parser.add_argument("-l", "--limit", action="store", type=int, nargs=1)
    parser.add_argument("-o", "--offset", action="store", type=int, nargs=1, default=0)
    parser.add_argument("-c", "--clear", action="store_true")
    parser.add_argument("--verify", action="store_true")

    args = parser.parse_args()

    # Open serial port
    ser = serial.Serial(args.device[0], 115200)

    time.sleep(1)

    if not ser.is_open:
        print("Failed to open " + ser.name)
        exit(1)

    ser.flushInput()

    print("Connected to " + ser.name + " at " + str(ser.baudrate))

    addr = args.offset

    if args.read:
        print("Reading EEPROM")

        for x in range(args.limit[0]):
            command = "RD" + hex(addr)[2:].zfill(4).upper() + '\n'
            b = command.encode()
            ser.write(b)

            # Wait for response
            response = ser.readline().decode().strip()
            print(hex(addr)[2:].zfill(4).upper() + " : " + response.zfill(2))
            addr += 1

    elif args.write:
        print("Writing file " + args.file[0] + " to EEPROM")

        # Open binary file
        with open(args.file[0], mode='rb') as file:
            contents = file.read()

            print("Input file size: " + str(len(contents)))

            print("Limiting to first " + str(args.limit[0]) + " bytes")

            if args.write:
                for b in contents:
                    command = "WR" + \
                        hex(addr)[2:].zfill(4).upper() + \
                        hex(b)[2:].zfill(2).upper() + '\n'
                    b = command.encode()
                    ser.write(b)
                    addr += 1

                    # Wait for response
                    response = ser.readline().decode().strip()

                    if response != "DONE":
                        print(response)
                        ser.close()
                        print("Closed " + ser.name)
                        exit(1)
                    else:
                        print(
                            str(addr - args.offset) + " / " + str(len(contents)))

                    if args.limit[0] is not None and addr >= args.limit[0] + args.offset:
                        break

    elif args.clear:
        # Check that limit is set
        if args.limit is None:
            print("Error: limit must be set to clear EEPROM using the -l flag.")
            ser.close()
            exit(1)

        print("Wiping EEPROM")
        for x in range(args.limit[0]):
            command = "WR" + \
                hex(addr)[2:].zfill(4).upper() + \
                hex(255)[2:].zfill(2).upper() + '\n'
            b = command.encode()
            ser.write(b)
            addr += 1

            # Wait for response
            response = ser.readline().decode().strip()

            if response != "DONE":
                print(response)
                ser.close()
                print("Closed " + ser.name)
                exit(1)
            else:
                print(str(addr - args.offset) + " / " + str(args.limit[0]))

    elif args.verify:
        print("Comparing contents of EEPROM to file " + args.file[0])

        start_addr = args.offset

        # Open binary file
        with open(args.file[0], mode='rb') as file:
            file_contents = bytearray(file.read())

        limit = args.limit if args.limit else len(file_contents) 

        # Cut contents to start from 'addr' and specified limit
        file_contents = file_contents[addr : limit + addr]
        # Convert to list of single bytes
        file_contents = [bytes([b]) for b in file_contents]

        eeprom_contents = []

        for x in range(limit):
            command = "RD" + hex(addr)[2:].zfill(4).upper() + '\n'
            b = command.encode()
            ser.write(b)

            # Wait for response
            response = ser.readline().decode().strip()
            response = bytes.fromhex(response)
            eeprom_contents.append(response)

            # Continue
            addr += 1

        # Compare contents, collect errors
        errors = []
        for i in range(len(eeprom_contents)):
            if eeprom_contents[i] != file_contents[i]:
                errors.append(f"addr[{start_addr + i}] 0x{eeprom_contents[i].hex()} != 0x{file_contents[i].hex()}")

        # Print errors
        if errors:
            print("Check failed with " + str(len(errors)) + " errors:")

            if len(errors) > 10:
                print("Showing first 10 errors")

            errors = errors[:10]
            for error in errors:
                print(error)
        else:
            print("Check passed")

    ser.close()
    print("Closed " + ser.name)


main()
