import sys
import os
sys.path.insert(0, os.path.abspath("/app"))
# Get the current working directory
current_dir = os.getcwd()
print(f"Current working directory: {current_dir}")
from vfd_handler.vfd_node import VFDController
from sensors_handler.sensor_node import SensorHandler
from serial_com.serial_com import SerialCom
import logging
import threading

def run_vfd_controller(vfd_controller):
    """Runs the VFD controller in a separate thread."""
    vfd_controller.run()

def run_sensor_handler(sensor_handler):
    """Runs the sensor handler in a separate thread."""
    sensor_handler.run()

if __name__ == "__main__":
    config_file = "config.json"
    serial_com = SerialCom(config_file)  # Assuming SerialCom needs to be instantiated
    vfd_controller = VFDController(config_file, serial_com)
    sensor_handler = SensorHandler(config_file, serial_com)

    # Create threads for running the VFD controller and sensor handler
    vfd_thread = threading.Thread(target=run_vfd_controller, args=(vfd_controller,))
    sensor_thread = threading.Thread(target=run_sensor_handler, args=(sensor_handler,))

    try:
        # Start both threads
        vfd_thread.start()
        sensor_thread.start()

        # Keep the main thread running while the other threads are active
        vfd_thread.join()
        sensor_thread.join()
    except KeyboardInterrupt:
        logging.info("\nKeyboardInterrupt: Stopping...")

        # Stop the VFD controller and sensor handler gracefully
        vfd_controller.emergency_stop()
        sensor_handler.stop()
        
        # Wait for threads to complete after stopping
        vfd_thread.join()
        sensor_thread.join()
