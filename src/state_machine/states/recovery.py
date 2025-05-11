from states.state import State
import time

class RecoveryState(State):
    def __init__(self, machine):
        super().__init__(machine)
        self.recovery_time = 1  # 60 seconds recovery time
        
    def on_enter(self):
        super().on_enter()
        self.machine.logger.info("Entering recovery state...")
        self.machine.current_status = f'Recovery {self.recovery_time}s'
        
        # Wait for recovery time
        i = self.recovery_time * 10  # Multiply by 10 for 0.1s resolution
        while i > 0 and not self.machine.force_stop:
            i = i - 1
            time.sleep(0.1)
            self.machine.current_status = f'Recovery {i/10.0}s'
        
        if self.machine.force_stop:
            self.machine.logger.warning("Recovery time interrupted")
        else:
            self.machine.logger.info("Recovery time completed")

    def on_exit(self):
        super().on_exit()
        self.machine.logger.info("Recovery complete, transitioning to idle")
        if self.machine.force_stop:
            self.machine.logger.warning("Holding time interrupted")
        else:
            if self.machine.test_index_wanted is not None and self.machine.project_id is not None:
                if self.machine.mode == 'manual':
                    self.machine.api.finish_static_test(
                        self.machine.project_id,
                        self.machine.test_index_wanted,
                        self.machine.deflection_sensors_values,
                        self.recovery_time
                    )
                else:
                    try:
                        self.machine.api.finish_cyclic_test(
                            self.machine.project_id,
                            self.machine.test_index_wanted,
                            self.machine.deflection_sensors_values,
                            self.recovery_time
                        )
                    except Exception as e:
                        self.machine.logger.error(f"Error finishing cyclic test: {e}")
                self.machine.notify()
            self.machine.logger.info("Recovery time completed.")

        for sensor in self.machine.selected_deflection_sensors: 
            self.machine.client.publish(f'sick/release/{sensor}', 'free')    
