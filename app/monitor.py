import asyncio
import uuid
import time
from collections import deque
from paho.mqtt.client import Client as MQTTClient


class RTTMonitor:
    def __init__(self, broker="broker.emqx.io", port=1883, window_size=100, base_topic="rtt/test"):
        self.window = deque(maxlen=window_size)
        self.latencies = deque(maxlen=window_size)
        self.message_count = 0
        self.start_time = time.time()
        self.responses = {}
        self.qos_level = 0
        self.message_timestamps = deque()  # ➕ Üzenetküldési idők nyilvántartása

        self.base_topic = base_topic
        self.req_topic = f"{self.base_topic}/request"
        self.resp_topic = f"{self.base_topic}/response"

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.client = MQTTClient()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.client.connect(broker, port, 60)
            self.client.subscribe(self.resp_topic)
            self.client.loop_start()
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")

        self.last_measure_time = time.time()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker successfully!")
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        message_id = msg.payload.decode()
        response_entry = self.responses.get(message_id)
        if response_entry and not response_entry["event"].is_set():
            rtt = time.time() - response_entry["sent"]
            if self.is_valid_metric(rtt):
                self.latencies.append(rtt)
                self.window.append(True)
            response_entry["event"].set()

    async def measure_rtt(self, qos_mode=None, timeout=1, qos_level=0, qos_selector=None):
        current_time = time.time()
        self.last_measure_time = current_time

        if qos_mode == "auto" and len(self.window) >= 5:
            metrics = self.get_metrics()
            self.qos_level = qos_selector.decide_qos(metrics["latency"], metrics["loss"])
        else:
            self.qos_level = qos_level

        message_id = str(uuid.uuid4())
        event = asyncio.Event()
        self.responses[message_id] = {"sent": time.time(), "event": event}

        self.client.publish(self.req_topic, payload=message_id, qos=self.qos_level)
        self.message_count += 1

        # ➕ Küldési idő regisztrálása
        self.message_timestamps.append(current_time)
        self._cleanup_old_timestamps()  # Régi időbélyegek törlése

        try:
            await asyncio.wait_for(event.wait(), timeout)
        except asyncio.TimeoutError:
            self.window.append(False)

        self.responses.pop(message_id, None)

        # ➕ Aktuális msg/min kiírás
        print(f"Üzenetek per perc: {self.get_msg_per_minute()}")

    def _cleanup_old_timestamps(self):
        """Eltávolítja az 1 percnél régebbi üzenetek időbélyegeit."""
        now = time.time()
        while self.message_timestamps and now - self.message_timestamps[0] > 60:
            self.message_timestamps.popleft()

    def get_msg_per_minute(self):
        """Visszaadja az utóbbi 60 másodpercben küldött üzenetek számát."""
        self._cleanup_old_timestamps()
        return len(self.message_timestamps)

    def get_metrics(self):
        success_count = sum(1 for success in self.window if success)
        total_count = len(self.window)
        loss_rate = ((total_count - success_count) / total_count * 100) if total_count else 0

        avg_latency = sum(self.latencies) / len(self.latencies) * 1000 if self.latencies else 0
        max_latency = max(self.latencies) * 1000 if self.latencies else 0

        msg_per_minute = self.get_msg_per_minute()

        return {
            "latency": avg_latency,
            "loss": loss_rate,
            "max_latency": max_latency,
            "messages_per_minute": msg_per_minute
        }

    @staticmethod
    def is_valid_metric(value):
        return value is not None and 0 <= value < 100



