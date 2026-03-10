import minimalmodbus
import serial
import json
import threading
import logging
from logging.handlers import RotatingFileHandler
from abc import ABC, abstractmethod
from typing import Union

class ModbusCom(ABC):
    """Abstract base class for Modbus communication interfaces."""
    
    @abstractmethod
    def __init__(self, config_file: str):
        """Initialize the Modbus communication interface with configuration."""
        pass

    @abstractmethod
    def _execute_with_lock(self, address: int, func, *args, **kwargs):
        """Helper method to execute a function with address setting and locking."""
        pass
       
    @abstractmethod
    def read_float(self, address: int, register: int, number_of_registers: int, functioncode: int = 3):
        """Read float value from registers."""
        pass

    @abstractmethod
    def read_int(self, address: int, register: int, number_of_registers: int):
        """Read integer value from registers."""
        pass

    @abstractmethod
    def read_string(self, address: int, register: int, number_of_registers: int):
        """Read string value from registers."""
        pass

    @abstractmethod
    def write_float(self, address: int, register: int, value: float, number_of_decimals: int = 0):
        """Write float value to registers."""
        pass

    @abstractmethod
    def write_int(self, address: int, register: int, value: int):
        """Write integer value to register."""
        pass

    @abstractmethod
    def write_string(self, address: int, register: int, value: str):
        """Write string value to registers."""
        pass

    @abstractmethod
    def read_register(self, address: int, register: int, number_of_registers: int, functioncode: int = 1):
        """Read registers using specified function code."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def read_block(self, address: int, register: int, number_of_registers: int):
        """Read a block of registers."""
        pass

    @abstractmethod
    def close(self):
        """Close the communication connection."""
        pass
        
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()