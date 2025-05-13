class QoSSelector:
    def __init__(self):
        # Új küszöbértékek a latency és loss paraméterekhez
        self.qos_thresholds = {
            0: {"latency": 100, "loss": 1},  # QoS 0: <100 ms latency és <50% loss
            1: {"latency": 300, "loss": 5},  # QoS 1: 100-300 ms latency és <60% loss
        }
        self.qos_level = 0

    def decide_qos(self, latency, loss):
        """
        QoS szint döntése latency és packet loss alapján.
        :param latency: a késleltetés (ms-ban)
        :param loss: a csomagveszteség százalékban
        :return: a kiválasztott QoS szint (0, 1, 2)
        """
        if latency < self.qos_thresholds[0]["latency"] and loss < self.qos_thresholds[0]["loss"]:
            self.qos_level = 0  # QoS 0, ha a késleltetés és a veszteség alacsony
        elif (latency < self.qos_thresholds[0]["latency"] <= latency < self.qos_thresholds[1]["latency"]
              or self.qos_thresholds[0]["loss"] <= loss < self.qos_thresholds[1]["loss"]):
            self.qos_level = 1  # QoS 1, ha a késleltetés és a veszteség közepes
        else:
            self.qos_level = 2  # QoS 2, ha a késleltetés vagy a veszteség magas

        return self.qos_level

    def get_qos_level(self):
        return self.qos_level
