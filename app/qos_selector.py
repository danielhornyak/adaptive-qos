class QoSSelector:
    def __init__(self):
        self.qos_thresholds = {
            0: {"latency": 50, "loss": 1},
            1: {"latency": 100, "loss": 5},
        }
        self.gos_level = 0

    def decide_qos(self, latency, loss):
        if latency < self.qos_thresholds[0]["latency"] and loss < self.qos_thresholds[0]["loss"]:
            self.gos_level = 0
            return self.gos_level
        elif (self.qos_thresholds[0]["latency"] <= latency < self.qos_thresholds[1]["latency"] or
              self.qos_thresholds[0]["loss"] <= loss < self.qos_thresholds[1]["loss"]):
            self.gos_level = 1
            return self.gos_level
        else:
            self.gos_level = 2
            return self.gos_level

    def get_gos_level(self):
        return self.gos_level
