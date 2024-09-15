import time
import random
import json
import paho.mqtt.client as mqtt
import logging
class FakeSensorAndVFD:
    def __init__(self):
        self.vfd_frequency = 0
        self.sensor_value = 0
        self.vfd_running = False
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.setup_mqtt()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_mqtt(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("192.168.1.16", 1883, 60)
        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc,_):
        self.logger.info(f"Connected to MQTT broker with result code {rc}")
        self.mqtt_client.subscribe("device1/vfd/command")

    def on_message(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload.decode())
            command = message.get("command")
            parameter = message.get("parameter")

            if command == "start":
                self.vfd_running = True
                self.logger.info("VFD started")
            elif command == "stop":
                self.vfd_running = False
                self.vfd_frequency = 0
                self.logger.info("VFD stopped")
            elif command == "set_frequency":
                if parameter is not None:
                    self.vfd_frequency = float(parameter)
                    self.logger.info(f"VFD frequency set to {self.vfd_frequency}")
                else:
                    self.logger.error("Error: No frequency parameter provided")
            elif command == "emergency_stop":
                self.vfd_running = False
                self.vfd_frequency = 0
                self.logger.info("Emergency stop executed")
            else:
                self.logger.warning(f"Unknown command: {command}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON message: {e}")

    def update_sensor_value(self):
        if self.vfd_running:
            # Sensor value increases with frequency, plus some random noise
            self.sensor_value = self.vfd_frequency * 10 + random.uniform(-5, 5)
        else:
            # When VFD is not running, sensor value slowly decreases to zero
            self.sensor_value = max(0, self.sensor_value - 1)

    def publish_data(self):
        self.mqtt_client.publish("device1/vfd/feedback", self.vfd_frequency)
        self.mqtt_client.publish("device1/sensors/1", self.sensor_value)
        self.logger.info(f"Published VFD frequency: {self.vfd_frequency}, Sensor value: {self.sensor_value}")

    def run(self):
        try:
            while True:
                self.update_sensor_value()
                self.publish_data()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.warning("Process interrupted by user")

if __name__ == "__main__":
    fake_system = FakeSensorAndVFD()
    fake_system.run()