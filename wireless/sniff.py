#!/usr/bin/env python3
"""
Simple WiFi packet sniffer for macOS using tcpdump.
Port of sniff.sh by Mike Tigas to Python 3.
Modernisiertes Python 3 CLI-Tool zur Verwaltung von Volume Shadow Copies (VSS).
Port von 'vssown.vbs' von Mark Baggett & Tim Tomes.
Inklusive Farbausgabe, Logging und modularem Aufbau.
Usage:
    python3 sniff.py [keyword]

The optional keyword is appended to the output filename.
Requirements:
- tcpdump must be installed and accessible.
- Run with sudo or appropriate privileges.
Copyright (c) 2025 Jan Schröder. Alle Rechte vorbehalten.
Basierend auf der Originalidee von Mark Baggett (@MarkBaggett) und Tim Tomes (@LaNMaSteR53).
part of ByKnocKulasT Toolkits.
"""

import subprocess
import sys
import os
import datetime

def get_interface_info(interface):
    import re
    try:
        ifconfig_output = subprocess.check_output(['ifconfig', interface], text=True)
    except subprocess.CalledProcessError:
        print(f"Error: Interface '{interface}' not found.")
        sys.exit(1)

    ip_addr = None
    mac_addr = None

    for line in ifconfig_output.splitlines():
        if 'inet ' in line:
            # Extract IP address
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
            if match:
                ip_addr = match.group(1)
        if 'ether ' in line:
            # Extract MAC address
            match = re.search(r'ether ([0-9a-f:]{17})', line)
            if match:
                mac_addr = match.group(1)

    if not ip_addr:
        print(f"Could not find IP address for interface {interface}")
        sys.exit(1)
    if not mac_addr:
        print(f"Could not find MAC address for interface {interface}")
        sys.exit(1)
    return ip_addr, mac_addr

def main():
    # Default WiFi interface on MacOS
    wifi_interface = "en1"

    # Accept optional keyword argument
    keyword = sys.argv[1] if len(sys.argv) > 1 else None

    ip_addr, mac_addr = get_interface_info(wifi_interface)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    if keyword:
        output_file = os.path.expanduser(f"~/Desktop/{timestamp}_{keyword}.pcap")
    else:
        output_file = os.path.expanduser(f"~/Desktop/{timestamp}.pcap")

    # Create empty file so it is owned by current user (tcpdump runs as root)
    with open(output_file, 'wb') as f:
        pass

    print(f"Starting packet capture on {wifi_interface}...")
    print(f"Output file: {output_file}")
    print("Press Ctrl-C to stop.\n")

    tcpdump_cmd = [
        "sudo", "tcpdump",
        "-i", wifi_interface,
        "-I",               # monitor mode
        "-n",               # no name resolution
        "-s", "0",          # capture full packet
        "-w", output_file,
        f"not ether host {mac_addr}",
        f"and not host {ip_addr}",
        "and not (wlan[0:1] & 0xfc == 0x40)",  # Probe request
        "and not (wlan[0:1] & 0xfc == 0x50)",  # Probe response
        "and not (wlan[0:1] & 0xfc == 0x80)",  # Beacon
        "and not (wlan[0:1] & 0xfc == 0xa4)",  # Power save
        "and not (wlan[0:1] & 0xfc == 0xc4)",  # Clear to send
        "and not (wlan[0:1] & 0xfc == 0xd4)"   # ACK frame
    ]

    try:
        subprocess.run(tcpdump_cmd)
    except KeyboardInterrupt:
        print("\nCapture stopped by user.")
    except Exception as e:
        print(f"Error running tcpdump: {e}")

if __name__ == "__main__":
    main()
