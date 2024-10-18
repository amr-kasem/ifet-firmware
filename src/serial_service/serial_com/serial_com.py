import minimalmodbus
import serial
import json
import threading
import logging
from logging.handlers import RotatingFileHandler
import os


from typing import Union

class SerialCom:
    def __init__(self, config_file):
        self.lock = threading.Lock()
        try:
            with open(config_file) as f:
                config = json.load(f)["serial"]
                self.port = config["port"]
                self.baudrate = config["baudrate"]
                self.bytesize = config["bytesize"]
                self.parity = getattr(serial, config["parity"])
                self.stopbits = config["stopbits"]
                self.timeout = config["timeout"]
                self.mode = getattr(minimalmodbus, config["mode"])
                self.clear_buffers_before_each_transaction = config["clear_buffers_before_each_transaction"]
                self.close_port_after_each_call = config["close_port_after_each_call"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            logging.error(f"Error loading configuration: {e}", exc_info=True)
            raise

        self.comport = minimalmodbus.Instrument(self.port, 1)  # Default address, will be changed in methods
        self.comport.serial.baudrate = self.baudrate
        self.comport.serial.bytesize = self.bytesize
        self.comport.serial.parity = self.parity
        self.comport.serial.stopbits = self.stopbits
        self.comport.serial.timeout = self.timeout
        self.comport.mode = self.mode
        self.comport.clear_buffers_before_each_transaction = self.clear_buffers_before_each_transaction
        self.comport.close_port_after_each_call = self.close_port_after_each_call
        
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
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
            self.logger.info(f"Acquiring lock and setting address to {address}")
            self.comport.address = address
            try:
                result = func(*args, **kwargs)
                self.logger.info(f"Operation successful for address {address}")
                return result
            except Exception as e:
                self.logger.warn(f"Error during operation at address {address}: {e}", exc_info=True)
                raise
            finally:
                self.logger.info(f"Releasing lock for address {address}")

    def read_float(self, address: int, register: int, number_of_registers: int):
        return self._execute_with_lock(address, self.comport.read_float, register, number_of_registers)

    def read_int(self, address: int, register: int, number_of_registers: int):
        return self._execute_with_lock(address, self.comport.read_int, register, number_of_registers)

    def read_string(self, address: int, register: int, number_of_registers: int):
        return self._execute_with_lock(address, self.comport.read_string, register, number_of_registers)

    def write_float(self, address: int, register: int, value: float, number_of_decimals: int = 0):
        return self._execute_with_lock(address, self.comport.write_float, register, value, number_of_decimals)

    def write_int(self, address: int, register: int, value: int):
        return self._execute_with_lock(address, self.comport.write_int, register, value)

    def write_string(self, address: int, register: int, value: str):
        return self._execute_with_lock(address, self.comport.write_string, register, value)

    def read_register(self, address: int, register: int, number_of_registers: int, functioncode: int = 1):
        return self._execute_with_lock(address, self.comport.read_register, register, number_of_registers, functioncode)

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

        :param address: The address of the device to communicate with.
        :param registeraddress: The address of the register to write to.
        :param value: The value to write. Can be an integer or a float.
        :param number_of_decimals: Number of decimals for scaling the value (default is 0).
        :param functioncode: Modbus function code to use (default is 16).
        :param signed: Whether the value is signed (default is False).
        """
        def write_func():
            if number_of_decimals > 0:
                self.comport.write_register(
                    registeraddress, 
                    value, 
                    number_of_decimals=number_of_decimals, 
                    functioncode=functioncode, 
                    signed=signed
                )
            else:
                self.comport.write_register(
                    registeraddress, 
                    int(value), 
                    number_of_decimals=number_of_decimals, 
                    functioncode=functioncode, 
                    signed=signed
                )
            self.logger.info(f"Successfully wrote value {value} to register {registeraddress} at address {address}.")
        
        self._execute_with_lock(address, write_func)

    def read_block(self, address: int, register: int, number_of_registers: int):
        return self._execute_with_lock(address, self.comport.read_block, register, number_of_registers)

    def close(self):
        self.comport.serial.close()
        
    def __del__(self):
        self.close()