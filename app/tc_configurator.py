import subprocess


class TCConfigurator:
    def __init__(self, interface="lo"):
        self.interface = interface

    def apply_tc_settings(self, delay="100ms", loss="0.5%"):
        try:
            subprocess.run(["tc", "qdisc", "del", "dev", self.interface, "root"], check=True)
        except subprocess.CalledProcessError:
            pass
        subprocess.run(["tc", "qdisc", "add", "dev", self.interface, "root", "netem", "delay", delay, "loss", loss], check=True)

    def reset_tc(self):
        subprocess.run(["tc", "qdisc", "del", "dev", self.interface, "root"], check=True)
