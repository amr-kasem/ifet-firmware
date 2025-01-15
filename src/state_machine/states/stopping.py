from states.state import State
import time
class StoppingState(State):
        def on_enter(self):
            super().on_enter()
            self.machine.logger.info("Stopping VDF...")
            self.machine.current_status = 'colding down'
            if(self.machine.force_stop): self.machine.current_status = 'emergency: waiting for vdf to stop'
            if self.machine.turbo_id is not None and self.machine.slave is not None:
                for valve in self.machine.turbo_valves:
                    self.machine.client.publish(f'{self.machine.turbo_id}/valves/{valve["name"]}',0) # off // release

                for valve in self.machine.valves:
                    self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',0 if "RELIEF" in valve["role"] else 1 ) # off // release
                    self.machine.client.publish(f'device{self.machine.slave}/valves/{valve["name"]}',1) # off // release

            else:
                for valve in self.machine.valves:
                    if "ACTIVE" in valve["role"]:
                        print(f'will default valve[{valve["name"]} to {"POSITIVE" in valve["role"]}]')
                        self.machine.logger.info(f'will default valve[{valve["name"]} to {"RELIEF" in valve["role"]}]')
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',0 if "RELIEF" in valve["role"] else 1 )
            while not self.machine.exit:
                if self.machine.vdf_feedback == 0 and (self.machine.turbo_vdf_feedback == 0 or self.slave is None):
                    break
                self.machine.set_vfd_speed(0)

                self.machine.set_vfd_state("stop")

               
                time.sleep(1)
            self.machine.current_status = 'vfd stopped'
        def on_exit(self):
            super().on_exit()
            self.machine.logger.info("Valves closed.")
            self.machine.current_status = 'Closed Valves'
        
        