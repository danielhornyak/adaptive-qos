import asyncio
import uuid
import time
from collections import deque
from paho.mqtt.client import Client as MQTTClient


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully!")
    else:
        print(f"Connection failed with code {rc}")


class RTTMonitor:
    def __init__(self, broker="mqtt-broker", port=1883, base_topic="rtt/test"):
        self.window = deque(maxlen=20)
        self.latencies = deque()  # List of (timestamp, rtt)
        self.message_count = 0
        self.start_time = time.time()
        self.responses = {}
        self.qos_level = 1
        self.message_timestamps = deque()

        self.base_topic = base_topic
        self.req_topic = f"{self.base_topic}/request"
        self.resp_topic = f"{self.base_topic}/response"

        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.client = MQTTClient()
        self.client.on_connect = on_connect
        self.client.on_message = self.on_message

        self.client.connect(broker, port, 60)
        self.client.subscribe(self.resp_topic)
        self.client.loop_start()

        self.last_measure_time = time.time()
        self.last_latency = 0  # Ensure it starts as 0

    def on_message(self, client, userdata, msg):
        message_id = msg.payload.decode()
        response_entry = self.responses.get(message_id)
        if response_entry and not response_entry["event"].is_set():
            rtt = time.time() - response_entry["sent"]
            now = time.time()
            self.latencies.append((now, rtt))
            self.last_latency = rtt  # Update only with valid RTT
            self.window.append(True)
            response_entry["event"].set()

    async def measure_rtt(self, qos_mode=None, timeout=1, qos_level=1, qos_selector=None):
        current_time = time.time()
        self.last_measure_time = current_time

        if qos_mode == "auto" and len(self.window) >= 1:
            metrics = self.get_metrics()
            self.qos_level = qos_selector.decide_qos(metrics["latency"], metrics["loss"])
        else:
            self.qos_level = qos_level

        message_id = str(uuid.uuid4())
        event = asyncio.Event()
        self.responses[message_id] = {"sent": time.time(), "event": event}

        self.client.publish(self.req_topic, payload=message_id, qos=self.qos_level)

        # ➕ Küldési idő regisztrálása
        self.message_timestamps.append(current_time)
        self._cleanup_old_timestamps()  # Régi időbélyegek törlése

        try:
            await asyncio.wait_for(event.wait(), timeout)
            self.message_count += 1
            self.message_timestamps.append(time.time())
        except asyncio.TimeoutError:
            self.window.append(False)

        self.responses.pop(message_id, None)
        print(f"Üzenetek per perc: {self.get_msg_per_minute()}")

    def get_msg_per_minute(self):
        now = time.time()
        return sum(1 for ts in self.message_timestamps if now - ts <= 60)

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

        recent_latencies = [lat for _, lat in self.latencies]

        success_count = sum(1 for success in self.window if success)
        total_count = len(self.window)
        loss_rate = ((total_count - success_count) / total_count * 100) if total_count else 0

        avg_latency = sum(recent_latencies) / len(recent_latencies) * 1000 if recent_latencies else 0
        max_latency = max(recent_latencies) * 1000 if recent_latencies else 0

        msg_per_minute = self.get_msg_per_minute()
        latency = self.last_latency * 1000 if self.last_latency else 0

        return {
            "latency": avg_latency,
            "loss": loss_rate,
            "max_latency": max_latency,
            "messages_per_minute": msg_per_minute,
            "last_latency": latency,
        }






