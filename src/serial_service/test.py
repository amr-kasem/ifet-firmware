# main.py
import time
from serial_com import ModbusCom
from new_sensor import NewSensor

def main():
    # --- RTU (Serial) config ---
    config = {
        "name": "PressureSensor_1",
        "address": 1,
        "debug": True,
    }

    com = ModbusCom(port="/dev/ttyUSB0", baudrate=9600, timeout=1)  # adjust as needed

    sensor = NewSensor(config=config, com_port=com, tcp=False)

    while True:
        value = sensor.read()
        print(f"[main] Latest reading: {value}")
        time.sleep(1)

if __name__ == "__main__":
    main()