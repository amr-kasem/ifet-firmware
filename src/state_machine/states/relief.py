from states.state import State
import time


class ReliefValvesState(State):
    def on_enter(self):
        super().on_enter()
        if self.machine.turbo_id is not None and self.machine.slave is not None:
            for valve in self.machine.turbo_valves:
                self.machine.client.publish(f'{self.machine.turbo_id}/valves/{valve["name"]}',1) # off // release

            for valve in self.machine.valves:
                self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',0) # off // release
                self.machine.client.publish(f'device{self.machine.slave}/valves/{valve["name"]}',0) # off // release

        else:
            for valve in self.machine.valves:
                if "ACTIVE" in valve["role"]:
                    self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',0)


        self.machine.logger.info("Valves RELEIFED.")
        self.machine.current_status = 'relief configuration requested'
        
        
    def on_exit(self):
        super().on_exit()
        while not self.machine.force_stop:
            all_matched = all(self.machine.valve_status)
            if all_matched:
                break
            time.sleep(0.1)
        self.machine.current_status = 'valves configured'
        