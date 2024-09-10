import minimalmodbus
import serial
import os
import time
import logging
import struct
import math
import paho.mqtt.client as mqtt


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
        self.pressure_topic =  f"{config['pressure_sensor_device_id']}/sensors/{config['pressure_sensor_address']}"
        self.temprature_topic =  f"{config['pressure_sensor_device_id']}/sensors/temperature"
        self.humidity_topic =  f"{config['pressure_sensor_device_id']}/sensors/humidity"
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
        self.P = 0
        self.phi = 0.66 
        self.T = 87
    def setup_mqtt(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, _):
        self.logger.info("Connected to MQTT broker with result code " + str(rc))
        client.subscribe(self.pressure_topic)
        client.subscribe(self.temprature_topic)
        client.subscribe(self.humidity_topic)

    def on_message(self, client, userdata, msg):
        try:
            if msg.topic == self.pressure_topic:
                self.P = float(msg.payload.decode()) * 47.88 + 101300
                self.logger.info(f"Received temperature from MQTT: {float(msg.payload.decode())},calcualted is {self.P}")
            elif msg.topic == self.humidity_topic:
                self.phi = float(msg.payload.decode()) / 100.0
            elif msg.topic == self.temprature_topic:
                self.T = float(msg.payload.decode())
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")

    def read_32bit_register_as_float(self,address):
        try:
            # Read two 16-bit registers (4 bytes) from the given address
            registers = self.sensor.read_registers(address, 2, functioncode=3)
            print(f"Raw register values: {registers}")
            # Convert the two 16-bit registers to a 32-bit float using IEEE 754 format
            packed_data = struct.pack('>HH', registers[0], registers[1])
            value = struct.unpack('>I', packed_data)[0]
            return value
        except Exception as e:
            print(f"Error reading float from address {address}: {e}")
            return None
    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
    def calc(self,deltaP):
        phi = self.phi
        P = self.P
        T = self.T
        
        n1 = 0.0289652 * phi * P
        
        x = 7.5*(T-273.15)/(T+237.3)
        n2 = 0.018016 * phi * 6.1078 * 10 ** x
        
        nominator = n1 + n2
        denominator = 8.31446 * T
        
        ro = nominator / denominator
        
        qv = 0.032429 * math.sqrt(deltaP * 2 / ro)
        
        return qv
    
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
        register_address = 0x0424
        value = self.read_32bit_register_as_float(register_address)
        try:
            # Read two 16-bit registers (4 bytes) from the given address
            self.last_t = self.calc(value / 10000)
            # self.last_t = self.calc(self.last_t)
            # Convert the two 16-bit registers to a 32-bit float
            # self.last_t = struct.unpack('>i', struct.pack('>HH', registers[0], registers[1]))[0] / 10000
        except Exception as e:
            self.logger.error(f'ignored writing command {e}')
        finally:
            self.release_lock()
        return self.last_t
    
    def __del__(self):
        self.release_lock()