# import RPi.GPIO as GPIO
# try:
#     import RPi.GPIO
# except (RuntimeError, ModuleNotFoundError):
#     import fake_rpigpio.utils
#     fake_rpigpio.utils.install()
# from fake_rpigpio import RPi
import RPi.GPIO as GPIO
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import paho.mqtt.client as mqtt
from logging.handlers import RotatingFileHandler

class ValveController:
    def __init__(self, config_file):
        self.logger = self.setup_logger()

        try:
            with open(config_file) as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading configuration file: {e}", exc_info=True)
            raise

        self.valves = config.get('valves', [])
        self.device_id = config.get('device_id')
        mqtt_config = config.get('mqtt', {})
        self.broker_host = mqtt_config.get('broker_host')
        self.broker_port = mqtt_config.get('broker_port')
        self.username = mqtt_config.get('username')
        self.password = mqtt_config.get('password')
        
        GPIO.setmode(GPIO.BOARD)  # Use Broadcom SOC channel numbering

        for valve in self.valves:
            pin = valve.get('pin')
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Initialize MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.username, self.password)

    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        os.makedirs('logs', exist_ok=True) 
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        fh = RotatingFileHandler('logs/valve_controller.log', maxBytes=1_000_000, backupCount=5)
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        logger.addHandler(ch)
        logger.addHandler(fh)
        return logger

    def connect_mqtt(self):
        while True:
            try:
                self.client.connect(self.broker_host, self.broker_port)
                self.client.loop_start()
                break
            except Exception as e:
                self.logger.error(f"MQTT connection failed: {e}", exc_info=True)
                time.sleep(5)  # Retry after 5 seconds

    def on_connect(self, client, userdata, flags, rc, prop):
        self.logger.info(f"Connected to MQTT broker with result code {rc}")
        # Subscribe to valve control topics
        for valve in self.valves:
            topic = f"{self.device_id}/valves/{valve['name']}"
            self.client.subscribe(topic)
            self.logger.info(f"Subscribed to topic: {topic}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic.split('/')[-1]
            state = int(msg.payload)
            self.set_valve_state(topic, state)
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    def set_valve_state(self, valve_name, state):
        retry_count = 3
        for i in range(retry_count):
            try:
                for valve in self.valves:
                    if valve['name'] == valve_name:
                        pin = valve['pin']
                        GPIO.output(pin, GPIO.HIGH if state == 1 else GPIO.LOW)
                        self.logger.info(f"Valve '{valve_name}' state set to {state}")
                        break
            except Exception as e:
                self.logger.error(f"Failed to set state for valve '{valve_name}': {e}", exc_info=True)
                time.sleep(1)  # Wait for 1 second before retrying
            else:
                return
        self.logger.error(f"Failed to set state for valve '{valve_name}' after {retry_count} retries")

    def run(self):
        self.connect_mqtt()
        while True:
            try:
                self.client.publish(f'{self.device_id}/valves/status', json.dumps({v['name']: GPIO.input(v['pin']) for v in self.valves}))
                time.sleep(0.2)  # Keep the script running to handle MQTT messages
            except Exception as e:
                self.logger.error(f"Error during run loop: {e}", exc_info=True)
            
    def cleanup(self):
        GPIO.cleanup()
        self.client.loop_stop()
        self.client.disconnect()
        
    def on_disconnect(self, client, userdata, rc,_,__):
        if rc != 0:
            self.logger.warning("Disconnected from MQTT broker. Reconnecting...")
            self.client.loop_stop()
            self.connect_mqtt()

if __name__ == "__main__":
    config_file = "config.json"
    controller = ValveController(config_file)

    try:
        controller.run()
        pass
        
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Cleaning up GPIO and MQTT...")
        controller.cleanup()
    controller.cleanup()