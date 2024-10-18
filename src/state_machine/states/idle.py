from states.state import State


class IdleState(State):
        def on_enter(self):
            super().on_enter()
            self.machine.freq_command = 0.0
            try:
                if self.machine.task:
                    self.machine.task.join()
                    self.machine.logger.info('Task joined successfully')
            except Exception as e:
                self.machine.logger.warning(f'Task is safe to delete')
            finally:
                self.machine.task = None
                
            try:
                for valve in self.machine.valves:
                    if not "FORCE" in valve['role']:
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}', 1)
                
                for valve in self.machine.valves:
                    if "ALWAYSON" in valve['role']:
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}', 0)
                    if "ALWAYSOFF" in valve['role']: 
                        self.machine.client.publish(f'{self.machine.device_id}/valves/{valve["name"]}', 1)
                
                self.machine.logger.info("Valves RELIEVED.")
                self.machine.current_status = 'idle'
            except Exception as e:
                self.machine.logger.error(f"Error configuring valves: {str(e)}")
                self.machine.force_Stop = True
