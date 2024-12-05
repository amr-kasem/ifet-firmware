import minimalmodbus
import argparse
import sys

def change_modbus_address(serial_port, old_address, new_address):
    try:
        instrument = minimalmodbus.Instrument(serial_port, old_address)
        instrument.serial.baudrate = 9600  # Set baudrate as needed
        instrument.serial.timeout = 0.1    # Set timeout as needed

        # Change the Modbus address
        instrument.address = new_address

        print(f"Modbus RTU address changed from {old_address} to {new_address}")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus Exception: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Change Modbus RTU address')
    parser.add_argument('serial_port', type=str, help='Serial port of the Modbus device')
    parser.add_argument('old_address', type=int, help='Old Modbus RTU address')
    parser.add_argument('new_address', type=int, help='New Modbus RTU address')
    args = parser.parse_args()

    change_modbus_address(args.serial_port, args.old_address, args.new_address)
