class QoSSelector:
    def __init__(self):
        self.qos_thresholds = {
            0: {"latency": 50, "loss": 1},
            1: {"latency": 100, "loss": 5},
        }
        self.qos_level = 0

    def decide_qos(self, latency, loss):
        if latency < self.qos_thresholds[0]["latency"] and loss < self.qos_thresholds[0]["loss"]:
            self.qos_level = 0
            return self.qos_level
        elif (self.qos_thresholds[0]["latency"] <= latency < self.qos_thresholds[1]["latency"] and
              self.qos_thresholds[0]["loss"] <= loss < self.qos_thresholds[1]["loss"]):
            self.qos_level = 1
            return self.qos_level
        else:
            self.qos_level = 2
            return self.qos_level

    def get_qos_level(self):
        return self.qos_level