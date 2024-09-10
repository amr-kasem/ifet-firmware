import json
import minimalmodbus
import paho.mqtt.client as mqtt
import serial
import asyncio
import logging
import time
import os
import threading


class VFDController:
    def __init__(self, config_file):
        self.load_config(config_file)
        self.release_lock()
        self.startstopAddr = 8192
        self.setFreqAddr = 8193
        self.readFreqAddr = 8451
        self.startCmd = 18
        self.stopCmd = 1
        self.startDec = 0
        self.setFreqDec = 2 
        self.writeFC = 6
        self.readFC = 3

        self.logger = self.setup_logger()

        self.connect_vfd()
        self.setup_mqtt()
        
    def setup_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
    
    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.device_id = config["device_id"]

        # MQTT configuration
        mqtt_config = config['mqtt']
        self.broker_host = mqtt_config['broker_host']
        self.broker_port = mqtt_config['broker_port']
        self.username = mqtt_config['username']
        self.password = mqtt_config['password']

        # VFD configuration
        vfd_config = config['vdf']
        self.port = vfd_config['port']
        self.address = int(vfd_config['address'])
        self.baudrate = vfd_config['baudrate']
        self.bytesize = vfd_config['bytesize']
        self.parity = getattr(serial, vfd_config['parity'])
        self.stopbits = vfd_config['stopbits']
        self.timeout = vfd_config['timeout']
        self.mode = getattr(minimalmodbus, vfd_config['mode'])
        self.clear_buffers_before_each_transaction = vfd_config['clear_buffers_before_each_transaction']
        self.close_port_after_each_call = vfd_config['close_port_after_each_call']
        self.debug = vfd_config['debug']
        self.frequency = vfd_config['frequency']
    

    def connect_vfd(self):
        while True:
            try:
                self.VFD = minimalmodbus.Instrument(self.port, self.address)
                self.VFD.serial.baudrate = self.baudrate
                self.VFD.serial.bytesize = self.bytesize
                self.VFD.serial.parity = self.parity
                self.VFD.serial.stopbits = self.stopbits
                self.VFD.serial.timeout = self.timeout
                self.VFD.mode = self.mode
                self.VFD.clear_buffers_before_each_transaction = self.clear_buffers_before_each_transaction
                self.VFD.close_port_after_each_call = self.close_port_after_each_call
                break
            except Exception as e:
                self.logger.error(f"Failed to connect to VFD: {e}")
                asyncio.sleep(1)

    def setup_mqtt(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        while True:
            try:
                self.client.connect(self.broker_host, self.broker_port, 60)
                break
            except:
                time.sleep(10)
                self.logger.error('broker not found will retry')
        self.client.loop_start()
        self.client.subscribe(f"{self.device_id}/vfd/command")

    def on_connect(self, client, userdata, flags, rc,prop):
        self.logger.info("Connected to MQTT broker with result code "+str(rc))

    def on_message(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload.decode())
            command = message.get("command")
            parameter = message.get("parameter")

            if command == "start":
                self.start_vfd()
            elif command == "stop":
                self.stop_vfd()
            elif command == "set_frequency":
                if parameter is not None:
                    frequency = float(parameter)
                    self.set_frequency(frequency)
                else:
                    self.logger.error("Error: No frequency parameter provided.")
            elif command == "emergency_stop":
                threading.Thread(target=asyncio.run,args=self.emergency_stop())
            else:
                self.logger.error(f"Unknown command: {command}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON message: {e}")
    def acquire_lock(self):
        lock_file = f"/dev/shm/{os.path.basename(self.port)}.lock"
        while os.path.exists(lock_file):
            self.logger.info(f"Waiting for lock on {self.port}...")
            time.sleep(0.02)  # Adjust the delay as needed
        open(lock_file, 'w').close()  # Create the lock file

    def release_lock(self):
        lock_file = f"/dev/shm/{os.path.basename(self.port)}.lock"
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)  # Delete the lock file
            except:
                pass

    def start_vfd(self):
        try:
            self.acquire_lock()
            self.VFD.write_register(self.startstopAddr, self.startCmd, self.startDec, self.writeFC)
        except:
            self.logger.error('ignored writing command')
            
        self.release_lock()
        self.logger.info("Started VFD.")

    def stop_vfd(self):
        try:
            self.acquire_lock()
            self.VFD.write_register(self.startstopAddr, self.stopCmd, self.startDec, self.writeFC)
        except:
            self.logger.error('ignored writing command')
        self.release_lock()
        self.logger.info("Stopped VFD.")

    def set_frequency(self, frequency):
        try:
            self.acquire_lock()
            self.VFD.write_register(self.setFreqAddr, frequency, self.setFreqDec, self.writeFC)
        except:
            self.logger.error('ignored writing command')
        self.release_lock()
        self.logger.info(f"Set frequency: {frequency}")

    async def emergency_stop(self):
        try:
            try:
                self.acquire_lock()
                self.VFD.write_register(self.startstopAddr, self.stopCmd, self.startDec, self.writeFC)
            except:
                self.logger.error('ignored writing command')
            finally:
                self.release_lock()
            while True:
                try:
                    self.acquire_lock()
                    speed = self.VFD.read_register(self.readFreqAddr, 2, self.readFC)
                except:
                    self.logger.error('ignored writing command')
                finally:
                    self.release_lock()
                if speed == 0:
                    break
                self.logger.error(f'waiting for vfd to respond current speed is {speed}')
                await asyncio.sleep(0.1)
            self.logger.info("Emergency stop executed.")
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")

    async def publish_feedback(self):
        while True:
            try:
                try:
                    self.acquire_lock()
                    speed = self.VFD.read_register(self.readFreqAddr, 2, self.readFC)
                except:
                    self.logger.error('ignored writing command')
                finally:
                    self.release_lock()
                self.client.publish(f"{self.device_id}/vfd/feedback", speed)
            except Exception as e:
                self.logger.error(f"Failed to read VFD feedback: {e}")
            await asyncio.sleep(1)
    
    def run(self):
        while True:
            # self.logger.info('controller is running')
            asyncio.run(vfd_controller.publish_feedback())
            time.sleep(0.2)  # Keep the script running to handle MQTT messages
    
    def __del__(self):
        self.release_lock()
        

if __name__ == "__main__":
    config_file = "config.json"
    vfd_controller = VFDController(config_file)
    try:
        # asyncio.run(vfd_controller.publish_feedback())
        vfd_controller.run()
    except KeyboardInterrupt:
        logging.info("\nKeyboardInterrupt: Stopping...")
        asyncio.run(vfd_controller.emergency_stop())
