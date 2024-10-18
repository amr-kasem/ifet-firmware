#!/usr/bin/env python
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import time
import json
import copy
import threading
import traceback
import os
from states.idle import IdleState
from states.initialize import InitializeState
from states.start_vfd import StartVDFState
from states.holding_time import HoldingTimeState
from states.automatic_cycling import AutomaticCyclingState
from states.stopping import StoppingState
from states.relief import ReliefValvesState


class StateMachine:
    def __init__(self, config_file):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        os.makedirs('logs', exist_ok=True)

        fileHandler = RotatingFileHandler('logs/state_machine.log', maxBytes=1_000_000, backupCount=5)
        fileHandler.setFormatter(formatter)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(stream_handler)
        
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Successfully loaded config from {config_file}")
        except FileNotFoundError:
            self.logger.error(f"Config file {config_file} not found.")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON from config file {config_file}.")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading config: {str(e)}")
            raise

        self.current_user_inputs = None
        self.current_event = None
        self.trigger_event_flag = False
        self.freq_command = 0
        self.broker_address = config['mqtt']['broker_host']
        self.broker_port = config['mqtt']['broker_port']
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.exit = False
        self.states = {
            "idle": IdleState(self),
            # "resume": ResumeState(self),
            "initializing_valves": InitializeState(self),
            "start_vdf": StartVDFState(self),
            "holding_time": HoldingTimeState(self),
            "automatic_cycling": AutomaticCyclingState(self),
            "stopping": StoppingState(self),
            "relief": ReliefValvesState(self)
        }
        self.current_state = self.states["idle"]

        # Initialize sensors and valves from config
        self.sensors = config.get('sensors', [])
        self.valves = config.get('valves', [])
        self.device_id = config.get('device_id','device0')
        
        self.retry_interval = 5  # seconds
        self.retry_attempts = 3
        
        self.sensors_values = {}
        self.valve_status = {}
        self.vdf_feedback = 0
        self.action = ''
        self.force_stop = False
        self.task = None

        self.cyclic_mode = False
        self.cyclic_resume = False
        self.resume_command = {}
        self.cyclic_command = {}
        self.test_index_wanted = 0
        self.current_test_index = 0
        self.cycle_counter = 0
        self.cycle_index = 0
        self.positive_setpoint = 0
        self.negative_setpoint = 0
        
        self.current_status = 'initial'
        self.feedback_loop = threading.Thread(target=self.pub_feedback)
        
        self.retrieve_variables()
        
    def store_variables(self,resume=None, command=None, current_test_index=None, cycle_index=None, current_inputs=None):
        # Load existing data
        try:
            with open('variables.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            self.logger.error("Error decoding JSON from variables file.")
            data = {}

        # Update with new values
        if resume is not None:
            data['resume'] = resume
        if command is not None:
            data['command'] = command
        if current_test_index is not None:
            data['current_test_index'] = current_test_index
        if cycle_index is not None:
            data['cycle_index'] = cycle_index
        if current_inputs is not None:
            data['current_inputs'] = current_inputs
        

        # Write back to file
        try:
            with open('variables.json', 'w') as file:
                json.dump(data, file)
        except Exception as e:
            self.logger.error(f"Error writing to variables file: {str(e)}")
        
        
        
    def retrieve_variables(self):
        try:
            with open('variables.json', 'r') as file:
                data = json.load(file)
                self.cyclic_resume =  data['resume']
                self.resume_command =  data['command']
                self.current_test_index =  int(data['current_test_index'])
                self.cycle_index =  int(data['cycle_index'])
                self.current_user_inputs = data['current_inputs']
                return data
        except FileNotFoundError:
            self.logger.warning("variables.json file not found.")
            return {}
        except json.JSONDecodeError:
            self.logger.error("Error decoding JSON from variables file.")
            return {}
        
        
    
                        
    def on_connect(self, client, userdata, flags, rc,prop):
        
        try:
            if rc == 0:
                self.logger.info("Connected to MQTT broker")
                self.client.subscribe(f'{self.device_id}/command')
                self.client.subscribe(f'{self.device_id}/resume_cancel')
                self.client.subscribe(f'{self.device_id}/vfd/command')
                self.client.subscribe(f'{self.device_id}/emergency_stop')
                self.client.subscribe(f'{self.device_id}/current_input')
                self.logger.info(f'subscribed to command topics')
                
                for sensor in self.sensors:
                    topic = f"{self.device_id}/sensors/{sensor['address']}"
                    self.logger.info(f'subscribed to {topic}')
                    self.client.subscribe(topic)
                    
                self.client.subscribe(f"{self.device_id}/valves/status")
                
                vdf_topic = f"{self.device_id}/vfd/feedback"
                self.client.subscribe(vdf_topic)
                self.feedback_loop.start()
                self.current_state.on_enter()
                if self.cyclic_resume:
                    self.current_status = f'resume cycle {self.cycle_index}'
                    
                if self.task is None: 
                    self.task = threading.Thread(target=self.state_loop)
                    self.task.start()
            else:
                self.logger.error(f"Failed to connect to MQTT broker with return code: {rc}")
                self.retry_connect()
        except Exception as e:
            self.logger.error(f"Error during on_connect: {str(e)}")
            self.retry_connect()
        

    def on_disconnect(self, client, userdata, rc,prop,d):
        self.logger.warning("Disconnected from MQTT broker")
        self.force_stop = True
        self.exit = True
        try:
            if self.task is not None: self.task.join()
            if self.feedback_loop is not None: self.feedback_loop.join()
        except Exception as e:
            self.logger.error(f"No threads to join: {str(e)}")
        # self.retry_connect()

    def retry_connect(self):
        self.logger.info(f"Retrying connection in {self.retry_interval} seconds...")
        attempts = 0
        while attempts < self.retry_attempts:
            time.sleep(self.retry_interval)
            try:
                self.client.connect(self.broker_address, self.broker_port)
                return
            except Exception as e:
                self.logger.error(f"Failed to connect to MQTT broker: {str(e)}")
                attempts += 1
        self.logger.error("Exceeded maximum retry attempts. Exiting...")
        exit(1)
        
    def publish_status(self):
        self.client.publish(f'{self.device_id}/status',self.current_status)
        self.client.publish(f'{self.device_id}/current_test_index',self.current_test_index)
        if self.cyclic_resume:
            self.client.publish(
                f'{self.device_id}/resume_status',
                json.dumps(
                    {
                        'command':self.resume_command               
                    }
                )
            )
        if self.current_user_inputs is not None:
              self.client.publish(
                f'{self.device_id}/initial_value',
                json.dumps(
                    self.current_user_inputs
                )
            )
        
    def on_message(self, client, userdata, message):
        try:
            topic_base, topic_name = self.get_topic_parts(message.topic)
            self.logger.debug(f"Received message on topic: {message.topic}")
            
            if message.topic == f'{self.device_id}/vfd/command':
                x = json.loads(message.payload.decode())
                if x['command'] == 'set_frequency':
                    self.freq_command = float(x['parameter'])
            elif topic_name == 'command':
                event = json.loads(message.payload.decode())
                self.current_event = event
                self.trigger_event_flag = True
                
            elif topic_name == 'resume_cancel':
                self.test_index_wanted = None
                self.cyclic_resume = False
                self.cycle_index = 0
                self.current_status = 'idle'
                self.store_variables(resume=self.cyclic_resume,command={},current_test_index=self.current_test_index,cycle_index=self.cycle_index)
                
            elif topic_name == 'emergency_stop': 
                self.client.publish(
                    f'{self.device_id}/vfd/command',
                    json.dumps(
                        {
                            "command":"emergency_stop",
                            "parameter": ""
                        }
                    )
                )
                self.force_stop = True
                
            elif topic_base == f'{self.device_id}/sensors':
                self.sensors_values[topic_name] = float(message.payload.decode())
            elif message.topic == f'{self.device_id}/vfd/feedback':
                self.vdf_feedback = float(message.payload.decode())
            elif message.topic == f'{self.device_id}/valves/status':
                data = json.loads(message.payload.decode())
                self.valve_status = {i:int(data[i]) for i in data}
            elif message.topic == f'{self.device_id}/current_input':
                data = json.loads(message.payload.decode())
                self.current_user_inputs = data
                self.store_variables(current_inputs=data)
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON from message on topic {message.topic}")
        except Exception as e:
            self.logger.error(f"Unexpected error processing message on topic {message.topic}: {str(e)}")
            self.logger.error(traceback.format_exc())
            
        
    def get_topic_parts(self,topic):
        # Split the topic string by "/"
        topic_parts = topic.split("/")
        
        # Extract the base portion
        topic_base = "/".join(topic_parts[:-1])
        
        return topic_base , topic_parts[-1]
    
    def trigger_event(self, event:dict): 

        if isinstance(self.current_state, IdleState):
            self.force_stop = False
            if event['command'] == "start":
                self.logger.info(event)
                if event.get('custom_preset') == 'preset' :
                    if event['mode'] == 'manual': 
                        self.cyclic_mode = False
                        
                        self.mode = event['mode']
                        self.sensor_id = event['sensor_id']
                        self.setpoint = event['setpoint']
                        self.holdtime = event['holdtime']
                        
                        self.current_state.on_exit()
                        self.current_state = self.states["initializing_valves"]
                        self.action = 'positive' if self.setpoint > self.sensors_values[self.sensor_id] else 'negative'
                        self.current_state.on_enter()
                        
                        n_event = copy.deepcopy(event) 
                        n_event['command'] = 'turn_on'
                        self.current_event = n_event
                        self.trigger_event_flag = True
                        # self.trigger_event(n_event)
                    elif event['mode'] == 'cyclic':
                        self.cyclic_mode = True
                        self.logger.info(f'Command Test index: {event["test_index"]}')
                        self.test_index_wanted = event['test_index'] if 'test_index' in event else 0
                        self.store_variables(command=event)
                        
                        self.mode = event['mode']
                        self.sensor_id =event['sensor_id']
                        self.cycle_counter = int(event['cycles'])
                        self.positive_setpoint = float(event['positive'])
                        self.negative_setpoint = float(event['negative'])
                        p1 = float(self.positive_setpoint)
                        p2 = float(self.negative_setpoint)
                        direction = p1 > p2
                        self.logger.info(f'{p1} > {p2} = {direction}')

                        self.action = 'positive' if direction else 'negative'
                        self.current_state.on_exit()
                        self.current_state = self.states["initializing_valves"]
                        self.current_state.on_enter()
                        n_event = copy.deepcopy(event) 
                        n_event['command'] = 'turn_on'
                        self.current_event = n_event
                        self.trigger_event_flag = True
                        # self.trigger_event(n_event)

                else:
                    if event['mode'] == 'manual': 
                        self.cyclic_mode = False
                        
                        self.mode = event['mode']
                        self.sensor_id = event['sensor_id']
                        self.setpoint = event['setpoint']
                        self.holdtime = event['holdtime']
                        
                        self.current_state.on_exit()
                        self.current_state = self.states["initializing_valves"]
                        self.action = 'positive' if self.setpoint > self.sensors_values[self.sensor_id] else 'negative'
                        self.current_state.on_enter()
                        
                        n_event = copy.deepcopy(event) 
                        n_event['command'] = 'turn_on'
                        self.current_event = n_event
                        self.trigger_event_flag = True
                        # self.trigger_event(n_event)
                    elif event['mode'] == 'cyclic':
                        self.cyclic_mode = True
                        self.logger.info(f'Command Test index: {event["test_index"]}')
                        self.test_index_wanted = event['test_index'] if 'test_index' in event else 0
                        self.store_variables(command=event)
                        
                        self.mode = event['mode']
                        self.sensor_id =event['sensor_id']
                        self.cycle_counter = int(event['cycles'])
                        self.positive_setpoint = float(event['positive'])
                        self.negative_setpoint = float(event['negative'])
                        p1 = float(self.positive_setpoint)
                        p2 = float(self.negative_setpoint)
                        direction = p1 > p2
                        self.logger.info(f'{p1} > {p2} = {direction}')

                        self.action = 'positive' if direction else 'negative'
                        self.current_state.on_exit()
                        self.current_state = self.states["initializing_valves"]
                        self.current_state.on_enter()
                        n_event = copy.deepcopy(event) 
                        n_event['command'] = 'turn_on'
                        self.current_event = n_event
                        self.trigger_event_flag = True
                        # self.trigger_event(n_event)

        elif isinstance(self.current_state, InitializeState):
            if event['command'] == "turn_on":
                self.current_state.on_exit()
                self.current_state = self.states["start_vdf"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'automatic' if self.cyclic_mode else 'hold'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)
                

        elif isinstance(self.current_state, StartVDFState):
            if event['command'] == "hold":
                self.current_state.on_exit()
                self.current_state = self.states["holding_time"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'relief'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)
            elif event['command'] == "automatic":
                self.current_state.on_exit()
                self.current_state = self.states["automatic_cycling"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'relief'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)

        elif isinstance(self.current_state, HoldingTimeState):
            if event['command'] == "relief":
                self.current_state.on_exit()
                self.current_state = self.states["relief"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'turn_off'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)

        elif isinstance(self.current_state, AutomaticCyclingState):
            if event['command'] == "relief":
                self.current_state.on_exit()
                self.current_state = self.states["relief"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'turn_off'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)

        elif isinstance(self.current_state, ReliefValvesState):
            if event['command'] == "turn_off":
                self.current_state.on_exit()
                self.current_state = self.states["stopping"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'idle'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)
                
        elif isinstance(self.current_state, StoppingState):
            if event['command'] == "idle":
                self.cyclic_mode = False
                self.current_state.on_exit()
                self.current_state = self.states["idle"]
                self.current_state.on_enter()

    def pub_feedback(self):
        while not self.exit:
            self.publish_status()
            time.sleep(0.3)
            
                    
                    
    def state_loop(self):
        while not self.exit:
            if self.trigger_event_flag and self.current_event is not None:
                self.trigger_event_flag = False
                self.trigger_event(self.current_event)
            time.sleep(0.01)
                
                
    def run(self):
        while not self.exit:
            try:
                self.logger.info(f"Connecting to MQTT broker at {self.broker_address}:{self.broker_port}")
                self.logger.info(f"Device ID: {self.device_id}")
                self.client.connect(self.broker_address, self.broker_port)
                self.logger.info("Successfully connected to MQTT broker")
                break
            except Exception as e:
                self.logger.warning(f"Waiting for MQTT server: {str(e)}") 
                time.sleep(3)
        try:
            self.client.loop_forever()
        except Exception as e:
            self.logger.error(f"Error in MQTT loop: {str(e)}")
            self.logger.error(traceback.format_exc())


    def disconnect(self):
        try:
            self.exit = True
            self.client.disconnect()
        finally:
            self.logger.info("Disconnected from MQTT broker")

