import paho.mqtt.client as mqtt


class MQTTEchoServer:
    def __init__(self, broker="mqtt-broker", port=1883,
                 topic_request="sensor/qos_test/request",
                 topic_response="sensor/qos_test/response"):
        self.broker = broker
        self.port = port
        self.topic_request = topic_request
        self.topic_response = topic_response

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.topic_request)

    def on_message(self, client, userdata, msg):
        qos = msg.qos
        payload = msg.payload
        client.publish(self.topic_response, payload=payload, qos=qos)

    def run(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()


if __name__ == "__main__":
    server = MQTTEchoServer()
    server.run()
