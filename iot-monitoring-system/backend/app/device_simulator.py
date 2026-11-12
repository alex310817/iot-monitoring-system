import paho.mqtt.client as mqtt
import json
import time
import random

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC = "iot/temperature"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

device_id = 1  # ID тестового устройства

while True:
    temperature = round(random.uniform(20.0, 30.0), 2)
    payload = json.dumps({"device_id": device_id, "value": temperature})
    client.publish(TOPIC, payload)
    print(f"📡 Sent: {payload}")
    time.sleep(5)  # Отправка каждые 5 секунд
