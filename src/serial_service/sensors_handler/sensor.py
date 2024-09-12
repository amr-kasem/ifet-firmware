import os
import time
import logging

from serial_com.serial_com import SerialCom

class Sensor:
    def __init__(self, config, serial_com:SerialCom):
        self.serial_com = serial_com
        self.release_lock()
        self.name = config["name"]
        self.debug = config["debug"]
        self.frequency = config["frequency"]
        self.logger = self.setup_logger()
        self.last_t = 0
        
    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
    

    def read(self):
        try:
            self.last_t = self.serial_com.read_float(1028, 3) * 144
        except:
            self.logger.error('ignored writing [read] command')
        return self.last_t
    
    def __del__(self):
        self.release_lock()