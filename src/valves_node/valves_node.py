# import RPi.GPIO as GPIO
# try:
#     import RPi.GPIO
# except (RuntimeError, ModuleNotFoundError):
#     import fake_rpigpio.utils
#     fake_rpigpio.utils.install()
# from fake_rpigpio import RPi
import RPi.GPIO as GPIO
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import paho.mqtt.client as mqtt
from logging.handlers import RotatingFileHandler


if __name__ == "__main__":
    config_file = "config.json"
    try:
        config = ""
        with open(config_file) as f:
            config = json.load(f)
        if config != "":
            if config["version"] == 5:
                from valve_controller_pi5 import ValveController 
            else:
                from valve_controller_pi4 import ValveController 

        controller = ValveController(config_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise

    try:
        controller.run()
        pass
        
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Cleaning up GPIO and MQTT...")
        controller.cleanup()
    controller.cleanup()