from paho.mqtt.client import Client as MQTTClient


class MQTTEchoServer:
    def __init__(self, broker="mqtt-broker", port=1883, base_topic="rtt/test"):
        self.broker = broker
        self.port = port
        self.base_topic = base_topic
        self.topic_request = f"{base_topic}/request"
        self.topic_response = f"{base_topic}/response"
        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.topic_request)

    def on_message(self, client, userdata, msg):
        message_qos = msg.qos
        payload = msg.payload
        client.publish(self.topic_response, payload=payload, qos=message_qos)

    def run(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()


if __name__ == "__main__":
    server = MQTTEchoServer()
    server.run()
