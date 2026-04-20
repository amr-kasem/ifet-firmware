import os
import time
import logging

from serial_com import ModbusCom, ModbusTcpCom

class NewSensor:
    def __init__(self, config, com_port:ModbusCom = None, tcp = False):
        self.name = config["name"]
        self.address = int(config["address"])
        self.debug = config["debug"]
        self.logger = self.setup_logger()
        self.last_t = 0
        if tcp:
            self.com_port = ModbusTcpCom(config)
        else: 
            self.com_port = com_port
        self.com_port.write_register(self.address, 3, 3, 8)
    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        if self.debug:
            logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
    

    def read(self):
        try:
            self.last_t = self.com_port.read_float(self.address, 1028, 3) * 144
            self.logger.error(f'sensor [{self.address}] value {self.last_t}')
            print(f'sensor [{self.address}] value is {self.last_t} ')
        except Exception as e:
            self.logger.error(f'failed to read sensor [{self.address}] command due to {e}')
            pass
        return self.last_t
    
