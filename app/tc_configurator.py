import subprocess


class TCConfigurator:
    def __init__(self, interface="lo"):
        self.interface = interface

    def apply_tc_settings(self, delay="100ms"):
        subprocess.run(["tc", "qdisc", "del", "dev", self.interface, "root"])
        subprocess.run(["tc", "qdisc", "add", "dev", self.interface, "root", "netem", "delay", delay])
    def reset_tc(self):
        subprocess.run(["tc", "gdisc", "del", "dev", self.interface, "root"])