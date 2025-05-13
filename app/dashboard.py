import asyncio
import threading
from flask import Flask, jsonify, render_template, request
from monitor import RTTMonitor
from qos_selector import QoSSelector
from tc_configurator import TCConfigurator

monitor = RTTMonitor()
qos_selector = QoSSelector()
tc = TCConfigurator()


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
        self.timeout = 0.1
        self.last_latency = 0

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/data')
        def data():
            metrics = monitor.get_metrics()
            self.loss = metrics['loss']
            self.messages_per_minute = metrics['messages_per_minute']
            self.max_latency = metrics['max_latency']
            self.last_latency = metrics['last_latency']

            if self.qos_mode == "auto":
                self.qos_level = qos_selector.get_qos_level()
            else:
                self.qos_level = self.manual_qos_level

            return jsonify(
                latency=self.last_latency,
                loss=self.loss,
                qos=self.qos_level,
                messages_per_minute=self.messages_per_minute,
                max_latency=self.max_latency,
                qos_mode=self.qos_mode
            )

        @self.app.route("/set_network", methods=["POST"])
        def set_network():
            request_data = request.json
            try:
                latency_ms = float(request_data.get("latency", 0))
                loss_percent = float(request_data.get("loss", 0))

                delay_str = f"{latency_ms}ms"
                loss_str = f"{loss_percent}%"

                tc.apply_tc_settings(delay=delay_str, loss=loss_str)

                return jsonify({"status": "ok", "latency": latency_ms, "loss": loss_percent})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400

        @self.app.route("/set_qos_mode", methods=["POST"])
        def set_qos_mode():
            request_data = request.json
            self.qos_mode = request_data.get("mode", "auto")
            self.manual_qos_level = int(request_data.get("qos_level", 1))
            return jsonify({"status": "ok", "mode": self.qos_mode, "manual_qos_level": self.manual_qos_level})

    def start_async_loop(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
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
                print(f"[ERROR] {e} - QoS szint: {self.qos_level}")
                await asyncio.sleep(1)

    def run_flask(self):
        self.app.run(host='0.0.0.0', port=5000)

    def run(self):
        flask_thread = threading.Thread(target=self.run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        self.start_async_loop()


if __name__ == '__main__':
    app = QoSMonitorApp()
    app.run()
