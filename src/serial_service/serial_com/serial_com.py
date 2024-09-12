import minimalmodbus
import serial
from typing import Union

class SerialCom:
    def __init__(self, config):
        self.port = config["port"]
        self.address = int(config["address"])
        self.baudrate = config["baudrate"]
        self.bytesize = config["bytesize"]
        self.parity = getattr(serial, config["parity"])
        self.stopbits = config["stopbits"]
        self.timeout = config["timeout"]
        self.mode = getattr(minimalmodbus, config["mode"])
        self.clear_buffers_before_each_transaction = config["clear_buffers_before_each_transaction"]
        self.close_port_after_each_call = config["close_port_after_each_call"]
        self.comport = minimalmodbus.Instrument(self.port, self.address)
        self.comport.serial.baudrate = self.baudrate
        self.comport.serial.bytesize = self.bytesize
        self.comport.serial.parity = self.parity
        self.comport.serial.stopbits = self.stopbits
        self.comport.serial.timeout = self.timeout
        self.comport.mode = self.mode
        self.comport.clear_buffers_before_each_transaction = self.clear_buffers_before_each_transaction
        self.comport.close_port_after_each_call = self.close_port_after_each_call
        
    def read_float(self, register, number_of_registers):
        return self.comport.read_float(register, number_of_registers)
    
    def read_int(self, register, number_of_registers):
        return self.comport.read_int(register, number_of_registers)
    
    def read_string(self, register, number_of_registers):
        return self.comport.read_string(register, number_of_registers)
    
    def write_float(self, register, value):
        return self.comport.write_float(register, value)
    
    def write_int(self, register, value):
        return self.comport.write_int(register, value)
    
    def write_string(self, register, value):
        return self.comport.write_string(register, value)
    
    def read_register(self, register, number_of_registers,functioncode=1):
        return self.comport.read_register(register, number_of_registers,functioncode)
    
    def write_register(
        self, 
        registeraddress: int, 
        value: Union[int, float], 
        number_of_decimals: int = 0, 
        functioncode: int = 16, 
        signed: bool = False
    ) -> None:
        """
        Writes a value to a specified register.

        :param registeraddress: The address of the register to write to.
        :param value: The value to write. Can be an integer or a float.
        :param number_of_decimals: Number of decimals for scaling the value (default is 0).
        :param functioncode: Modbus function code to use (default is 16).
        :param signed: Whether the value is signed (default is False).
        """
        try:
            # Decide whether to write as integer or float based on number_of_decimals
            if number_of_decimals > 0:
                # Writes the value as a float if there are decimals to consider
                self.comport.write_register(
                    registeraddress, 
                    value, 
                    number_of_decimals=number_of_decimals, 
                    functioncode=functioncode, 
                    signed=signed
                )
            else:
                # Writes the value as an integer if there are no decimals
                self.comport.write_register(
                    registeraddress, 
                    int(value), 
                    number_of_decimals=number_of_decimals, 
                    functioncode=functioncode, 
                    signed=signed
                )
            print(f"Successfully wrote value {value} to register {registeraddress}.")
        except Exception as e:
            print(f"Error writing to register {registeraddress}: {e}")

    
    def read_block(self, register, number_of_registers):
        return self.comport.read_block(register, number_of_registers)
    
    def close(self):
        self.comport.close()
        
    def __del__(self):
        self.close()
        
    