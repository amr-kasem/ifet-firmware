from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import json
import threading
import logging
from logging.handlers import RotatingFileHandler
import struct
from typing import Union
from .modbus_com import ModbusCom

class ModbusTcpCom(ModbusCom):
    def __init__(self, config_file: str):
        self.lock = threading.Lock()
        try:
            with open(config_file) as f:
                config = json.load(f)["tcp"]
                self.host = config["host"]
                self.port = config.get("port", 502)  # Default Modbus TCP port
                self.timeout = config.get("timeout", 3)
                self.unit_id = config.get("unit_id", 1)  # Default unit ID
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            logging.error(f"Error loading configuration: {e}", exc_info=True)
            raise

        self.client = ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)
        
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler("logs/serial_com.log", maxBytes=1_000_000, backupCount=5),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _execute_with_lock(self, address: int, func, *args, **kwargs):
        """Helper method to execute a function with address setting and locking."""
        with self.lock:
            self.logger.info(f"Acquiring lock for operation at address {address}")
            try:
                if not self.client.connected:
                    connection = self.client.connect()
                    if not connection:
                        raise ConnectionError(f"Failed to connect to {self.host}:{self.port}")
                
                result = func(address, *args, **kwargs)
                self.logger.info(f"Operation successful for address {address}")
                return result
            except Exception as e:
                self.logger.warn(f"Error during operation at address {address}: {e}", exc_info=True)
                raise
            finally:
                self.logger.info(f"Releasing lock for address {address}")

    def read_float(self, address: int, register: int, number_of_registers: int = 2):
        """Read float value from holding registers (32-bit float requires 2 registers)."""
        def _read_float(unit_id, reg, count):
            result = self.client.read_holding_registers(reg, count, slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to read float from register {reg}")
            # Convert two 16-bit registers to 32-bit float
            combined = (result.registers[0] << 16) | result.registers[1]
            return struct.unpack('>f', struct.pack('>I', combined))[0]
        
        return self._execute_with_lock(address, _read_float, register, number_of_registers)

    def read_int(self, address: int, register: int, number_of_registers: int = 1):
        """Read integer value from holding registers."""
        def _read_int(unit_id, reg, count):
            result = self.client.read_holding_registers(reg, count, slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to read int from register {reg}")
            if count == 1:
                return result.registers[0]
            else:
                # For multi-register integers, combine them
                combined = 0
                for i, reg_val in enumerate(result.registers):
                    combined |= (reg_val << (16 * (count - 1 - i)))
                return combined
        
        return self._execute_with_lock(address, _read_int, register, number_of_registers)

    def read_string(self, address: int, register: int, number_of_registers: int):
        """Read string value from holding registers."""
        def _read_string(unit_id, reg, count):
            result = self.client.read_holding_registers(reg, count, slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to read string from register {reg}")
            # Convert registers to string
            byte_data = []
            for reg_val in result.registers:
                byte_data.extend([(reg_val >> 8) & 0xFF, reg_val & 0xFF])
            return bytes(byte_data).decode('ascii').rstrip('\x00')
        
        return self._execute_with_lock(address, _read_string, register, number_of_registers)

    def write_float(self, address: int, register: int, value: float, number_of_decimals: int = 0):
        """Write float value to holding registers."""
        def _write_float(unit_id, reg, val, decimals):
            # Convert float to two 16-bit registers
            packed = struct.pack('>f', val)
            combined = struct.unpack('>I', packed)[0]
            high_reg = (combined >> 16) & 0xFFFF
            low_reg = combined & 0xFFFF
            
            result = self.client.write_registers(reg, [high_reg, low_reg], slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to write float to register {reg}")
            return result
        
        return self._execute_with_lock(address, _write_float, register, value, number_of_decimals)

    def write_int(self, address: int, register: int, value: int):
        """Write integer value to holding register."""
        def _write_int(unit_id, reg, val):
            result = self.client.write_register(reg, val, slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to write int to register {reg}")
            return result
        
        return self._execute_with_lock(address, _write_int, register, value)

    def write_string(self, address: int, register: int, value: str):
        """Write string value to holding registers."""
        def _write_string(unit_id, reg, val):
            # Pad string to even length
            if len(val) % 2:
                val += '\x00'
            
            # Convert string to registers
            registers = []
            for i in range(0, len(val), 2):
                high_byte = ord(val[i]) if i < len(val) else 0
                low_byte = ord(val[i + 1]) if i + 1 < len(val) else 0
                registers.append((high_byte << 8) | low_byte)
            
            result = self.client.write_registers(reg, registers, slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to write string to register {reg}")
            return result
        
        return self._execute_with_lock(address, _write_string, register, value)

    def read_register(self, address: int, register: int, number_of_registers: int, functioncode: int = 3):
        """Read registers using specified function code."""
        def _read_register(unit_id, reg, count, func_code):
            if func_code == 3:  # Read Holding Registers
                result = self.client.read_holding_registers(reg, count, slave=unit_id)
            elif func_code == 4:  # Read Input Registers
                result = self.client.read_input_registers(reg, count, slave=unit_id)
            elif func_code == 1:  # Read Coils
                result = self.client.read_coils(reg, count, slave=unit_id)
                return result.bits[:count] if not result.isError() else result
            elif func_code == 2:  # Read Discrete Inputs
                result = self.client.read_discrete_inputs(reg, count, slave=unit_id)
                return result.bits[:count] if not result.isError() else result
            else:
                raise ValueError(f"Unsupported function code: {func_code}")
            
            if result.isError():
                raise ModbusException(f"Failed to read register {reg} with function code {func_code}")
            
            return result.registers if hasattr(result, 'registers') else result
        
        return self._execute_with_lock(address, _read_register, register, number_of_registers, functioncode)

    def write_register(
        self, 
        address: int, 
        registeraddress: int, 
        value: Union[int, float], 
        number_of_decimals: int = 0, 
        functioncode: int = 16, 
        signed: bool = False
    ) -> None:
        """
        Writes a value to a specified register.

        :param address: The address of the device to communicate with (unit ID).
        :param registeraddress: The address of the register to write to.
        :param value: The value to write. Can be an integer or a float.
        :param number_of_decimals: Number of decimals for scaling the value (default is 0).
        :param functioncode: Modbus function code to use (default is 16).
        :param signed: Whether the value is signed (default is False).
        """
        def _write_register(unit_id, reg_addr, val, decimals, func_code, is_signed):
            # Scale the value if decimals are specified
            if decimals > 0:
                val = int(val * (10 ** decimals))
            
            # Handle signed values
            if is_signed and val < 0:
                val = val & 0xFFFF  # Convert to unsigned 16-bit
            
            if func_code == 5:  # Write Single Coil
                result = self.client.write_coil(reg_addr, bool(val), slave=unit_id)
            elif func_code == 6:  # Write Single Register
                result = self.client.write_register(reg_addr, int(val), slave=unit_id)
            elif func_code == 16:  # Write Multiple Registers
                result = self.client.write_register(reg_addr, int(val), slave=unit_id)
            else:
                raise ValueError(f"Unsupported function code: {func_code}")
            
            if result.isError():
                raise ModbusException(f"Failed to write register {reg_addr}")
            
            self.logger.info(f"Successfully wrote value {value} to register {registeraddress} at address {address}.")
            return result
        
        self._execute_with_lock(address, _write_register, registeraddress, value, number_of_decimals, functioncode, signed)

    def read_block(self, address: int, register: int, number_of_registers: int):
        """Read a block of holding registers."""
        def _read_block(unit_id, reg, count):
            result = self.client.read_holding_registers(reg, count, slave=unit_id)
            if result.isError():
                raise ModbusException(f"Failed to read block from register {reg}")
            return result.registers
        
        return self._execute_with_lock(address, _read_block, register, number_of_registers)

    def close(self):
        """Close the TCP connection."""
        if self.client.connected:
            self.client.close()
        
    def __del__(self):
        self.close()