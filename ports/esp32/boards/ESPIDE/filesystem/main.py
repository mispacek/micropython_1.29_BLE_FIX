# SPDX-License-Identifier: MIT
# Adapted from ESP IDE main.py by Milan Spacek, 2019-2026.
# Install on the device filesystem as /main.py; do not freeze this file.

import gc
import os
import sys
import time

_ble_started = False
_ble_name = ""


def start_BLE():
    global _ble_name, _ble_started
    if _ble_started:
        return
    try:
        with open("/cfg/ble_name.cfg", "rb") as f:
            raw = f.read(32)
    except OSError as e:
        if e.args and e.args[0] == 2:
            print("Bluetooth is disabled")
        else:
            print("Failed to read Bluetooth configuration:", e)
        return

    # Match the ESP IDE name limit without silently changing an invalid name.
    name_b = raw.strip()
    if not 3 <= len(name_b) <= 8 or any(c < 32 or c > 126 for c in name_b):
        print("Invalid Bluetooth name (use 3-8 printable ASCII characters)")
        return

    try:
        from ble_repl_bletime import start_ble_repl

        start_ble_repl(name=name_b, slot=0)
        _ble_name = name_b.decode("ascii")
        _ble_started = True
        print("Bluetooth name:", _ble_name)
    except Exception as e:
        print("Failed to start Bluetooth:", e)


def autostart():
    try:
        with open("idecode", "r") as f:
            start_data = f.read(16)
    except OSError as e:
        if not e.args or e.args[0] != 2:
            print("Failed to read idecode:", e)
        return

    if "#autostart*" in start_data:
        print("Starting the program in 2 seconds")
        time.sleep(2)
        print("Starting...")
        try:
            # run_code is provided by the accompanying filesystem boot.py.
            run_code()  # noqa: F821
        except Exception as e:
            print("Program execution failed:")
            sys.print_exception(e)


gc.collect()
time.sleep_ms(100)
gc.collect()
print("ESP IDE MicroPython 1.29 BLE")
start_BLE()
autostart()
