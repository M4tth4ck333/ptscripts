import subprocess
import sys
from abc import ABC, abstractmethod

class AbstractBasicCleanup(ABC):
    def __init__(self):
        pass

    def run(self, cmd, check=True, capture_output=False):
        print(f"$ {' '.join(cmd)}")
        try:
            if capture_output:
                return subprocess.check_output(cmd, text=True).strip()
            else:
                subprocess.run(cmd, check=check)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Command failed: {' '.join(cmd)}\n{e}")
            if check:
                sys.exit(1)

    def disable_ip_forwarding(self):
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("0\n")
            print("IP forwarding disabled.")
        except Exception as e:
            print(f"[WARNING] Could not disable IP forwarding: {e}")

    @abstractmethod
    def perform_cleanup(self):
        """
        Hier werden alle Cleanup-Schritte definiert,
        die von Unterklassen implementiert werden müssen.
        """
        pass

    def cleanup(self):
        """
        Führt das Cleanup aus, indem perform_cleanup aufgerufen wird.
        """
        print("Starting cleanup...")
        self.perform_cleanup()
        print("Cleanup done.")

# Beispiel einer konkreten Implementierung
class BasicCleanup(AbstractBasicCleanup):
    def perform_cleanup(self):
        self.run(["killall", "airbase-ng"], check=False)
        self.run(["service", "dhcp3-server", "stop"], check=False)
        self.run(["killall", "python"], check=False)
        self.run(["ifconfig", "mitm", "down"], check=False)
        self.run(["brctl", "delbr", "mitm"], check=False)
        self.run(["iptables", "--flush"])
        self.run(["iptables", "--table", "nat", "--flush"])
        self.run(["iptables", "--delete-chain"])
        self.run(["iptables", "--table", "nat", "--delete-chain"])
        self.disable_ip_forwarding()
        self.run(["airmon-ng", "stop", "mon0"], check=False)
        self.run(["route", "del", "-net", "192.168.3.0", "netmask", "255.255.255.0", "gw", "192.168.3.1"], check=False)
        self.run(["ifconfig"])
        self.run(["route", "-n"])
        self.run(["iptables", "-nvL", "-t", "nat"])

if __name__ == "__main__":
    cleanup = BasicCleanup()
    cleanup.cleanup()
