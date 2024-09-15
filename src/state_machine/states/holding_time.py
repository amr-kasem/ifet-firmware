from states.state import State
import time

class HoldingTimeState(State):
    def __init__(self, machine):
        super().__init__(machine)
        self.freq = 0
        
    def on_enter(self):
        super().on_enter()
        self.freq = 0
         
        self.feedback = self.machine.sensors_values[self.machine.sensor_id]
        self.machine.current_status = 'zero_slider'
        self.machine.publish_status()
        self.machine.current_status = 'tuning'
        
        start_time = time.time()
        while not self.machine.force_stop:
            if abs(self.machine.sensors_values[self.machine.sensor_id]) > abs(self.machine.setpoint):
                self.machine.logger.info(f"Setpoint reached: {self.machine.sensors_values[self.machine.sensor_id]}")
                break
            self.freq = self.machine.freq_command
            if time.time() - start_time > 90:  # 5 minutes timeout
                self.machine.logger.error("Tuning timeout")
                raise TimeoutError("Failed to reach setpoint within 5 minutes")
            time.sleep(0.05)

    def on_exit(self):
        super().on_exit()
        self.machine.current_status = 'tuned'
        self.machine.publish_status()
      
        self.machine.logger.info(f"Starting holding time for {self.machine.holdtime} seconds...")
        i = self.machine.holdtime * 10
        while i > 0 and not self.machine.force_stop:
            i = i - 1
            time.sleep(0.1)
            self.machine.current_status = f'Holding {i/10.0}s'
        
        if self.machine.force_stop:
            self.machine.logger.warning("Holding time interrupted")
        else:
            self.machine.logger.info("Holding time completed.")
