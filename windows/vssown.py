#!/usr/bin/env python3
"""
Modernisiertes Python 3 CLI-Tool zur Verwaltung von Volume Shadow Copies (VSS).
Port von 'vssown.vbs' von Mark Baggett & Tim Tomes.
Inklusive Farbausgabe, Logging und modularem Aufbau.

Copyright (c) 2025 Jan Schröder. Alle Rechte vorbehalten.
Basierend auf der Originalidee von Mark Baggett (@MarkBaggett) und Tim Tomes (@LaNMaSteR53).
Teil des ByKnocKulasT Toolkits.
"""

import argparse
import logging
import os
import subprocess
import sys

import wmi
from colorama import init, Fore, Style

# Initialisierung
init(autoreset=True)
c = wmi.WMI()
logging.basicConfig(
    filename="vssown.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

vss_service = c.Win32_Service(Name="VSS")[0]

def log_print(message, level="info"):
    colors = {
        "info": Fore.GREEN,
        "warn": Fore.YELLOW,
        "error": Fore.RED
    }
    color = colors.get(level, Fore.WHITE)
    print(color + message)
    getattr(logging, level, logging.info)(message)

def list_shadow_copies():
    print(Fore.CYAN + "SHADOW COPIES\n===============\n")
    for sc in c.Win32_ShadowCopy():
        for prop in sc.properties.keys():
            print(f"[*] {prop.replace('_', ' ').title()}: {getattr(sc, prop)}")
        print()

def start_service():
    result = vss_service.StartService()
    log_print(f"[*] Start signal sent to {vss_service.Name} service.")
    return result

def stop_service():
    result = vss_service.StopService()
    log_print(f"[*] Stop signal sent to {vss_service.Name} service.")
    return result

def service_status():
    log_print(f"[*] VSS service status: {vss_service.State}")

def service_mode(mode=None):
    if mode:
        mode = mode.capitalize()
        if mode not in ["Manual", "Automatic", "Disabled"]:
            log_print(f"[!] '{mode}' is not a valid mode.", "error")
            return 1
        result = vss_service.ChangeStartMode(mode)
        log_print(f"[*] Service mode set to '{mode}'")
        return result
    else:
        log_print(f"[*] Current start mode: {vss_service.StartMode}")

def create_shadow_copy(drive_letter):
    volume = f"{drive_letter.upper()}:\\"
    obj = c.Win32_ShadowCopy()[0]
    result, out = obj.Create(volume, "ClientAccessible")
    log_print("[*] Shadow copy creation attempted.")
    return result

def delete_shadow_copy(id_or_all):
    for sc in c.Win32_ShadowCopy():
        if id_or_all == "*" or sc.ID == id_or_all:
            log_print(f"[*] Deleting shadow copy {sc.DeviceObject or sc.ID}")
            sc.Delete_()

def mount_shadow_copy(path, device_object):
    cmd = f'mklink /D "{path}" "{device_object}:\\"'
    subprocess.run(["cmd", "/C", cmd], shell=True)
    log_print(f"[*] Mounted {device_object} to {path}")

def execute_from_shadow(file_rel_path):
    for sc in c.Win32_ShadowCopy():
        device = sc.DeviceObject.replace("?", "\\\\?\\GLOBALROOT")
        full_path = os.path.join(device, file_rel_path.strip("\\"))
        log_print(f"[*] Attempting to execute: {full_path}")
        ret = subprocess.run(full_path, shell=True)
        if ret.returncode != 0:
            log_print(f"[!] Execution failed with return code {ret.returncode}", "error")
        else:
            log_print("[*] Process created.")

def show_storage():
    print(Fore.CYAN + "SHADOW STORAGE\n==============\n")
    for store in c.Win32_ShadowStorage():
        print(f"[*] Allocated: {int(store.AllocatedSpace/1e6)}MB")
        print(f"[*] Maximum:   {int(store.MaxSpace/1e6)}MB")
        print(f"[*] Used:      {int(store.UsedSpace/1e6)}MB\n")

def set_storage_size(bytes_):
    for store in c.Win32_ShadowStorage():
        store.MaxSpace = int(bytes_)
        store.Put_()
    log_print(f"[*] Storage size set to {int(bytes_ / 1e6)}MB.")

def main():
    parser = argparse.ArgumentParser(description="Volume Shadow Copy Management Tool (Python Version)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List shadow copies")
    sub.add_parser("start", help="Start the VSS service")
    sub.add_parser("stop", help="Stop the VSS service")
    sub.add_parser("status", help="Check VSS service status")
    sub.add_parser("store", help="Show shadow storage stats")

    mode = sub.add_parser("mode", help="Show or change start mode")
    mode.add_argument("mode", nargs="?", help="Manual|Automatic|Disabled")

    create = sub.add_parser("create", help="Create shadow copy")
    create.add_argument("drive_letter")

    delete = sub.add_parser("delete", help="Delete a shadow copy")
    delete.add_argument("id")

    mount = sub.add_parser("mount", help="Mount a shadow copy")
    mount.add_argument("path")
    mount.add_argument("device")

    exe = sub.add_parser("execute", help="Execute a file from shadow copy")
    exe.add_argument("path")

    size = sub.add_parser("size", help="Set reserved space")
    size.add_argument("bytes", type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    match args.command:
        case "list": list_shadow_copies()
        case "start": start_service()
        case "stop": stop_service()
        case "status": service_status()
        case "mode": service_mode(args.mode)
        case "create": create_shadow_copy(args.drive_letter)
        case "delete": delete_shadow_copy(args.id)
        case "mount": mount_shadow_copy(args.path, args.device)
        case "execute": execute_from_shadow(args.path)
        case "store": show_storage()
        case "size": set_storage_size(args.bytes)

if __name__ == "__main__":
    main()
