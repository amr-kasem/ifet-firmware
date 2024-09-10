#!/usr/bin/env python
import logging
import paho.mqtt.client as mqtt
import time
import json
import copy
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValveController:
    
    def store_variables(self,resume=None, command=None, current_test_index=None, cycle_index=None, current_inputs=None):
        # Load existing data
        try:
            with open('variables.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
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
        with open('variables.json', 'w') as file:
            json.dump(data, file)
        
        
        
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
            return {}
        
        
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
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
            "idle": self.IdleState(self),
            # "resume": self.ResumeState(self),
            "initializing_valves": self.InitializingValvesState(self),
            "start_vdf": self.StartVDFState(self),
            "holding_time": self.HoldingTimeState(self),
            "automatic_cycling": self.AutomaticCyclingState(self),
            "stopping": self.StoppingState(self),
            "relief": self.ReliefValvesState(self)
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
        
        

    class State:
        def __init__(self, controller):
            self.controller = controller

        def on_enter(self):
            logger.info(f"Entering state: {self.controller.current_state}")

        def on_exit(self):
            logger.info(f"Exiting state: {self.controller.current_state}")

    class IdleState(State):
        def on_enter(self):
            super().on_enter()
            self.controller.freq_command = 0.0
            try:
                self.controller.task.join()
            except : logger.info('already joined')
            finally:

                self.controller.task = None
                for valve in self.controller.valves:
                    if not "FORCE" in valve['role']:
                        self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',1)
                    
                for valve in self.controller.valves:
                    if "ALWAYSON" in valve['role']:
                        self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',0)
                    if "ALWAYSOFF" in valve['role']: 
                        self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',1)
                
                logger.info("Valves RELEIFED.")
                self.controller.current_status = 'idle'

                    

    # class ResumeState(State):
    #     def on_enter(self):
    #         super().on_enter()
    #         self.controller.current_status = f'resume cycle {self.controller.cycle_index}'


    class InitializingValvesState(State):
        def __init__(self, controller):
            super().__init__(controller)
            
        def on_enter(self):
            super().on_enter()

            logger.info("Initializing valves...")
            if self.controller.action == 'positive' :
                for valve in self.controller.valves:
                    if 'ACTIVE' in valve['role'] :
                        self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',int(not "POSITIVE" in valve['role']))

            elif self.controller.action == 'negative' :
                for valve in self.controller.valves:
                    if 'ACTIVE' in valve['role'] :
                        self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',int(not "NEGATIVE" in valve['role']))
            self.controller.current_status = 'valves configuration requested'

        def on_exit(self):
            if self.controller.action == 'positive':
                while not self.controller.force_stop:
                    # if "ACTIVE" in valve['role']:
                        all_matched = all(((not "POSITIVE" in valve['role']) == self.controller.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.controller.valves)
                        if all_matched:
                            break
                        time.sleep(0.1)
                    
            elif self.controller.action == 'negative':
                while not self.controller.force_stop:
                    # if "ACTIVE" in valve['role']:
                        all_matched = all(((not "NEGATIVE" in valve['role']) == self.controller.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.controller.valves)
                        if all_matched:
                            break
                        time.sleep(0.1)
                        
            self.controller.current_status = 'valves configuration approved'
            
          
    class ReliefValvesState(State):
        def __init__(self, controller):
            super().__init__(controller)
            
        def on_enter(self):
            super().on_enter()
            for valve in self.controller.valves:
                self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',1)
            logger.info("Valves RELEIFED.")
            self.controller.current_status = 'relief configuration requested'
            
            
        def on_exit(self):
            super().on_exit()
            while not self.controller.force_stop:
                all_matched = all(self.controller.valve_status)
                if all_matched:
                    break
                time.sleep(0.1)
            self.controller.current_status = 'valves configured'
            


    class StartVDFState(State):
        def on_enter(self):
            super().on_enter()
            
            logger.info("Starting VDF...")
            self.controller.client.publish(
                f'{self.controller.device_id}/vfd/command',
                json.dumps(
                    {
                        "command":"set_frequency",
                        "parameter":  0
                    }
                )
            )
            self.controller.client.publish(
                f'{self.controller.device_id}/vfd/command',
                json.dumps(
                    {
                        "command":"start",
                        "parameter": ""
                    }
                )
            )
            self.controller.current_status = 'vfd reset'
            
            
        def on_exit(self):
            super().on_exit()
            while not self.controller.force_stop:
                if self.controller.vdf_feedback == 0 :
                    break
                time.sleep(0.1)
            self.controller.current_status = 'vfd started'
            

    class HoldingTimeState(State):
        def __init__(self, controller):
            super().__init__(controller)
            self.freq = 0
        def on_enter(self):
            super().on_enter()
            self.freq = 0
             
            self.feedback = self.controller.sensors_values[self.controller.sensor_id]
            self.controller.current_status = 'zero_slider'
            self.controller.publish_status()
            self.controller.current_status = 'tuning'
            while not self.controller.force_stop:
                # if abs(self.controller.sensors_values[self.controller.sensor_id] - self.controller.setpoint) < 0.1 and abs(self.controller.vdf_feedback -  self.controller.freq_command) < 0.1:
                if abs(self.controller.sensors_values[self.controller.sensor_id]) > abs(self.controller.setpoint):
                    break
                self.freq = self.controller.freq_command
                time.sleep(0.05)

        def on_exit(self):
            super().on_exit()
            self.controller.current_status = 'tuned'
            self.controller.publish_status()
          
            logger.info("Waiting for holding time...")
            i = self.controller.holdtime * 10
            while i > 0 and not self.controller.force_stop:
                
                i = i - 1
                time.sleep(0.1)  # Simulate holding time
                self.controller.current_status = f'Holding {i/10.0}s'
            logger.info("Holding time expired.")

    class AutomaticCyclingState(State):
        def __init__(self, controller):
            super().__init__(controller)
        def on_enter(self):
            super().on_enter()
            self.freq = 0
            self.controller.current_status = 'warming up'
            self.controller.store_variables(resume=True)
            
            self.setpoint = max(abs(float(self.controller.positive_setpoint)),abs(float(self.controller.negative_setpoint)))
            while not self.controller.force_stop:
                self.error =  abs(self.controller.sensors_values[self.controller.sensor_id]) - abs(self.setpoint) 
                self.abs_error = abs(self.error)
                if self.controller.freq_command - self.controller.vdf_feedback < 0.3:
                    self.step =  5 if self.abs_error > 5 else 3 if self.abs_error > 3 else 1
                    self.freq += self.step
                self.controller.client.publish(
                        f'{self.controller.device_id}/vfd/command',
                        json.dumps(
                            {
                                "command":"set_frequency",
                                "parameter": self.freq,
                            }
                        )
                )
                    
                if self.error >= 0 :
                    break
                time.sleep(1)
                    
        def on_exit(self):
            super().on_exit()
            for i in range(self.controller.cycle_index,self.controller.cycle_counter):
                
                if self.controller.force_stop : return
                self.controller.store_variables(cycle_index=i)    
                                   
                if self.controller.action == 'positive':
                    while not self.controller.force_stop:
                        self.controller.current_status = f'Cycle {i+1} High Stroke'
                        # if self.controller.sensors_values[self.controller.sensor_id] >= float(self.controller.positive_setpoint) * 0.9 :
                        if True: # modif
                            for valve in self.controller.valves:
                                if "POSITIVE_RELEASE" in valve['role']:
                                    self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',0) # off // release
                            time.sleep(0.8) # modif
                            break
                        time.sleep(0.02)
                        
                        
                    #####################
                    # if self.controller.sensors_values[self.controller.sensor_id] <= float(self.controller.positive_setpoint) * 0.8 :
                    #     break
                    #####################
                    
                    
                    while not self.controller.force_stop:
                        self.controller.current_status = f'Cycle {i+1} Low Stroke'
                        # if self.controller.sensors_values[self.controller.sensor_id] <= float(self.controller.negative_setpoint) * 1.1:
                        if True: # modif
                            for valve in self.controller.valves:
                                if "POSITIVE_RELEASE" in valve['role']:
                                    self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',1) # on // pump
                            time.sleep(0.8) # modif
                            break
                        time.sleep(0.02)
                else:
                    
                    while not self.controller.force_stop:
                        self.controller.current_status = f'Cycle {i+1} High Stroke'
                        # if self.controller.sensors_values[self.controller.sensor_id] <= float(self.controller.positive_setpoint) * 0.9:
                        if True: # modif
                            for valve in self.controller.valves:
                                if "NEGATIVE_RELEASE" in valve['role']:
                                    self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',0) # on // release
                            time.sleep(0.8) # modif
                            break
                        time.sleep(0.02)
                    
                    #####################
                    # if self.controller.sensors_values[self.controller.sensor_id] >= float(self.controller.positive_setpoint) * 0.9:
                    #     break
                    #####################
                        
                    while not self.controller.force_stop:
                        self.controller.current_status = f'Cycle {i+1} Low Stroke'
                        # if self.controller.sensors_values[self.controller.sensor_id] >= float(self.controller.negative_setpoint) * 1.1:
                        if True: # modif
                            for valve in self.controller.valves:
                                if "NEGATIVE_RELEASE" in valve['role']:
                                    self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',1) # off // suck
                            time.sleep(0.8) # modif
                            break
                        time.sleep(0.02)
                    
                
                if i == self.controller.cycle_counter - 1 :
                    for valve in self.controller.valves:
                        self.controller.client.publish(f'{self.controller.device_id}/valves/{valve["name"]}',1) # on // release
            
            
                       
            if self.controller.test_index_wanted is not None and  not self.controller.force_stop:
                self.controller.store_variables(current_test_index=self.controller.test_index_wanted)
                self.controller.current_test_index = self.controller.test_index_wanted
            
            self.controller.cycle_index = 0
            self.controller.store_variables(cycle_index=0)    
            self.controller.store_variables(resume=False)


    class StoppingState(State):
        def on_enter(self):
            super().on_enter()
            logger.info("Stopping VDF...")
            self.controller.current_status = 'colding down'

        def on_exit(self):
            super().on_exit()
            if(self.controller.force_stop): self.controller.current_status = 'emergency: waiting for vdf to stop'
            while not self.controller.exit:
                if self.controller.vdf_feedback == 0:
                    break
                self.controller.client.publish(
                    f'{self.controller.device_id}/vfd/command',
                    json.dumps(
                        {
                            "command":"set_frequency",
                            "parameter": 0
                        }
                    )
                )
                self.controller.client.publish(
                    f'{self.controller.device_id}/vfd/command',
                    json.dumps(
                        {
                            "command":"stop",
                            "parameter": ""
                        }
                    )
                )
                time.sleep(1)
            self.controller.current_status = 'vfd stopped'
                
    def on_connect(self, client, userdata, flags, rc,prop):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.client.subscribe(f'{self.device_id}/command')
            self.client.subscribe(f'{self.device_id}/resume_cancel')
            self.client.subscribe(f'{self.device_id}/vfd/command')
            self.client.subscribe(f'{self.device_id}/emergency_stop')
            self.client.subscribe(f'{self.device_id}/current_input')
            for sensor in self.sensors:
                topic = f"{self.device_id}/sensors/{sensor['address']}"
                logger.info(f'subscribed to {topic}')
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
            logger.error(f"Failed to connect to MQTT broker with return code: {rc}")
            self.retry_connect()

    def on_disconnect(self, client, userdata, rc,prop,d):
        logger.warning("Disconnected from MQTT broker")
        self.force_stop = True
        self.exit = True
        if self.task is not None: self.task.join()
        if self.feedback_loop is not None: self.feedback_loop.join()
        # self.retry_connect()

    def retry_connect(self):
        logger.info(f"Retrying connection in {self.retry_interval} seconds...")
        attempts = 0
        while attempts < self.retry_attempts:
            time.sleep(self.retry_interval)
            try:
                self.client.connect(self.broker_address, self.broker_port)
                return
            except Exception as e:
                logger.error(f"Failed to connect to MQTT broker: {e}")
                attempts += 1
        logger.error("Exceeded maximum retry attempts. Exiting...")
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
        topic_base, topic_name = self.get_topic_parts(message.topic)
        if message.topic == f'{self.device_id}/vfd/command':
            x = json.loads(message.payload.decode())
            if x['command'] == 'set_frequency':
                self.freq_command = float(x['parameter'])
        elif topic_name == 'command':
            event = json.loads(message.payload.decode())
            self.current_event = event
            self.trigger_event_flag = True
            
        elif topic_name == 'resume_cancel':
            self.current_test_index = 0
            self.test_index_wanted = 0
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
            
        
    def get_topic_parts(self,topic):
        # Split the topic string by "/"
        topic_parts = topic.split("/")
        
        # Extract the base portion
        topic_base = "/".join(topic_parts[:-1])
        
        return topic_base , topic_parts[-1]
    
    def trigger_event(self, event): 

        if isinstance(self.current_state, ValveController.IdleState):
            self.force_stop = False
            if event['command'] == "start":
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
                    logger.info(f'{p1} > {p2} = {direction}')

                    self.action = 'positive' if direction else 'negative'
                    self.current_state.on_exit()
                    self.current_state = self.states["initializing_valves"]
                    self.current_state.on_enter()
                    n_event = copy.deepcopy(event) 
                    n_event['command'] = 'turn_on'
                    self.current_event = n_event
                    self.trigger_event_flag = True
                    # self.trigger_event(n_event)

        elif isinstance(self.current_state, ValveController.InitializingValvesState):
            if event['command'] == "turn_on":
                self.current_state.on_exit()
                self.current_state = self.states["start_vdf"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'automatic' if self.cyclic_mode else 'hold'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)
                

        elif isinstance(self.current_state, ValveController.StartVDFState):
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

        elif isinstance(self.current_state, ValveController.HoldingTimeState):
            if event['command'] == "relief":
                self.current_state.on_exit()
                self.current_state = self.states["relief"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'turn_off'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)

        elif isinstance(self.current_state, ValveController.AutomaticCyclingState):
            if event['command'] == "relief":
                self.current_state.on_exit()
                self.current_state = self.states["relief"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'turn_off'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)

        elif isinstance(self.current_state, ValveController.ReliefValvesState):
            if event['command'] == "turn_off":
                self.current_state.on_exit()
                self.current_state = self.states["stopping"]
                self.current_state.on_enter()
                n_event = copy.deepcopy(event) 
                n_event['command'] = 'idle'
                self.current_event = n_event
                self.trigger_event_flag = True
                # self.trigger_event(n_event)
                
        elif isinstance(self.current_state, ValveController.StoppingState):
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
                self.client.connect(self.broker_address, self.broker_port)
                break
            except:
                logger.warning("waiting for mqtt server") 
                time.sleep(3)
                
        if self.client.is_connected: 
            self.client.loop_forever()
                    
    def disconnect(self):
        try:
            self.exit = True
            self.client.disconnect()
        finally:
            logger.info("Disconnected from MQTT broker")

if __name__ == "__main__":
    valve_controller = ValveController('config.json')
    try:
        valve_controller.run()
    except KeyboardInterrupt:
        print('')
        logger.info("Exiting...")
    finally:
        valve_controller.disconnect()