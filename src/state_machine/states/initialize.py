import time
from states.state import State
import json
import sensor_ownership


class InitializeState(State):
        def on_enter(self):
            super().on_enter()

            self.machine.logger.info("Initializing valves...")

            # Write-ahead: record ownership before SICK assigns so a crash
            # between here and the assign loop is still recoverable on reboot.
            if self.machine.selected_deflection_sensors:
                sensor_ownership.publish(
                    self.machine.client,
                    self.machine.device_id,
                    self.machine.selected_deflection_sensors,
                )

            for sensor in self.machine.selected_deflection_sensors:
                self.machine.client.publish(
                    f'sick/assign/{sensor}',
                    json.dumps({
                        "testing_system_id": self.machine.device_id
                    })
                )
            if self.machine.action == 'positive' :
                if self.machine.turbo_id is not None and self.machine.slave is not None:
                    for valve in self.machine.turbo_valves:
                        self.machine.client.publish(f'{self.machine.turbo_id}/valves/{valve["name"]}',int(not "POSITIVE" in valve['role'])) # off // release

                    for valve in self.machine.valves:
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',int(not "POSITIVE_TURBO" in valve['role'])) # off // release
                        self.machine.client.publish(f'device{self.machine.slave}/valves/{valve["name"]}',int(not "POSITIVE_TURBO_SLAVE" in valve['role'])) # off // release
                else:
                    for valve in self.machine.valves:
                        if 'ACTIVE' in valve['role'] :
                            self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',int(not "POSITIVE" in valve['role']))
                            
                
            elif self.machine.action == 'negative' :
                if self.machine.turbo_id is not None and self.machine.slave is not None:
                    for valve in self.machine.turbo_valves:
                        self.machine.client.publish(f'{self.machine.turbo_id}/valves/{valve["name"]}',int(not "NEGATIVE" in valve['role'])) # off // release

                    for valve in self.machine.valves:
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',int(not "NEGATIVE_TURBO" in valve['role'])) # off // release
                        self.machine.client.publish(f'device{self.machine.slave}/valves/{valve["name"]}',int(not "NEGATIVE_TURBO_SLAVE" in valve['role'])) # off // release
                else:
                    for valve in self.machine.valves:
                        if 'ACTIVE' in valve['role'] :
                            self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',int(not "NEGATIVE" in valve['role']))
            self.machine.current_status = 'valves configuration requested'

        def on_exit(self):
            if self.machine.action == 'positive':
                while not self.machine.force_stop:
                    # if "ACTIVE" in valve['role']:
                    if self.machine.turbo_id is not None and self.machine.slave is not None:
                        # for valve in self.machine.turbo_valves:
                        #     self.machine.client.publish(f'{self.machine.turbo_id}/valves/{valve["name"]}',1) # off // release

                        all_matched = all(((not "POSITIVE" in valve['role']) == self.machine.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.machine.valves)
                        pass
                        break
                    else:
                        all_matched = all(((not "POSITIVE" in valve['role']) == self.machine.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.machine.valves)
                        if all_matched:
                            break
                        time.sleep(0.1)
                    
            elif self.machine.action == 'negative':
                while not self.machine.force_stop:
                    # if "ACTIVE" in valve['role']:
                    if self.machine.turbo_id is not None and self.machine.slave is not None:
                        # all_matched = all(((not "POSITIVE" in valve['role']) == self.machine.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.machine.valves)
                        pass
                        break
                    else:
                        all_matched = all(((not "NEGATIVE" in valve['role']) == self.machine.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.machine.valves)
                        if all_matched:
                            break
                        time.sleep(0.1)
                        
            self.machine.current_status = 'valves configuration approved'
            