import time
from states.state import State
class InitializeState(State):
        def on_enter(self):
            super().on_enter()

            self.machine.logger.info("Initializing valves...")
            if self.machine.action == 'positive' :
                for valve in self.machine.valves:
                    if 'ACTIVE' in valve['role'] :
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',int(not "POSITIVE" in valve['role']))

            elif self.machine.action == 'negative' :
                for valve in self.machine.valves:
                    if 'ACTIVE' in valve['role'] :
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',int(not "NEGATIVE" in valve['role']))
            self.machine.current_status = 'valves configuration requested'

        def on_exit(self):
            if self.machine.action == 'positive':
                while not self.machine.force_stop:
                    # if "ACTIVE" in valve['role']:
                        all_matched = all(((not "POSITIVE" in valve['role']) == self.machine.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.machine.valves)
                        if all_matched:
                            break
                        time.sleep(0.1)
                    
            elif self.machine.action == 'negative':
                while not self.machine.force_stop:
                    # if "ACTIVE" in valve['role']:
                        all_matched = all(((not "NEGATIVE" in valve['role']) == self.machine.valve_status[valve['name']]) or not "ACTIVE" in valve['role'] for valve in self.machine.valves)
                        if all_matched:
                            break
                        time.sleep(0.1)
                        
            self.machine.current_status = 'valves configuration approved'
            