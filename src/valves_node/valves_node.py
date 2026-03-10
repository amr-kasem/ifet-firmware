import gpiod
from gpiod.line import Direction, Value
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import paho.mqtt.client as mqtt

class ValveController:
    def __init__(self, config_file):
        self.logger = self.setup_logger()
        self.valve_lines = {}

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
        
        # Pin conversion: BOARD -> BCM
        BOARD_TO_BCM = {
            13: 27,  # Valve 1
            35: 19,  # Valve 2
            31: 6,   # Valve 3
            15: 22   # Valve 4
        }

        # Initialize GPIO using gpiod v2 API
        try:
            # Setup valve pins
            for valve in self.valves:
                board_pin = valve.get('pin')
                valve_name = valve.get('name')
                
                # Convert BOARD pin to BCM
                bcm_pin = BOARD_TO_BCM.get(board_pin)
                if bcm_pin is None:
                    self.logger.error(f"Invalid BOARD pin {board_pin} for valve '{valve_name}'")
                    raise ValueError(f"Pin {board_pin} is not a valid BOARD pin")
                
                try:
                    # gpiod v2 API: request line directly
                    line_request = gpiod.request_lines(
                        "/dev/gpiochip0",
                        consumer=f"valve_{valve_name}",
                        config={
                            bcm_pin: gpiod.LineSettings(
                                direction=Direction.OUTPUT,
                                output_value=Value.INACTIVE
                            )
                        }
                    )
                    self.valve_lines[valve_name] = (line_request, bcm_pin)
                    self.logger.info(f"Valve '{valve_name}' initialized on BOARD pin {board_pin} (BCM {bcm_pin})")
                except Exception as e:
                    self.logger.error(f"Failed to setup valve '{valve_name}': {e}", exc_info=True)
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}", exc_info=True)
            raise

        # Initialize MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.username, self.password)

    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
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
                self.logger.error(f"MQTT connection {(self.broker_host, self.broker_port)} failed: {e}", exc_info=True)
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
                if valve_name in self.valve_lines:
                    line_request, pin = self.valve_lines[valve_name]
                    # gpiod v2 API: set_value
                    line_request.set_value(pin, Value.ACTIVE if state == 1 else Value.INACTIVE)
                    self.logger.info(f"Valve '{valve_name}' state set to {state}")
                    return
                else:
                    self.logger.error(f"Valve '{valve_name}' not found")
                    return
            except Exception as e:
                self.logger.error(f"Failed to set state for valve '{valve_name}': {e}", exc_info=True)
                time.sleep(1)  # Wait for 1 second before retrying
        
        self.logger.error(f"Failed to set state for valve '{valve_name}' after {retry_count} retries")

    def get_valve_state(self, valve_name):
        """Get current state of a valve"""
        try:
            if valve_name in self.valve_lines:
                line_request, pin = self.valve_lines[valve_name]
                # gpiod v2 API: get_value
                value = line_request.get_value(pin)
                return 1 if value == Value.ACTIVE else 0
            else:
                self.logger.error(f"Valve '{valve_name}' not found")
                return 0
        except Exception as e:
            self.logger.error(f"Failed to get state for valve '{valve_name}': {e}", exc_info=True)
            return 0

    def run(self):
        self.connect_mqtt()
        while True:
            try:
                # Publish valve status
                status = {valve['name']: self.get_valve_state(valve['name']) for valve in self.valves}
                self.client.publish(f'{self.device_id}/valves/status', json.dumps(status))
                time.sleep(0.2)  # Keep the script running to handle MQTT messages
            except Exception as e:
                self.logger.error(f"Error during run loop: {e}", exc_info=True)
            
    def cleanup(self):
        """Clean up GPIO resources"""
        self.logger.info("Cleaning up GPIO resources...")
        
        # Release all GPIO lines
        for valve_name, (line_request, pin) in self.valve_lines.items():
            try:
                line_request.release()
                self.logger.info(f"Released GPIO line for valve '{valve_name}'")
            except Exception as e:
                self.logger.error(f"Error releasing line for valve '{valve_name}': {e}", exc_info=True)
        
        # MQTT cleanup
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("MQTT connection closed")
        
    def on_disconnect(self, client, userdata, rc, _, __):
        if rc != 0:
            self.logger.warning("Disconnected from MQTT broker. Reconnecting...")
            self.client.loop_stop()
            self.connect_mqtt()

if __name__ == "__main__":
    config_file = "config.json"
    controller = ValveController(config_file)

    try:
        controller.run()
        
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Cleaning up GPIO and MQTT...")
        controller.cleanup()
    except Exception as e:
        controller.logger.error(f"Unexpected error: {e}", exc_info=True)
        controller.cleanup()
    finally:
        controller.cleanup()