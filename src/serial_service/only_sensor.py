import time
from serial_com import ModbusTcpCom
from sensors_handler.sensor import Sensor  # assuming the class is saved in sensor.py

def main():

    # Step 2: Define sensor configuration
    config = {
      "name": "1",
      "address": "1",
      "debug": True,
      "value": "",
      "active": True,
      "type": "pressure",
      "host": "10.1.10.120",
      "port": 3001,
    }

    # Step 3: Create Sensor instance
    sensor = Sensor(config, tcp=True)

    # Step 4: Read from sensor in a loop (or just once for quick test)
    try:
        while True:
            print(sensor.read())
            time.sleep(1/15)  # adjust interval as needed
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()