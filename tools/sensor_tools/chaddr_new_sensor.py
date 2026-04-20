import minimalmodbus
import argparse
import sys

def change_modbus_address(serial_port, old_address, new_address):
    try:
        # Initialize the instrument with the current address
        instrument = minimalmodbus.Instrument(serial_port, old_address)
        
        # Serial port setup as per documentation 
        instrument.serial.baudrate = 9600
        instrument.serial.bytesize = 8
        instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 1.0

        # 1. Write the new address to Offset 0 
        # The document supports Function Code 0x06 for modifying data 
        instrument.write_register(0, new_address, functioncode=6)
        print(f"Address changed from {old_address} to {new_address} in volatile memory.")

        # 2. Re-initialize instrument with the NEW address to send the save command
        instrument.address = new_address

        # 3. Save to user zone 
        # Writing 0 to register 65535 saves data to permanent memory 
        instrument.write_register(65535, 0, functioncode=6)
        print(f"Configuration saved successfully to permanent memory.")
        
    except minimalmodbus.ModbusException as e:
        print(f"Modbus Exception: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Change SenTec Modbus RTU address')
    parser.add_argument('serial_port', type=str, help='Serial port (e.g., /dev/ttyUSB0 or COM3)')
    parser.add_argument('old_address', type=int, help='Current Modbus RTU address (1-255)')
    parser.add_argument('new_address', type=int, help='New Modbus RTU address to set (1-255)')
    
    args = parser.parse_args()

    if not (1 <= args.new_address <= 255):
        print("Error: New address must be between 1 and 255.")
        sys.exit(1)

    change_modbus_address(args.serial_port, args.old_address, args.new_address)
