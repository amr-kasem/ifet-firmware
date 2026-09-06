"""
Fake SICK deflection-gauge gateway.

Stands in for the real `sick_mqtt_gateway` (which lives in ifet-management and talks
to IO-Link masters over HTTP) so a simulated rig can complete a static or cyclic test
without any SICK hardware.

Payload fidelity matters here, so this mirrors the real gateway's
`process_device_data` output exactly, including the two details that hide type bugs:

  * `sick/sensors/{id}` carries `max_value` and `permanent_value` as **strings**
    ("{:.2f}"), not numbers - the state machine forwards them straight into the
    trial POST, so the fake must produce strings too.
  * values are raw IO-Link counts, and `units` is a label the counts do not honour.
    See docs/labos-airtable/evidence/firmware-production-runtime-contract-2026-08-31.md.

Assignment lifecycle is honoured the same way: a gauge only tracks max/permanent
while it is assigned, and `sick/release/{id}` frees it.
"""
import json
import logging
import random
import time
from logging.handlers import RotatingFileHandler

import paho.mqtt.client as mqtt


class FakeSickGateway:
    def __init__(self, config_file):
        self.logger = self.setup_logger()

        with open(config_file) as f:
            config = json.load(f)

        sick = config.get('sick', {})
        self.gauges = [str(g) for g in sick.get('gauges', [])]
        self.unit = sick.get('unit', 'mm')
        self.poll_interval = float(sick.get('poll_interval', 0.2))

        mqtt_config = config.get('mqtt', {})
        self.broker_host = mqtt_config.get('broker_host')
        self.broker_port = mqtt_config.get('broker_port')
        self.username = mqtt_config.get('username')
        self.password = mqtt_config.get('password')

        # device_id -> assigned test system, or None when free
        self.assignments = {g: None for g in self.gauges}
        self.raw_values = {g: 0.0 for g in self.gauges}
        self.max_values = {g: None for g in self.gauges}
        self.latest_values = {g: None for g in self.gauges}

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        if self.username:
            self.client.username_pw_set(self.username, self.password)

    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        try:
            fh = RotatingFileHandler('logs/fake_sick.log', maxBytes=1_000_000, backupCount=5)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except FileNotFoundError:
            pass
        return logger

    def on_connect(self, client, userdata, flags, rc, prop):
        self.logger.info(f"Connected to MQTT broker with result code {rc}")
        # The real gateway takes assign/release over these topics.
        client.subscribe("sick/assign/#")
        client.subscribe("sick/release/#")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            gauge = topic.split('/')[-1]
            if gauge not in self.assignments:
                self.logger.warning(f"Unknown gauge for {topic}: {gauge}")
                return
            if topic.startswith('sick/assign/'):
                # The rig sends {"testing_system_id": "<device>"}; tolerate a bare string.
                raw = msg.payload.decode()
                try:
                    self.assignments[gauge] = json.loads(raw).get('testing_system_id') or 'testing'
                except (ValueError, AttributeError):
                    self.assignments[gauge] = raw or 'testing'
                # Assignment zeroes the gauge, as the real gateway does.
                self.max_values[gauge] = None
                self.latest_values[gauge] = None
                self.logger.info(f"Gauge {gauge} assigned to {self.assignments[gauge]}")
            elif topic.startswith('sick/release/'):
                self.assignments[gauge] = None
                self.logger.info(f"Gauge {gauge} released")
        except Exception as e:
            self.logger.error(f"Error processing MQTT message on {msg.topic}: {e}")

    def step(self, gauge):
        """Advance one gauge by a small random walk and track max/permanent."""
        self.raw_values[gauge] += random.uniform(-1.5, 2.0)
        value = self.raw_values[gauge]

        if self.assignments.get(gauge) is not None:
            current_max = self.max_values.get(gauge)
            if current_max is None or abs(value) > abs(current_max):
                self.max_values[gauge] = value
            self.latest_values[gauge] = value

        max_value = self.max_values.get(gauge) or 0
        permanent_value = self.latest_values.get(gauge) or 0
        assigned_to = self.assignments.get(gauge) or 'free'

        # Field-for-field the real gateway's processed_data.
        return {
            "valid": True,
            "raw_value": round(value, 4),
            "value": "{:.2f}".format(value),
            "permanent_value": "{:.2f}".format(permanent_value),
            "offset": 0,
            "zeroed": False,
            "assigned_to": assigned_to,
            "max_value": "{:.2f}".format(max_value),
            "units": self.unit,
            "timestamp": time.time(),
        }

    def run(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
        self.logger.info(f"Faking SICK gauges {self.gauges} in {self.unit}")
        try:
            while True:
                for gauge in self.gauges:
                    self.client.publish(f"sick/sensors/{gauge}", json.dumps(self.step(gauge)))
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt detected. Stopping Service...")
        finally:
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    FakeSickGateway("config.json").run()
