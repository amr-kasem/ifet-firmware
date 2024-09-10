import minimalmodbus
import serial
import os
import time
import logging

class Sensor:
    def __init__(self, config):
        self.name = config["name"]
        self.port = config["port"]
        self.release_lock()
        self.address = int(config["address"])
        self.baudrate = config["baudrate"]
        self.bytesize = config["bytesize"]
        self.parity = getattr(serial, config["parity"])
        self.stopbits = config["stopbits"]
        self.timeout = config["timeout"]
        self.mode = getattr(minimalmodbus, config["mode"])
        self.clear_buffers_before_each_transaction = config["clear_buffers_before_each_transaction"]
        self.close_port_after_each_call = config["close_port_after_each_call"]
        self.debug = config["debug"]
        self.frequency = config["frequency"]
        self.sensor = minimalmodbus.Instrument(self.port, self.address)
        self.sensor.serial.baudrate = self.baudrate
        self.sensor.serial.bytesize = self.bytesize
        self.sensor.serial.parity = self.parity
        self.sensor.serial.stopbits = self.stopbits
        self.sensor.serial.timeout = self.timeout
        self.sensor.mode = self.mode
        self.sensor.clear_buffers_before_each_transaction = self.clear_buffers_before_each_transaction
        self.sensor.close_port_after_each_call = self.close_port_after_each_call
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
    
    def acquire_lock(self):
        lock_file = f"/dev/shm/{os.path.basename(self.port)}.lock"
        while os.path.exists(lock_file):
            self.logger.info(f"Waiting for lock on {self.port}...")
            time.sleep(0.02)  # Adjust the delay as needed
        open(lock_file, 'w').close()  # Create the lock file

    def release_lock(self):
        lock_file = f"/dev/shm/{os.path.basename(self.port)}.lock"
        if os.path.exists(lock_file):
            os.remove(lock_file)  # Delete the lock file

    def read(self):
        self.acquire_lock()
        try:
            self.last_t = self.sensor.read_float(1028, 3) * 144
        except:
            self.logger.error('ignored writing command')
        finally:
            self.release_lock()
        return self.last_t
    
    def __del__(self):
        self.release_lock()