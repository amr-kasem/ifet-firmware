import os
import time
import logging

from serial_com import ModbusCom, ModbusTcpCom

class Sensor:
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
        
    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Add file handler
        fh = logging.handlers.RotatingFileHandler("logs/sensor.log", maxBytes=1_000_000, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        # Also add stream handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
    

    def read(self):
        try:
            raw_value = self.com_port.read_float(self.address, 7, 2, 4)
            self.logger.info(f'sensor [{self.address}] raw value {raw_value}')
            self.last_t = raw_value * 204.816
            self.logger.info(f'sensor [{self.address}] value {self.last_t}')
            print(f'sensor [{self.address}] value is {self.last_t} ')
        except Exception as e:
            self.logger.error(f'failed to read sensor [{self.address}] command due to {e}')
            pass
        return self.last_t
    
