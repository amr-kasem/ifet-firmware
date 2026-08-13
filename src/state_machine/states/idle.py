from states.state import State
import sensor_ownership


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
                    if not "FORCE" in valve['role'] and not "RELIEF" in valve['role']:
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

            # Release any owned deflection sensors and clear retained ownership.
            # Runs on every Idle entry: normal completion, force-stop, and
            # boot-time orphan recovery (§3 / §4 of SENSOR_CLEANUP_PLAN.md).
            sensors = list(getattr(self.machine, 'selected_deflection_sensors', None) or [])
            topics = list(getattr(self.machine, 'selected_deflection_sensors_topics', None) or [])

            for sensor in sensors:
                try:
                    self.machine.client.publish(f'sick/release/{sensor}', 'free')
                except Exception as e:
                    self.machine.logger.warning(f"Sensor release failed for {sensor}: {e}")

            for sub in topics:
                try:
                    self.machine.client.unsubscribe(sub)
                except Exception:
                    pass

            sensor_ownership.clear(self.machine.client, self.machine.device_id)
            self.machine.selected_deflection_sensors = []
            self.machine.selected_deflection_sensors_topics = []
