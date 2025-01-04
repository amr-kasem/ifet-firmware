import json
import paho.mqtt.client as mqtt
import logging
import time

from sensors_handler.sensor import Sensor as PressureSensor
from sensors_handler.flow_sensor import Sensor as FlowSensor
from serial_com.serial_com import SerialCom

class SensorHandler:
    def __init__(self, config_file, serial_com : SerialCom):
        self.serial_com = serial_com
        self.sensors: list = []
        self.load_config(config_file)
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_connected = False
        self.logger = self.setup_logger()  # Initialize logger with class name
        self.connect_mqtt_broker()
                
    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
    def load_config(self, config_file):
        with open(config_file) as f:
            config = json.load(f)
            self.device_id = config["device_id"]
            self.mqtt_config = config["mqtt"]
            for sensor_config in config["sensors"]:
                self.add_sensor(sensor_config)

    def add_sensor(self, sensor_config):
        if sensor_config['type'] == 'pressure':
            sensor = PressureSensor(sensor_config,serial_com=self.serial_com)
            self.sensors.append(sensor)
        elif sensor_config['type'] == 'flow':
            sensor = FlowSensor(sensor_config,serial_com=self.serial_com)
            self.sensors.append(sensor)

    def connect_mqtt_broker(self):
        while True:
            try:
                self.mqtt_client.username_pw_set(self.mqtt_config["username"], self.mqtt_config["password"])
                self.mqtt_client.connect(self.mqtt_config["broker_host"], self.mqtt_config["broker_port"])
                self.mqtt_client.loop_start()
                break
            except Exception as e:
                self.logger.error(f"Failed to connect to MQTT broker: {e}")
                time.sleep(5)

    def on_mqtt_connect(self, client, userdata, flags, rc,prop):
        if rc == 0:
            self.logger.info("Connected to MQTT broker")
            self.mqtt_connected = True
        else:
            self.logger.error("Failed to connect to MQTT broker")

    def on_mqtt_disconnect(self, client, userdata, rc,_,__):
        self.logger.warning("Disconnected from MQTT broker")
        self.mqtt_connected = False
        self.connect_mqtt_broker()

    def send_sensor_reading(self, sensor :PressureSensor):
        topic = f"{self.device_id}/sensors/{sensor.address}"
        try:
            if self.mqtt_connected:
                sensor_reading = sensor.read()
                self.mqtt_client.publish(topic, int(sensor_reading*100)/100)
                self.logger.info(f"Published reading for {sensor.name}: {sensor_reading} on {topic}")
            else:
                self.logger.warning("MQTT broker not connected. Cannot publish reading.")
        except Exception as e:
            # self.logger.error(f"Error sending reading for {sensor.name}: {e}")
            pass

    def run(self):
        while True:
            for sensor in self.sensors:
                self.send_sensor_reading(sensor)
            time.sleep( 1 / 50)  # Adjust as needed

    def stop(self):
        self.mqtt_client.disconnect()

