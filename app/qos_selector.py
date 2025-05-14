class QoSSelector:
    def __init__(self):
        # Küszöbértékek a QoS 0 és QoS 1 szintekhez.
        # QoS 0 feltétele: késleltetés < 50 ms és csomagveszteség < 5%
        # QoS 1 feltétele: késleltetés < 100 ms és csomagveszteség < 10%
        self.qos_thresholds = {
            0: {"latency": 50, "loss": 5},
            1: {"latency": 100, "loss": 10},
        }
        self.qos_level = None

    def decide_qos(self, latency, loss):
        """
        QoS szint kiválasztása a mért késleltetés és csomagveszteség alapján.

        :param latency: A késleltetés (ms-ban)
        :param loss: A csomagveszteség százalékban (%)
        :return: A kiválasztott QoS szint (0, 1 vagy 2)
                 - 0: alacsony késleltetés és veszteség
                 - 1: közepes késleltetés vagy veszteség
                 - 2: magas késleltetés vagy veszteség
        """
        if latency < self.qos_thresholds[0]["latency"] and loss < self.qos_thresholds[0]["loss"]:
            self.qos_level = 0  # Ideális körülmények: QoS 0
        elif latency < self.qos_thresholds[1]["latency"] and loss < self.qos_thresholds[1]["loss"]:
            self.qos_level = 1  # Közepes körülmények: QoS 1
        else:
            self.qos_level = 2  # Magas késleltetés vagy veszteség: QoS 2

        return self.qos_level

    def get_qos_level(self):
        """
        Visszaadja az aktuális QoS szintet.
        """
        return self.qos_level
