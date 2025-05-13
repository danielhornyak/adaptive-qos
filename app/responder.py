from paho.mqtt.client import Client as MQTTClient

class MQTTEchoServer:
    def __init__(self, broker="test.mosquitto.org", port=1883, base_topic="rtt/test"):
        self.broker = broker
        self.port = port
        self.base_topic = base_topic
        self.topic_request = f"{base_topic}/request"
        self.topic_response = f"{base_topic}/response"
        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"[EchoServer] Connected to broker with result code {rc}")
        client.subscribe(self.topic_request)
        print(f"[EchoServer] Subscribed to: {self.topic_request}")

    def on_message(self, client, userdata, msg):
        qos = msg.qos
        payload = msg.payload
        print(f"[EchoServer] Received: {payload.decode()}, QoS: {qos}")
        client.publish(self.topic_response, payload=payload, qos=qos)
        print(f"[EchoServer] Responded with same payload on: {self.topic_response}")

    def run(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    server = MQTTEchoServer()
    server.run()
