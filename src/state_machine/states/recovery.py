from states.state import State
import time

class RecoveryState(State):
    def __init__(self, machine):
        super().__init__(machine)
        self.recovery_time = 60  # 60 seconds recovery time
        
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
        for sensor in self.machine.selected_deflection_sensors: 
            self.machine.client.publish(f'sick/release/{sensor}', 'free')    
