import paho.mqtt.client as mqtt
import random
import time

# MQTT broker details
broker_address = "localhost"
broker_port = 1883
topic = "device1/sensors/4"

# Create a MQTT client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Connect to the MQTT broker
client.connect(broker_address, broker_port)

try:
    while True:
        # Generate fake sensor readings
        temperature = random.uniform(20, 30)
        humidity = random.uniform(40, 60)

        # Create a JSON payload with the sensor readings
        payload = temperature

        # Publish the payload to the MQTT broker
        client.publish(topic, int(humidity *100 ) /100)

        # Print the published payload for debugging
        print(f"Published: {payload}")

        # Wait for some time before publishing the next reading
        time.sleep(5)  # Change the interval as needed
except KeyboardInterrupt:
    # Disconnect from the MQTT broker when the script is interrupted
    client.disconnect()
