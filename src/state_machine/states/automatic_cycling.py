from states.state import State
import time
import json

class AutomaticCyclingState(State):
    def on_enter(self):
        super().on_enter()
        self.freq = 0
        self.machine.current_status = 'warming up'
        self.machine.store_variables(resume=True)
        
        self.setpoint = max(abs(float(self.machine.positive_setpoint)),abs(float(self.machine.negative_setpoint)))
        while not self.machine.force_stop:
            self.error =  abs(self.machine.sensors_values[self.machine.sensor_id]) - abs(self.setpoint) 
            self.abs_error = abs(self.error)
            if self.machine.freq_command - self.machine.vdf_feedback < 0.3:
                self.step =  5 if self.abs_error > 5 else 3 if self.abs_error > 3 else 1
                self.freq += self.step
            self.machine.client.publish(
                    f'{self.machine.device_id}/vfd/command',
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
        for i in range(self.machine.cycle_index,self.machine.cycle_counter):
            
            if self.machine.force_stop : return
            self.machine.store_variables(cycle_index=i)    
                                
            if self.machine.action == 'positive':
                while not self.machine.force_stop:
                    self.machine.current_status = f'Cycle {i+1} High Stroke'
                    # if self.machine.sensors_values[self.machine.sensor_id] >= float(self.machine.positive_setpoint) * 0.9 :
                    if True: # modif
                        for valve in self.machine.valves:
                            if "POSITIVE_RELEASE" in valve['role']:
                                self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',0) # off // release
                        time.sleep(0.8) # modif
                        break
                    time.sleep(0.02)
                    
                    
                #####################
                # if self.machine.sensors_values[self.machine.sensor_id] <= float(self.machine.positive_setpoint) * 0.8 :
                #     break
                #####################
                
                
                while not self.machine.force_stop:
                    self.machine.current_status = f'Cycle {i+1} Low Stroke'
                    # if self.machine.sensors_values[self.machine.sensor_id] <= float(self.machine.negative_setpoint) * 1.1:
                    if True: # modif
                        for valve in self.machine.valves:
                            if "POSITIVE_RELEASE" in valve['role']:
                                self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',1) # on // pump
                        time.sleep(0.8) # modif
                        break
                    time.sleep(0.02)
            else:
                
                while not self.machine.force_stop:
                    self.machine.current_status = f'Cycle {i+1} High Stroke'
                    # if self.machine.sensors_values[self.machine.sensor_id] <= float(self.machine.positive_setpoint) * 0.9:
                    if True: # modif
                        for valve in self.machine.valves:
                            if "NEGATIVE_RELEASE" in valve['role']:
                                self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',0) # on // release
                        time.sleep(0.8) # modif
                        break
                    time.sleep(0.02)
                
                #####################
                # if self.machine.sensors_values[self.machine.sensor_id] >= float(self.machine.positive_setpoint) * 0.9:
                #     break
                #####################
                    
                while not self.machine.force_stop:
                    self.machine.current_status = f'Cycle {i+1} Low Stroke'
                    # if self.machine.sensors_values[self.machine.sensor_id] >= float(self.machine.negative_setpoint) * 1.1:
                    if True: # modif
                        for valve in self.machine.valves:
                            if "NEGATIVE_RELEASE" in valve['role']:
                                self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',1) # off // suck
                        time.sleep(0.8) # modif
                        break
                    time.sleep(0.02)
                
            
            if i == self.machine.cycle_counter - 1 :
                for valve in self.machine.valves:
                    self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',1) # on // release
        
        
                    
        if self.machine.test_index_wanted is not None and  not self.machine.force_stop:
            self.machine.store_variables(current_test_index=self.machine.test_index_wanted)
            self.machine.current_test_index = self.machine.test_index_wanted
        
        self.machine.cycle_index = 0
        self.machine.store_variables(cycle_index=0)    
        self.machine.store_variables(resume=False)

