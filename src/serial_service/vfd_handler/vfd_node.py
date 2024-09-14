import json
import logging
import time
import threading
import paho.mqtt.client as mqtt

from serial_com.serial_com import SerialCom


class VFDController:
    def __init__(self, config_file, serial_com: SerialCom):
        self.load_config(config_file)
        self.serial_com = serial_com
        self.startstopAddr = 8192
        self.setFreqAddr = 8193
        self.readFreqAddr = 8451
        self.startCmd = 18
        self.stopCmd = 1
        self.startDec = 0
        self.setFreqDec = 2
        self.writeFC = 6
        self.readFC = 3

        self.logger = self.setup_logger()

        self.setup_mqtt()

    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.device_id = config["device_id"]
        self.address = int(config["vfd"]["address"])

        # MQTT configuration
        mqtt_config = config['mqtt']
        self.broker_host = mqtt_config['broker_host']
        self.broker_port = mqtt_config['broker_port']
        self.username = mqtt_config['username']
        self.password = mqtt_config['password']

    def setup_mqtt(self):
        self.client = mqtt.Client()
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        while True:
            try:
                self.client.connect(self.broker_host, self.broker_port, 60)
                break
            except Exception as e:
                time.sleep(10)
                self.logger.error('Broker not found, will retry.')
        self.client.loop_start()
        self.client.subscribe(f"{self.device_id}/vfd/command")

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"Connected to MQTT broker with result code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload.decode())
            command = message.get("command")
            parameter = message.get("parameter")

            if command == "start":
                self.start_vfd()
            elif command == "stop":
                self.stop_vfd()
            elif command == "set_frequency":
                if parameter is not None:
                    frequency = float(parameter)
                    self.set_frequency(frequency)
                else:
                    self.logger.error("Error: No frequency parameter provided.")
            elif command == "emergency_stop":
                threading.Thread(target=self.emergency_stop).start()
            else:
                self.logger.error(f"Unknown command: {command}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON message: {e}")

    def start_vfd(self):
        try:
            self.serial_com.write_register(self.address,self.startstopAddr, self.startCmd, self.startDec, self.writeFC)
        except Exception as e:
            self.logger.error(f"Ignored writing command: {e}")

        self.logger.info("Started VFD.")

    def stop_vfd(self):
        try:
            self.serial_com.write_register(self.address,self.startstopAddr, self.stopCmd, self.startDec, self.writeFC)
        except Exception as e:
            self.logger.error(f"Ignored writing command: {e}")

        self.logger.info("Stopped VFD.")

    def set_frequency(self, frequency):
        try:
            self.serial_com.write_register(self.address,self.setFreqAddr, frequency, self.setFreqDec, self.writeFC)
        except Exception as e:
            self.logger.error(f"Ignored writing command: {e}")

        self.logger.info(f"Set frequency: {frequency}")

    def emergency_stop(self):
        try:
            self.serial_com.write_register(self.address,self.startstopAddr, self.stopCmd, self.startDec, self.writeFC)
        except Exception as e:
            self.logger.error(f"Ignored writing command: {e}")
        while True:
            try:
                speed = self.serial_com.read_register(self.address,self.readFreqAddr, 2, self.readFC)
            except Exception as e:
                self.logger.error(f"Ignored reading command: {e}")
            if speed == 0:
                break
            self.logger.error(f"Waiting for VFD to respond, current speed is {speed}")
            time.sleep(0.1)
        self.logger.info("Emergency stop executed.")

    def publish_feedback(self):
        while True:
            try:
                speed = self.serial_com.read_register(self.address,self.readFreqAddr, 2, self.readFC)
                self.client.publish(f"{self.device_id}/vfd/feedback", speed)
            except Exception as e:
                self.logger.error(f"Failed to read VFD feedback: {e}")
            time.sleep(1)

    def run(self):
        feedback_thread = threading.Thread(target=self.publish_feedback)
        feedback_thread.daemon = False
        feedback_thread.start()
        while True:
            time.sleep(0.2)  # Keep the script running to handle MQTT messages


