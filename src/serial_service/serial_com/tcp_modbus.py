from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import json
import struct
from typing import Union
from .modbus_com import ModbusCom

class ModbusTcpCom(ModbusCom):
    def __init__(self, config: dict):
        self.host = config["host"]
        self.port = config.get("port", 502)  # Default Modbus TCP port
        self.timeout = config.get("timeout", 3)
        self.unit_id = config.get("address", 1)  # Default unit ID
        
        self.client = ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)

    def _execute_with_lock(self, address, func, *args, **kwargs):
        """Not Used anymore"""
        pass

    def _connect(self):
        """Ensure connection is established."""
        if not self.client.connected:
            if not self.client.connect():
                raise ConnectionError(f"Failed to connect to {self.host}:{self.port}")

    def read_float(self, address: int, register: int, number_of_registers: int = 2):
        """Read float value from holding registers (32-bit float requires 2 registers)."""
        self._connect()
        print('wil read')
        result = self.client.read_holding_registers(register, count=number_of_registers, slave=address)
        if result.isError():
            raise ModbusException(f"Failed to read float from register {register}")
        # Convert two 16-bit registers to 32-bit float
        combined = (result.registers[0] << 16) | result.registers[1]
        return struct.unpack('>f', struct.pack('>I', combined))[0]

    def read_int(self, address: int, register: int, number_of_registers: int = 1):
        """Read integer value from holding registers."""
        self._connect()
        result = self.client.read_holding_registers(register, count=number_of_registers, slave=address)
        if result.isError():
            raise ModbusException(f"Failed to read int from register {register}")
        if number_of_registers == 1:
            return result.registers[0]
        else:
            # For multi-register integers, combine them
            combined = 0
            for i, reg_val in enumerate(result.registers):
                combined |= (reg_val << (16 * (number_of_registers - 1 - i)))
            return combined

    def read_string(self, address: int, register: int, number_of_registers: int):
        """Read string value from holding registers."""
        self._connect()
        result = self.client.read_holding_registers(register, count=number_of_registers, slave=address)
        if result.isError():
            raise ModbusException(f"Failed to read string from register {register}")
        # Convert registers to string
        byte_data = []
        for reg_val in result.registers:
            byte_data.extend([(reg_val >> 8) & 0xFF, reg_val & 0xFF])
        return bytes(byte_data).decode('ascii').rstrip('\x00')

    def write_float(self, address: int, register: int, value: float, number_of_decimals: int = 0):
        """Write float value to holding registers."""
        self._connect()
        # Convert float to two 16-bit registers
        packed = struct.pack('>f', value)
        combined = struct.unpack('>I', packed)[0]
        high_reg = (combined >> 16) & 0xFFFF
        low_reg = combined & 0xFFFF
        
        result = self.client.write_registers(register, [high_reg, low_reg], device_id=address)
        if result.isError():
            raise ModbusException(f"Failed to write float to register {register}")
        return result

    def write_int(self, address: int, register: int, value: int):
        """Write integer value to holding register."""
        self._connect()
        result = self.client.write_register(register, value, device_id=address)
        if result.isError():
            raise ModbusException(f"Failed to write int to register {register}")
        return result

    def write_string(self, address: int, register: int, value: str):
        """Write string value to holding registers."""
        self._connect()
        # Pad string to even length
        if len(value) % 2:
            value += '\x00'
        
        # Convert string to registers
        registers = []
        for i in range(0, len(value), 2):
            high_byte = ord(value[i]) if i < len(value) else 0
            low_byte = ord(value[i + 1]) if i + 1 < len(value) else 0
            registers.append((high_byte << 8) | low_byte)
        
        result = self.client.write_registers(register, registers, slave=address)
        if result.isError():
            raise ModbusException(f"Failed to write string to register {register}")
        return result

    def read_register(self, address: int, register: int, number_of_registers: int, functioncode: int = 3):
        """Read registers using specified function code."""
        self._connect()
        if functioncode == 3:  # Read Holding Registers
            result = self.client.read_holding_registers(register, count=number_of_registers, slave=address)
        elif functioncode == 4:  # Read Input Registers
            result = self.client.read_input_registers(register, count=number_of_registers, slave=address)
        elif functioncode == 1:  # Read Coils
            result = self.client.read_coils(register, count=number_of_registers, slave=address)
            return result.bits[:number_of_registers] if not result.isError() else result
        elif functioncode == 2:  # Read Discrete Inputs
            result = self.client.read_discrete_inputs(register, count=number_of_registers, slave=address)
            return result.bits[:number_of_registers] if not result.isError() else result
        else:
            raise ValueError(f"Unsupported function code: {functioncode}")
        
        if result.isError():
            raise ModbusException(f"Failed to read register {register} with function code {functioncode}")
        
        return result.registers if hasattr(result, 'registers') else result

    def write_register(
        self, 
        address: int, 
        registeraddress: int, 
        value: Union[int, float], 
        number_of_decimals: int = 0, 
        functioncode: int = 16, 
        signed: bool = False
    ) -> None:
        """Write a value to a specified register."""
        self._connect()
        
        # Scale the value if decimals are specified
        if number_of_decimals > 0:
            value = int(value * (10 ** number_of_decimals))
        
        # Handle signed values
        if signed and value < 0:
            value = value & 0xFFFF  # Convert to unsigned 16-bit
        
        if functioncode == 5:  # Write Single Coil
            result = self.client.write_coil(registeraddress, bool(value), device_id=address)
        elif functioncode == 6:  # Write Single Register
            result = self.client.write_register(registeraddress, int(value), device_id=address)
        elif functioncode == 16:  # Write Multiple Registers
            result = self.client.write_register(registeraddress, int(value), device_id=address)
        else:
            raise ValueError(f"Unsupported function code: {functioncode}")
        
        if result.isError():
            raise ModbusException(f"Failed to write register {registeraddress}")

    def read_block(self, address: int, register: int, number_of_registers: int):
        """Read a block of holding registers."""
        self._connect()
        result = self.client.read_holding_registers(register, count=number_of_registers, slave=address)
        if result.isError():
            raise ModbusException(f"Failed to read block from register {register}")
        return result.registers

    def close(self):
        """Close the TCP connection."""
        if self.client.connected:
            self.client.close()
        
    def __del__(self):
        self.close()