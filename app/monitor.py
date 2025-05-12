import asyncio
import uuid
import time
from paho.mqtt.client import Client as MQTTClient

from qos_selector import QoSSelector

qos_decider = QoSSelector()


class RTTMonitor:
    def __init__(self, broker="mqtt-broker", port=1883, window_size=20):
        self.latencies = []
        self.loss_count = 0
        self.message_count = 0
        self.WINDOW_SIZE = window_size
        self.responses = {}
        self.start_time = time.time()

        self.qos_selector = QoSSelector()

        self.loop = asyncio.get_event_loop()
        self.client = MQTTClient()
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.subscribe("sensor/qos_test/response")
        self.client.loop_start()
        self.qos_level = 0

    def on_message(self, client, userdata, msg):
        message_id = msg.payload.decode()
        if message_id in self.responses:
            rtt = time.time() - self.responses[message_id]["sent"]
            self.latencies.append(rtt)
            self.responses[message_id]["event"].set()

    async def measure_rtt(self, gos_mode=None, timeout=1):
        if gos_mode == "auto":
            if len(self.latencies) >= 5 or self.loss_count > 0:
                metrics = self.get_metrics()
                latency = metrics["latency"]
                loss = metrics["loss"]
                self.qos_level = qos_decider.decide_qos(latency, loss)
        message_id = str(uuid.uuid4())
        event = asyncio.Event()
        self.responses[message_id] = {
            "sent": time.time(),
            "event": event
        }
        self.client.publish("sensor/qos_test/request", payload=message_id, qos=self.qos_level)
        self.message_count += 1

        try:
            await asyncio.wait_for(event.wait(), timeout)
        except asyncio.TimeoutError:
            print(f"[LOSS] Message {message_id} timed out.")
            self.loss_count += 1

        if len(self.latencies) > self.WINDOW_SIZE:
            self.latencies.pop(0)

        self.responses.pop(message_id, None)

    def get_metrics(self):
        avg_latency = (sum(self.latencies) / len(self.latencies) * 1000) if self.latencies else 0
        loss_rate = self.loss_count / self.message_count * 100 if self.message_count else 0
        max_latency = max(self.latencies) if self.latencies else 0
        messages_per_minute = self.message_count / ((time.time() - self.start_time) / 60)
        return {
            "latency": avg_latency,
            "loss": loss_rate,
            "messages_per_minute": messages_per_minute,
            "max_latency": max_latency
        }