import asyncio
import uuid
import time
from collections import deque
from paho.mqtt.client import Client as MQTTClient

class RTTMonitor:
    def __init__(self, broker="test.mosquitto.org", port=1883, window_size=20, base_topic="rtt/test"):
        self.window = deque(maxlen=window_size)
        self.latencies = deque(maxlen=window_size)
        self.message_count = 0
        self.start_time = time.time()
        self.responses = {}
        self.qos_level = 0

        self.base_topic = base_topic
        self.req_topic = f"{self.base_topic}/request"
        self.resp_topic = f"{self.base_topic}/response"

        self.loop = asyncio.get_event_loop()
        self.client = MQTTClient()
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.subscribe(self.resp_topic)
        self.client.loop_start()

    def on_message(self, client, userdata, msg):
        message_id = msg.payload.decode()
        if message_id in self.responses:
            response_entry = self.responses[message_id]
            if not response_entry["event"].is_set():
                rtt = time.time() - response_entry["sent"]
                self.latencies.append(rtt)
                self.window.append(True)
                response_entry["event"].set()

    async def measure_rtt(self, qos_mode=None, timeout=1, qos_level=0, qos_selector=None):
        if qos_mode == "auto":
            if len(self.window) >= 5:
                metrics = self.get_metrics()
                latency = metrics["latency"]
                loss = metrics["loss"]
                self.qos_level = qos_selector.decide_qos(latency, loss)
        else:
            self.qos_level = qos_level

        message_id = str(uuid.uuid4())
        event = asyncio.Event()
        self.responses[message_id] = {
            "sent": time.time(),
            "event": event
        }

        self.client.publish(self.req_topic, payload=message_id, qos=self.qos_level)
        self.message_count += 1

        try:
            await asyncio.wait_for(event.wait(), timeout)
        except asyncio.TimeoutError:
            self.window.append(False)

        self.responses.pop(message_id, None)

    def get_metrics(self):
        success_count = sum(1 for success in self.window if success)
        total_count = len(self.window)
        loss_rate = ((total_count - success_count) / total_count * 100) if total_count else 0
        last_latency = self.latencies[-1] * 1000 if self.latencies else 0
        max_latency = max(self.latencies) * 1000 if self.latencies else 0
        messages_per_minute = self.message_count / ((time.time() - self.start_time) / 60)

        return {
            "latency": last_latency,
            "loss": loss_rate,
            "messages_per_minute": messages_per_minute,
            "max_latency": max_latency
        }

