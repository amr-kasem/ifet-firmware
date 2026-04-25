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
from logging.handlers import RotatingFileHandler

from api.api import Api
from states.idle import IdleState
from states.initialize import InitializeState
from states.start_vfd import StartVDFState
from states.holding_time import HoldingTimeState
from states.automatic_cycling import AutomaticCyclingState
from states.stopping import StoppingState
from states.relief import ReliefValvesState
from states.recovery import RecoveryState


class StateMachine:
    def __init__(self, config_file):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        os.makedirs('logs', exist_ok=True)        
        fileHandler = RotatingFileHandler('logs/state_machine.log', maxBytes=1_000_000, backupCount=5)
        fileHandler.setFormatter(formatter)
        self.test_index_wanted = None
        
        self.deflection_sensors_values  = {}

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(stream_handler)
        
        self.slave = None
        
        
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
        self.turbo_vdf_topic = ''
        self.api_base_url = config['api']['base_url']
        self.api = Api(logger=self.logger,api=self.api_base_url)
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
            "relief": ReliefValvesState(self),
            "recovery": RecoveryState(self)
        }
        self.current_state = self.states["idle"]

        # Initialize sensors and valves from config
        self.sensors = config.get('sensors', [])
        self.valves = config.get('valves', [])
        self.device_id = config.get('device_id', 'device0')
        turbo = config.get('turbo',None)
        if turbo is not None: 
            self.turbo_id = turbo.get('id',None)
            self.turbo_valves = turbo.get('valves',[])
        self.id = config.get('id','0')
        
        self.retry_interval = 5  # seconds
        self.retry_attempts = 3
        
        self.sensors_values = {}
        self.valve_status = {}
        self.vdf_feedback = 0
        self.turbo_vdf_feedback = 0
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

        self.selected_deflection_sensors = []
        self.selected_deflection_sensors_topics = []

        self.current_status = 'initial'
        self.feedback_loop = threading.Thread(target=self.pub_feedback)
        self.connected_event = threading.Event()
        self.boot_recovery_done = False
        
        
   
                        
    def on_connect(self, client, userdata, flags, rc, prop):

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

                # [CHANGE] boot orchestration moved to run() so reconnects don't
                # re-start threads or re-run boot recovery. Signal run() instead.
                self.connected_event.set()
                # self.feedback_loop.start()
                # self.current_state.on_enter()
                # if self.cyclic_resume:
                #     self.current_status = f'resume cycle {self.cycle_index}'
                # if self.task is None:
                #     self.task = threading.Thread(target=self.state_loop)
                #     self.task.start()
            else:
                self.logger.error(f"Failed to connect to MQTT broker with return code: {rc}")
                self.retry_connect()
        except Exception as e:
            self.logger.error(f"Error during on_connect: {str(e)}")
            self.retry_connect()
        

    def on_disconnect(self, client, userdata, rc, prop, d):
        self.logger.warning("Disconnected from MQTT broker")
        self.force_stop = True
        self.exit = True
        # [CHANGE] thread joins moved out — loop_stop() in run() handles cleanup
        # try:
        #     if self.task is not None: self.task.join()
        #     if self.feedback_loop is not None: self.feedback_loop.join()
        # except Exception as e:
        #     self.logger.error(f"No threads to join: {str(e)}")
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
        
    def notify(self):
        self.client.publish(f'{self.device_id}/notify','notify')
    
    def set_vfd_speed(self, freq, slaveOnly:bool = False):
        if not slaveOnly:
            self.client.publish(
                    f'device{self.id}/vfd/command',
                    json.dumps(
                        {
                            "command":"set_frequency",
                            "parameter": freq,
                        }
                    )
                )
        if self.slave is not None:
            self.logger.info('sending frequency')
            self.client.publish(
                f'device{self.slave}/vfd/command',
                json.dumps(
                    {
                        "command":"set_frequency",
                        "parameter": freq,
                    }
                )
            )
    
        
    def set_vfd_state(self, state):
        self.client.publish(
                f'device{self.id}/vfd/command',
                json.dumps(
                    {
                        "command":state,
                        "parameter": "",
                    }
                )
            )
        self.logger.info(self.slave)
        if self.slave is not None:
            self.client.publish(
                f'device{self.slave}/vfd/command',
                json.dumps(
                    {
                        "command":state,
                        "parameter": "",
                    }
                )
            )

    
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
            
            if message.topic == f'{self.device_id}/vfd/command':
                x = json.loads(message.payload.decode())
                if x['command'] == 'set_frequency':
                    self.freq_command = float(x['parameter'])
                    if self.slave is not None: 
                        self.set_vfd_speed(self.freq_command,True)
            elif topic_name == 'command':
                event = json.loads(message.payload.decode())
                self.logger.info(f'command: {event}')
                if(event['command'] == 'slave_turn_off'):
                    self.current_state = self.states["relief"]
                self.current_event = event
                self.trigger_event_flag = True
                
            # elif topic_name == 'resume_cancel':
            #     self.test_index_wanted = None
            #     self.cyclic_resume = False
            #     self.cycle_index = 0
            #     self.current_status = 'idle'
                
            elif topic_name == 'emergency_stop': 
                self.set_vfd_state('emergency_stop')
                self.force_stop = True
            elif topic_base == f'{self.device_id}/sensors':
                self.sensors_values[topic_name] = float(message.payload.decode())
            elif message.topic == f'{self.device_id}/vfd/feedback':
                self.vdf_feedback = float(message.payload.decode())
            elif message.topic == self.turbo_vdf_topic:
                self.turbo_vdf_feedback = float(message.payload.decode())
            elif message.topic == f'{self.device_id}/valves/status':
                data = json.loads(message.payload.decode())
                self.valve_status = {i:int(data[i]) for i in data}
            elif message.topic == f'{self.device_id}/current_input':
                data = json.loads(message.payload.decode())
                self.current_user_inputs = data
            elif topic_base == f'sick/sensors':
                data = json.loads(message.payload.decode())
                self.deflection_sensors_values[topic_name] = data
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
        self.logger.info(f"Triggering event: {event['command']}")
        if isinstance(self.current_state, IdleState):
            self.force_stop = False
            
            if event['command'] == "start":
                
                dev_info = self.api.get_device(self.id)
                self.slave = dev_info.get('turbo_charger',None)
                self.selected_deflection_sensors = event.get('selectedSensors',[])
                self.deflection_sensors_values  = {}
                self.selected_deflection_sensors_topics = [
                    f'sick/sensors/{sensor}'
                    for sensor in self.selected_deflection_sensors
                ]
                for subscription in self.selected_deflection_sensors_topics:
                    self.client.subscribe(subscription)
                if self.slave is not None:
                    try:
                        self.client.unsubscribe(self.turbo_vdf_topic)
                    except:
                        pass
                    self.turbo_vdf_topic = f"device{self.slave}/vfd/feedback"
                    self.logger.info(self.turbo_vdf_topic)
                    self.client.subscribe(self.turbo_vdf_topic)
                    
                # if event.get('custom_preset') == 'preset' :
                self.logger.info(event)
                if event['mode'] == 'manual': 
                    self.project_id = event['project_id']
                    self.current_test = event['test_index']
                    data = self.api.get_static_test(self.project_id,self.current_test)
                    self.cyclic_mode = False
                    self.mode = event['mode']
                    self.sensor_id = event['sensor_id']
                    direction = data['type'] == 'outward'
                    self.setpoint = data['pressure'] * (1 if direction else -1)
                    self.test_index_wanted = data['index']
                    self.holdtime = data['duration']
                    self.current_state.on_exit()
                    self.current_state = self.states["initializing_valves"]
                    self.action = 'positive' if direction else 'negative'
                    self.current_state.on_enter()
                    n_event = copy.deepcopy(event) 
                    n_event['command'] = 'turn_on'
                    self.current_event = n_event
                    self.trigger_event_flag = True
                    pass
                elif event['mode'] == 'cyclic':
                    self.logger.info(f'test event: {event}')
                    self.project_id = event['project_id']
                    data = self.api.get_next_cyclic_test(self.project_id)
                    self.cyclic_mode = True
                    self.logger.info(f'test data: {data}')
                    self.test_index_wanted = data['index']
                    self.cycle_index = data['current_cycle']
                    self.mode = event['mode']
                    self.sensor_id =event['sensor_id']
                    self.cycle_counter = data['cycles']
                    direction = data['type'] == 'outward'
                    self.positive_setpoint = data['high_pressure'] * ( -1 if direction else 1 )
                    self.negative_setpoint = data['low_pressure'] * ( -1 if direction else 1 )
                    self.action = 'positive' if direction else 'negative'
                    self.current_state.on_exit()
                    self.current_state = self.states["initializing_valves"]
                    self.current_state.on_enter()
                    n_event = copy.deepcopy(event) 
                    n_event['command'] = 'turn_on'
                    self.current_event = n_event
                    self.trigger_event_flag = True

                # else:
                #     self.logger.info(event)
                #     direction = event['inout'] == 'outward'

                #     if event['mode'] == 'manual': 
                #         self.test_index_wanted = None
                #         self.cyclic_mode = False
                #         self.mode = event['mode']
                #         self.sensor_id = event['sensor_id']
                #         self.setpoint = event['setpoint']
                #         self.holdtime = event['holdtime']
                #         self.current_state.on_exit()
                #         self.current_state = self.states["initializing_valves"]
                #         self.action = 'positive' if direction else 'negative'
                #         self.current_state.on_enter()
                        
                #         n_event = copy.deepcopy(event) 
                #         n_event['command'] = 'turn_on'
                #         self.current_event = n_event
                #         self.trigger_event_flag = True
                #         # self.trigger_event(n_event)
                #     elif event['mode'] == 'cyclic':
                #         self.cyclic_mode = True
                #         self.logger.info(f'Command Test index: {event["test_index"]}')
                #         self.test_index_wanted = None
                #         self.mode = event['mode']
                #         self.sensor_id =event['sensor_id']
                #         self.cycle_counter = int(event['cycles'])
                #         self.positive_setpoint = float(event['positive'])
                #         self.negative_setpoint = float(event['negative'])
                #         self.action = 'positive' if direction else 'negative'
                #         self.current_state.on_exit()
                #         self.current_state = self.states["initializing_valves"]
                #         self.current_state.on_enter()
                #         n_event = copy.deepcopy(event) 
                #         n_event['command'] = 'turn_on'
                #         self.current_event = n_event
                #         self.trigger_event_flag = True
                #         # self.trigger_event(n_event)

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
                n_event['command'] = 'recovery'
                self.current_event = n_event
                self.trigger_event_flag = True
            elif event['command'] == 'slave_turn_off':
                self.slave = None
                try: self.client.unsubscribe(self.turbo_vdf_topic)
                except: pass
                self.current_state = self.states["stopping"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'idle'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)
                
        elif isinstance(self.current_state, StoppingState):
            if event['command'] == "recovery":
                if self.mode == 'cyclic':
                    # [CHANGE] cyclic mode bypasses RecoveryState — finish_cyclic_test called here, then go directly to idle
                    self.current_state.on_exit()
                    if self.test_index_wanted is not None and not self.force_stop:
                        try:
                            self.api.finish_cyclic_test(
                                self.project_id,
                                self.test_index_wanted,
                                self.deflection_sensors_values,
                                0
                            )
                        except Exception as e:
                            self.logger.error(f"Error finishing cyclic test: {e}")
                        else:
                            # notify only on successful API call — avoid false UI refresh on failure
                            self.notify()
                    for sensor in self.selected_deflection_sensors:
                        self.client.publish(f'sick/release/{sensor}', 'free')
                    for subscription in self.selected_deflection_sensors_topics:
                        self.client.unsubscribe(subscription)
                    self.current_state = self.states["idle"]
                    self.current_state.on_enter()
                    n_event = copy.deepcopy(event)
                    n_event['command'] = 'idle'
                    self.current_event = n_event
                    self.trigger_event_flag = True
                else:
                    # Static/manual mode goes through RecoveryState as normal
                    # (previously both modes entered RecoveryState here)
                    self.current_state.on_exit()
                    self.current_state = self.states["recovery"]
                    self.logger.info("Entering recovery state...")
                    self.current_state.on_enter()
                    n_event = copy.deepcopy(event)
                    n_event['command'] = 'idle'
                    self.logger.info("Entered already recovery state...")
                    self.current_event = n_event
                    self.trigger_event_flag = True
                # --- original (both modes entered RecoveryState) ---
                # self.current_state.on_exit()
                # self.current_state = self.states["recovery"]
                # self.logger.info("Entering recovery state...")
                # self.current_state.on_enter()
                # n_event = copy.deepcopy(event)
                # n_event['command'] = 'idle'
                # self.logger.info("Entered already recovery state...")
                # self.current_event = n_event
                # self.trigger_event_flag = True
            elif event['command'] == 'idle':
                self.current_state.on_exit()
                self.current_state = self.states["idle"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'idle'
        elif isinstance(self.current_state, RecoveryState):
            self.logger.info(f"Current state: {self.current_state} and event: {event}")
            if event['command'] == "idle":
                self.logger.info("Leaving recovery state...")
                self.current_state.on_exit()
                self.current_state = self.states["idle"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'idle'
                for subscription in self.selected_deflection_sensors_topics:
                    self.client.unsubscribe(subscription)

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
        import sensor_ownership

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

        # [CHANGE] loop_start() replaces loop_forever() so the main thread is
        # free to call fetch_on_boot() without deadlocking the paho callback thread.
        # loop_forever() would have blocked here; loop_start() runs paho in background.
        # try:
        #     self.client.loop_forever()
        # except Exception as e:
        #     self.logger.error(f"Error in MQTT loop: {str(e)}")
        #     self.logger.error(traceback.format_exc())
        self.client.loop_start()

        try:
            if not self.connected_event.wait(timeout=10.0):
                self.logger.error("MQTT connect timeout — exiting")
                return

            # Boot-time orphan recovery — runs on the main thread while the
            # paho loop thread can freely deliver the retained payload back.
            if not self.boot_recovery_done:
                orphans = sensor_ownership.fetch_on_boot(self.client, self.device_id)
                if orphans:
                    self.logger.info(f"Recovered ownership from broker: {orphans}")
                    self.selected_deflection_sensors = orphans
                    # topics list left empty: we never subscribed to sick/sensors
                    # in this process, so nothing to unsubscribe.
                self.boot_recovery_done = True

            # Start state machine — IdleState.on_enter releases any orphans.
            self.current_state.on_enter()
            self.feedback_loop.start()
            if self.task is None:
                self.task = threading.Thread(target=self.state_loop)
                self.task.start()

            while not self.exit:
                time.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Error in run loop: {str(e)}")
            self.logger.error(traceback.format_exc())
        finally:
            self.client.loop_stop()


    def disconnect(self):
        try:
            self.exit = True
            self.client.disconnect()
        finally:
            self.logger.info("Disconnected from MQTT broker")

