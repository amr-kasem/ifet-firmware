import minimalmodbus
import struct

# Configure the serial connection to the Modbus device
instrument = minimalmodbus.Instrument('/dev/ttyACM0', 11)  # port name, slave address (in decimal)
instrument.serial.baudrate = 9600
instrument.serial.bytesize = 8
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 1  # seconds

# Function to read a 32-bit register value (4 bytes)
def read_32bit_register_as_float(address):
    try:
        # Read two 16-bit registers (4 bytes) from the given address
        registers = instrument.read_registers(address, 2, functioncode=3)
        print(f"Raw register values: {registers}")
        # Convert the two 16-bit registers to a 32-bit float using IEEE 754 format
        packed_data = struct.pack('>HH', registers[1], registers[0])
        value = struct.unpack('>I', packed_data)[0]
        return value
    except Exception as e:
        print(f"Error reading float from address {address}: {e}")
        return None

# Address of the register to read (0x0405 in hex is 1029 in decimal)
register_address = 0x042D
# Read the value from the register
value = read_32bit_register_as_float(register_address)

print(f'The value read from register 0x0405 is: {value / 10000}')
