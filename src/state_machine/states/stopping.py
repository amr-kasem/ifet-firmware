from states.state import State
import json
import time
class StoppingState(State):
        def on_enter(self):
            super().on_enter()
            self.machine.logger.info("Stopping VDF...")
            self.machine.current_status = 'colding down'

        def on_exit(self):
            super().on_exit()
            if(self.machine.force_stop): self.machine.current_status = 'emergency: waiting for vdf to stop'
            while not self.machine.exit:
                if self.machine.vdf_feedback == 0:
                    break
                self.machine.set_vfd_speed(0)

                self.machine.set_vfd_state("stop")

               
                time.sleep(1)
            self.machine.current_status = 'vfd stopped'