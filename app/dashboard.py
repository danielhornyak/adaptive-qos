from flask import Flask, jsonify, render_template, request
import threading
import asyncio
from monitor import RTTMonitor
from tc_configurator import TCConfigurator
from qos_selector import QoSSelector

monitor = RTTMonitor()
tc = TCConfigurator()
qos_selector = QoSSelector()


class QoSMonitorApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.qos_level = 0
        self.latency = 0
        self.loss = 0
        self.messages_per_minute = 0
        self.max_latency = 0
        self.qos_mode = "auto"
        self.manual_qos_level = 0
        self._setup_routes()
        self.timeout = 5

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/data')
        def data():
            # Szinkron lekérés a metrikákhoz
            metrics = monitor.get_metrics()
            self.latency = metrics['latency']
            self.loss = metrics['loss']
            self.messages_per_minute = metrics['messages_per_minute']
            self.max_latency = metrics['max_latency']

            if self.qos_mode == "auto":
                self.qos_level = qos_selector.get_qos_level()
            else:
                self.qos_level = self.manual_qos_level

            # Az összes adat egyszerre kerül visszaküldésre
            return jsonify(
                latency=self.latency,
                loss=self.loss,
                qos=self.qos_level,
                messages_per_minute=self.messages_per_minute,
                max_latency=self.max_latency,
                qos_mode=self.qos_mode
            )

        @self.app.route("/set_qos_mode", methods=["POST"])
        def set_qos_mode():
            request_data = request.json
            self.qos_mode = request_data.get("mode", "auto")
            self.manual_qos_level = int(request_data.get("qos_level", 1))
            return jsonify({"status": "ok", "mode": self.qos_mode, "manual_qos_level": self.manual_qos_level})

    def start_async_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self.adaptive_qos_loop())
        loop.run_forever()

    async def adaptive_qos_loop(self):
        while True:
            try:
                await monitor.measure_rtt(self.qos_mode, self.timeout, self.manual_qos_level, qos_selector)
                await asyncio.sleep(1)

            except Exception as e:
                print(f"[ERROR] {e}")
                await asyncio.sleep(1)

    def run(self):
        thread = threading.Thread(target=self.start_async_loop)
        thread.daemon = True
        thread.start()
        self.app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    app = QoSMonitorApp()
    app.run()