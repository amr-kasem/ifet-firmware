import minimalmodbus
import serial
import sys

def scan_modbus_addresses(port, baudrate=9600, timeout=1, start_address=1, end_address=247):
    # Configure the serial connection
    instrument = minimalmodbus.Instrument(port, 1)  # Temporary address, will be changed in the loop
    instrument.serial.baudrate = baudrate
    instrument.serial.bytesize = 8
    instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = timeout  # seconds

    available_addresses = []

    print(f"Scanning Modbus addresses from {start_address} to {end_address}...")

    for address in range(start_address, end_address + 1):
        try:
            # Change the slave address in the loop
            instrument.address = address
            # Attempt to read a register (we use a common register address 1 for the check)
            instrument.read_register(1, 0, functioncode=3)
            print(f"Address {address} is available.")
            available_addresses.append(address)
        except (minimalmodbus.NoResponseError, minimalmodbus.InvalidResponseError, serial.SerialException):
            # Ignore errors indicating no response or invalid response, or serial communication errors
            pass

    print(f"Available addresses: {available_addresses}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <serial_port>")
        print("Example: python scan_modbus.py /dev/ttyUSB0")
        sys.exit(1)

    serial_port = sys.argv[1]
    scan_modbus_addresses(serial_port)