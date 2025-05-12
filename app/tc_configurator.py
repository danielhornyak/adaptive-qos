import subprocess


class TCConfigurator:
    def __init__(self, interface="eth0"):
        self.interface = interface

    def apply_tc_settings(self, delay="100ms", loss="1%"):
        subprocess.run(["tc", "qdisc", "del", "dev", self.interface, "root"], stderr=subprocess.DEVNULL)
        subprocess.run(["tc", "qdisc", "add", "dev", self.interface, "root", "netem", "delay", delay, "loss", loss])

    def reset_tc(self):
        subprocess.run(["tc", "disc", "del", "dev", self.interface, "root"], stderr=subprocess.DEVNULL)