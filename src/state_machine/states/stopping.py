from states.state import State
import json
import time
class StoppingState(State):
        def on_enter(self):
            super().on_enter()
            self.machine.logger.info("Stopping VDF...")
            self.machine.current_status = 'colding down'
            if(self.machine.force_stop): self.machine.current_status = 'emergency: waiting for vdf to stop'
            while not self.machine.exit:
                if self.machine.vdf_feedback == 0:
                    break
                self.machine.client.publish(
                    f'{self.machine.device_id}/vfd/command',
                    json.dumps(
                        {
                            "command":"set_frequency",
                            "parameter": 0
                        }
                    )
                )
                self.machine.client.publish(
                    f'{self.machine.device_id}/vfd/command',
                    json.dumps(
                        {
                            "command":"stop",
                            "parameter": ""
                        }
                    )
                )
                time.sleep(1)
            self.machine.current_status = 'vfd stopped'
        def on_exit(self):
            super().on_exit()
            for valve in self.machine.valves:
                if "ACTIVE" in valve["role"]:
                    self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}',1)
            self.machine.logger.info("Valves closed.")
            self.machine.current_status = 'Closed Valves'
        
        