import time
from serial_com.serial_com import SerialCom
from sensors_handler.sensor import Sensor  # assuming the class is saved in sensor.py

def main():
    # Step 1: Initialize SerialCom (adjust port and baudrate as needed)
    serial_com = SerialCom('debug-sensor.json')

    # Step 2: Define sensor configuration
    config = {
      "name": "2",
      "address": "2",
      "debug": True,
      "value": "",
      "active": True,
      "type": "pressure"
    }

    # Step 3: Create Sensor instance
    sensor = Sensor(config, serial_com)

    # Step 4: Read from sensor in a loop (or just once for quick test)
    try:
        while True:
            sensor.read()
            time.sleep(1/15)  # adjust interval as needed
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()