import paho.mqtt.client as mqtt
import json
import time
import logging
import argparse
import curses
import threading
import queue

class ApplicationClient:
    def __init__(self, broker_host, broker_port, device_id):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_id = device_id
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.logger = self.setup_logger()

        # Store latest sensor and VFD data
        self.sensor_data = {}
        self.vfd_feedback = None
        self.valve_status = {}
        self.current_state = None
        self.update_queue = queue.Queue()

    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def connect(self):
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, _):
        self.logger.info(f"Connected with result code {rc}")
        # Subscribe to relevant topics
        self.client.subscribe(f"{self.device_id}/sensors/#")
        self.client.subscribe(f"{self.device_id}/vfd/feedback")
        self.client.subscribe(f"{self.device_id}/valves/status")
        self.client.subscribe(f"{self.device_id}/state")

    def on_message(self, client, userdata, msg):
        try:
            if msg.topic.startswith(f"{self.device_id}/sensors/"):
                sensor_id = msg.topic.split('/')[-1]
                self.sensor_data[sensor_id] = float(msg.payload)
            elif msg.topic == f"{self.device_id}/vfd/feedback":
                self.vfd_feedback = float(msg.payload)
            elif msg.topic == f"{self.device_id}/valves/status":
                self.valve_status = json.loads(msg.payload)
            elif msg.topic == f"{self.device_id}/state":
                self.current_state = msg.payload.decode()
            self.update_queue.put("update")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def send_vfd_command(self, command, parameter=None):
        payload = {"command": command}
        if parameter is not None:
            payload["parameter"] = parameter
        self.client.publish(f"{self.device_id}/vfd/command", json.dumps(payload))
        self.logger.info(f"Sent VFD command: {payload}")

    def set_valve_state(self, valve_name, state):
        self.client.publish(f"{self.device_id}/valves/{valve_name}", state)
        self.logger.info(f"Set valve {valve_name} to state {state}")

    def send_state_command(self, command):
        self.client.publish(f"{self.device_id}/state/command", command)
        self.logger.info(f"Sent state command: {command}")

    def get_sensor_data(self):
        return self.sensor_data

    def get_vfd_feedback(self):
        return self.vfd_feedback

    def get_valve_status(self):
        return self.valve_status

    def get_current_state(self):
        return self.current_state

    def update_display(self, stdscr):
        status_win = curses.newwin(curses.LINES - 3, curses.COLS, 0, 0)
        while True:
            try:
                self.update_queue.get(timeout=0.1)
                status_win.clear()
                status_win.addstr(0, 0, f"Current State: {self.current_state}")
                status_win.addstr(1, 0, f"VFD: {self.vfd_feedback:.2f}")
                status_win.addstr(2, 0, f"Sensors: {self.sensor_data}")
                status_win.addstr(3, 0, f"Valves: {self.valve_status}")
                status_win.refresh()
            except queue.Empty:
                pass

    def run_interactive(self, stdscr):
        curses.curs_set(1)  # Show cursor
        stdscr.clear()
        stdscr.refresh()

        # Create a window for user input
        input_win = curses.newwin(3, curses.COLS, curses.LINES - 3, 0)
        input_win.scrollok(True)
        input_win.addstr(0, 0, "Enter commands below. Type 'help' for available commands.")
        input_win.addstr(1, 0, "Command: ")
        input_win.refresh()

        update_thread = threading.Thread(target=self.update_display, args=(stdscr,), daemon=True)
        update_thread.start()

        while True:
            input_win.move(1, 9)  # Move cursor to input position
            curses.echo()
            command = input_win.getstr(1, 9).decode().strip().lower()
            curses.noecho()
            input_win.clear()
            input_win.addstr(0, 0, "Enter commands below. Type 'help' for available commands.")
            input_win.addstr(1, 0, "Command: ")

            if command == "quit":
                break
            elif command == "help":
                input_win.addstr(2, 0, "Available commands: vfd, valve, sensor, status, state, quit")
            elif command == "vfd":
                input_win.addstr(2, 0, "Enter VFD command (start/stop/set_frequency/emergency_stop): ")
                vfd_cmd = input_win.getstr().decode().strip()
                if vfd_cmd == "set_frequency":
                    input_win.addstr(3, 0, "Enter frequency: ")
                    freq = float(input_win.getstr().decode().strip())
                    self.send_vfd_command(vfd_cmd, freq)
                else:
                    self.send_vfd_command(vfd_cmd)
            elif command == "valve":
                input_win.addstr(2, 0, "Enter valve name: ")
                valve_name = input_win.getstr().decode().strip()
                input_win.addstr(3, 0, "Enter valve state (0/1): ")
                state = int(input_win.getstr().decode().strip())
                self.set_valve_state(valve_name, state)
            elif command == "sensor":
                input_win.addstr(2, 0, f"Sensor data: {self.get_sensor_data()}")
            elif command == "status":
                input_win.addstr(2, 0, f"Current State: {self.get_current_state()}")
                input_win.addstr(3, 0, f"VFD feedback: {self.get_vfd_feedback()}")
                input_win.addstr(4, 0, f"Valve status: {self.get_valve_status()}")
                input_win.addstr(5, 0, f"Sensor data: {self.get_sensor_data()}")
            elif command == "state":
                input_win.addstr(2, 0, "Enter state command (start/stop/pause/resume): ")
                state_cmd = input_win.getstr().decode().strip()
                self.send_state_command(state_cmd)
            else:
                input_win.addstr(2, 0, "Invalid command. Type 'help' for available commands.")

            input_win.refresh()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

def main(stdscr):
    parser = argparse.ArgumentParser(description="Application Client")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--device", default="device1", help="Device ID")
    args = parser.parse_args()

    client = ApplicationClient(args.host, args.port, args.device)
    client.connect()

    try:
        client.run_interactive(stdscr)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()

if __name__ == "__main__":
    curses.wrapper(main)