import json
import logging
from logging.handlers import RotatingFileHandler
import time
import paho.mqtt.client as mqtt
from threading import Thread

class FakeValveController:
    def __init__(self, config_file):
        self.logger = self.setup_logger()

        with open(config_file) as f:
            config = json.load(f)
        self.valves = config.get('valves', [])
        self.device_id = config.get('device_id')
        mqtt_config = config.get('mqtt', {})
        self.broker_host = mqtt_config.get('broker_host')
        self.broker_port = mqtt_config.get('broker_port')
        self.username = mqtt_config.get('username')
        self.password = mqtt_config.get('password')
        
        # Initialize fake valve states
        self.valve_states = {valve['name']: 0 for valve in self.valves}

        # Initialize MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.username, self.password)

    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        fh = RotatingFileHandler('logs/fake_valve_controller.log', maxBytes=1_000_000, backupCount=5)
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
                self.logger.error(f"MQTT connection failed: {e}")
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
            self.logger.error(f"Error processing MQTT message: {e}")

    def set_valve_state(self, valve_name, state):
        if valve_name in self.valve_states:
            self.valve_states[valve_name] = state
            self.logger.info(f"Valve '{valve_name}' state set to {state}")
        else:
            self.logger.error(f"Valve '{valve_name}' not found")

    def run(self):
        self.connect_mqtt()
        try:
            while True:
                self.client.publish(f'{self.device_id}/valves/status', json.dumps(self.valve_states))
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt detected. Stopping Service...")
    def cleanup(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_disconnect(self, client, userdata, rc, _, __):
        if rc != 0:
            self.logger.warning("Disconnected from MQTT broker. Reconnecting...")
            self.client.loop_stop()
            self.connect_mqtt()

if __name__ == "__main__":
    config_file = "config.json"
    controller = FakeValveController(config_file)

    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Cleaning up MQTT...")
        controller.cleanup()