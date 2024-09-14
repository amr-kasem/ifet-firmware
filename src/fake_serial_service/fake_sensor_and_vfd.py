import time
import random
import json
import paho.mqtt.client as mqtt

class FakeSensorAndVFD:
    def __init__(self):
        self.vfd_frequency = 0
        self.sensor_value = 0
        self.vfd_running = False
        self.mqtt_client = mqtt.Client()
        self.setup_mqtt()

    def setup_mqtt(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("172.17. 0.1", 1883, 60)
        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        self.mqtt_client.subscribe("device1/vfd/command")

    def on_message(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload.decode())
            command = message.get("command")
            parameter = message.get("parameter")

            if command == "start":
                self.vfd_running = True
                print("VFD started")
            elif command == "stop":
                self.vfd_running = False
                self.vfd_frequency = 0
                print("VFD stopped")
            elif command == "set_frequency":
                if parameter is not None:
                    self.vfd_frequency = float(parameter)
                    print(f"VFD frequency set to {self.vfd_frequency}")
                else:
                    print("Error: No frequency parameter provided")
            elif command == "emergency_stop":
                self.vfd_running = False
                self.vfd_frequency = 0
                print("Emergency stop executed")
            else:
                print(f"Unknown command: {command}")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON message: {e}")

    def update_sensor_value(self):
        if self.vfd_running:
            # Sensor value increases with frequency, plus some random noise
            self.sensor_value = self.vfd_frequency * 10 + random.uniform(-5, 5)
        else:
            # When VFD is not running, sensor value slowly decreases to zero
            self.sensor_value = max(0, self.sensor_value - 1)

    def publish_data(self):
        vfd_feedback = {
            "frequency": self.vfd_frequency,
            "running": self.vfd_running
        }
        self.mqtt_client.publish("device1/vfd/feedback", json.dumps(vfd_feedback))

        sensor_data = {
            "value": self.sensor_value
        }
        self.mqtt_client.publish("device1/sensor/data", json.dumps(sensor_data))

    def run(self):
        while True:
            self.update_sensor_value()
            self.publish_data()
            time.sleep(1)

if __name__ == "__main__":
    fake_system = FakeSensorAndVFD()
    fake_system.run()