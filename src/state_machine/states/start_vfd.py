from states.state import State
import json
import time

class StartVDFState(State):
    def on_enter(self):
        super().on_enter()
        
        self.machine.logger.info("Starting VDF...")
        try:
            self.machine.client.publish(
                f'{self.machine.device_id}/vfd/command',
                json.dumps(
                    {
                        "command":"set_frequency",
                        "parameter":  0
                    }
                )
            )
            self.machine.logger.info("VDF frequency set to 0.")
            
            self.machine.client.publish(
                f'{self.machine.device_id}/vfd/command',
                json.dumps(
                    {
                        "command":"start",
                        "parameter": ""
                    }
                )
            )
            self.machine.logger.info("VDF start command issued.")
            self.machine.current_status = 'vfd reset'
        except Exception as e:
            self.machine.logger.error(f"Error starting VDF: {str(e)}")
            raise
        
    def on_exit(self):
        super().on_exit()
        self.machine.logger.info("Waiting for VDF to start...")
        start_time = time.time()
        while not self.machine.force_stop:
            if self.machine.vdf_feedback == 0:
                self.machine.logger.info("VDF feedback is 0, VDF initialized successfully.")
                break
            if time.time() - start_time > 90:  # 90 seconds timeout
                self.machine.logger.error("VDF start timeout")
                raise TimeoutError("VDF failed to start within 30 seconds")
            time.sleep(0.1)
        self.machine.current_status = 'vfd started'