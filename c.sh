#!/bin/bash

# Create main directory
mkdir -p src/state_machine_updated/states

# Create files in main directory
cat << EOF > src/state_machine_updated/__init__.py
from .state_machine import StateMachine
from .valve_controller import ValveController
from .config import Config
from .mqtt_client import MQTTClient
EOF

cat << EOF > src/state_machine_updated/state_machine.py
import logging
import json
import time
import threading
from .states import IdleState, InitializingState, RunningState, StoppingState, PausedState

logger = logging.getLogger(__name__)

class StateMachine:
    def __init__(self, valve_controller, mqtt_client, config):
        self.valve_controller = valve_controller
        self.mqtt_client = mqtt_client
        self.config = config
        self.current_status = "Initializing"
        self.exit = False
        self.freq_command = 0
        self.vfd_feedback = 0
        self.sensors_values = {}

        # Initialize states
        self.idle_state = IdleState()
        self.initializing_state = InitializingState()
        self.running_state = RunningState()
        self.stopping_state = StoppingState()
        self.paused_state = PausedState()

        # Set initial state
        self.current_state = self.idle_state
        self.current_state.enter(self)

    def run(self):
        self.connect_mqtt()
        self.start_feedback_thread()
        self.start_state_loop()

    def connect_mqtt(self):
        while not self.exit:
            try:
                self.mqtt_client.connect()
                break
            except:
                logger.warning("waiting for mqtt server")
                time.sleep(3)

        if self.mqtt_client.is_connected():
            self.mqtt_client.loop_forever()

    def start_feedback_thread(self):
        threading.Thread(target=self.pub_feedback, daemon=True).start()

    def start_state_loop(self):
        threading.Thread(target=self.state_loop, daemon=True).start()

    def pub_feedback(self):
        while not self.exit:
            self.mqtt_client.publish(f'{self.config.device_id}/status', self.current_status)
            time.sleep(0.3)

    def state_loop(self):
        while not self.exit:
            time.sleep(0.01)

    def handle_event(self, event):
        if self.current_state.handle_event(self, event):
            logger.info(f"Handled event: {event}")
        else:
            logger.warning(f"Unhandled event in current state: {event}")

    def transition_to(self, new_state):
        logger.info(f"Transitioning from {self.current_state.__class__.__name__} to {new_state.__class__.__name__}")
        self.current_state.exit(self)
        self.current_state = new_state
        self.current_state.enter(self)
        return True

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload.decode()

        if topic == f'{self.config.device_id}/vfd/command':
            self.handle_vfd_command(json.loads(payload))
        elif topic.endswith('/command'):
            self.handle_state_command(payload)
        elif topic.startswith(f'{self.config.device_id}/sensors/'):
            self.handle_sensor_update(topic, payload)
        elif topic == f'{self.config.device_id}/vfd/feedback':
            self.vfd_feedback = float(payload)
        elif topic == f'{self.config.device_id}/valves/status':
            self.valve_controller.valve_status = {k: int(v) for k, v in json.loads(payload).items()}

    def handle_vfd_command(self, command):
        if command['command'] == 'set_frequency':
            self.freq_command = float(command['parameter'])

    def handle_state_command(self, event):
        self.handle_event(event)

    def handle_sensor_update(self, topic, payload):
        sensor_id = topic.split('/')[-1]
        self.sensors_values[sensor_id] = float(payload)

    def start_vfd(self):
        self.mqtt_client.publish(f'{self.config.device_id}/vfd/command', json.dumps({"command": "start"}))

    def stop_vfd(self):
        self.mqtt_client.publish(f'{self.config.device_id}/vfd/command', json.dumps({"command": "stop"}))

    def pause_vfd(self):
        self.mqtt_client.publish(f'{self.config.device_id}/vfd/command', json.dumps({"command": "pause"}))

    def disconnect(self):
        self.exit = True
        self.mqtt_client.disconnect()
        logger.info("Disconnected from MQTT broker")
EOF

cat << EOF > src/state_machine_updated/valve_controller.py
import logging

logger = logging.getLogger(__name__)

class ValveController:
    def __init__(self, mqtt_client, config):
        self.mqtt_client = mqtt_client
        self.config = config
        self.valve_status = {}

    def initialize_valves(self, action):
        logger.info("Initializing valves...")
        for valve in self.config.valves:
            if 'ACTIVE' in valve['role']:
                state = int(not (action in valve['role']))
                self.set_valve_state(valve['name'], state)

    def set_valve_state(self, valve_name, state):
        self.mqtt_client.publish(f'{self.config.device_id}/valves/{valve_name}', state)
        logger.info(f"Set valve {valve_name} to state {state}")

    def relief_valves(self):
        for valve in self.config.valves:
            self.set_valve_state(valve['name'], 1)
        logger.info("Valves RELIEVED.")

    def check_valve_configuration(self):
        # Implement valve configuration check logic here
        pass
EOF

cat << EOF > src/state_machine_updated/config.py
import json

class Config:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.mqtt = config['mqtt']
        self.sensors = config.get('sensors', [])
        self.valves = config.get('valves', [])
        self.device_id = config.get('device_id', 'device0')
EOF

cat << EOF > src/state_machine_updated/mqtt_client.py
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, config, on_message_callback):
        self.config = config
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message_callback

    def connect(self):
        self.client.connect(self.config.mqtt['broker_host'], self.config.mqtt['broker_port'])

    def on_connect(self, client, userdata, flags, rc, _):
        print(f"Connected with result code {rc}")
        self.client.subscribe(f"{self.config.device_id}/#")

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def loop_forever(self):
        self.client.loop_forever()

    def disconnect(self):
        self.client.disconnect()

    def is_connected(self):
        return self.client.is_connected()
EOF

# Create files in states directory
cat << EOF > src/state_machine_updated/states/__init__.py
from .idle_state import IdleState
from .initializing_state import InitializingState
from .running_state import RunningState
from .stopping_state import StoppingState
from .paused_state import PausedState
EOF

cat << EOF > src/state_machine_updated/states/base_state.py
from abc import ABC, abstractmethod

class State(ABC):
    @abstractmethod
    def enter(self, context):
        pass

    @abstractmethod
    def exit(self, context):
        pass

    @abstractmethod
    def handle_event(self, context, event):
        pass
EOF

cat << EOF > src/state_machine_updated/states/idle_state.py
from .base_state import State

class IdleState(State):
    def enter(self, context):
        context.valve_controller.relief_valves()
        context.current_status = "Idle"

    def exit(self, context):
        pass

    def handle_event(self, context, event):
        if event == "start":
            return context.transition_to(context.initializing_state)
        return False
EOF

cat << EOF > src/state_machine_updated/states/initializing_state.py
from .base_state import State

class InitializingState(State):
    def enter(self, context):
        context.valve_controller.initialize_valves("positive")
        context.current_status = "Initializing"

    def exit(self, context):
        context.valve_controller.check_valve_configuration()

    def handle_event(self, context, event):
        if event == "valves_configured":
            return context.transition_to(context.running_state)
        elif event == "stop":
            return context.transition_to(context.idle_state)
        return False
EOF

cat << EOF > src/state_machine_updated/states/running_state.py
from .base_state import State

class RunningState(State):
    def enter(self, context):
        context.start_vfd()
        context.current_status = "Running"

    def exit(self, context):
        context.stop_vfd()

    def handle_event(self, context, event):
        if event == "stop":
            return context.transition_to(context.stopping_state)
        elif event == "pause":
            return context.transition_to(context.paused_state)
        return False
EOF

cat << EOF > src/state_machine_updated/states/stopping_state.py
from .base_state import State

class StoppingState(State):
    def enter(self, context):
        context.stop_vfd()
        context.current_status = "Stopping"

    def exit(self, context):
        pass

    def handle_event(self, context, event):
        if event == "vfd_stopped":
            return context.transition_to(context.idle_state)
        return False
EOF

cat << EOF > src/state_machine_updated/states/paused_state.py
from .base_state import State

class PausedState(State):
    def enter(self, context):
        context.pause_vfd()
        context.current_status = "Paused"

    def exit(self, context):
        pass

    def handle_event(self, context, event):
        if event == "resume":
            return context.transition_to(context.running_state)
        elif event == "stop":
            return context.transition_to(context.stopping_state)
        return False
EOF

echo "State machine files and folders have been created successfully."