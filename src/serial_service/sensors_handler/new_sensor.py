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
        # Optional per-sensor unit conversion (default preserves raw PSI reading).
        self.scale = float(config.get("scale", 1))
        self.unit = config.get("unit", "PSI")
        if tcp:
            self.com_port = ModbusTcpCom(config)
        else: 
            self.com_port = com_port
        if self.com_port is None:
            raise ValueError(f"NewSensor '{self.name}': com_port must be provided when tcp=False")
    def setup_logger(self):
        logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")
        if not logger.handlers:
            logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(ch)
        return logger
    

    def read(self):
        try:
            self.last_t = self.com_port.read_float(self.address, 22, 3) * self.scale
            self.logger.info(f'sensor [{self.address}] value {self.last_t} {self.unit}')
            print(f'sensor [{self.address}] value is {self.last_t} {self.unit}')
        except Exception as e:
            self.logger.error(f'failed to read sensor [{self.address}] command due to {e}')
            pass
        return self.last_t
    
