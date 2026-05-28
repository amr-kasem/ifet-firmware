import time
from serial_com import ModbusTcpCom, SerialCom
from sensors_handler.sensor import Sensor
from sensors_handler.new_sensor import NewSensor

CONFIG_FILE = "debug-sensor.json"

def main():

    config = {
      "name": "1",
      "address": "1",
      "debug": True,
      "value": "",
      "active": True,
      "type": "pressure2",
    }

    com_port = SerialCom(CONFIG_FILE)
    sensor = NewSensor(config, com_port=com_port)

    try:
        while True:
            print(sensor.read())
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    main()