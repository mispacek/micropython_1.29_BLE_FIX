#!/usr/bin/env python3
"""Reject ignored or overridden BLE/Wi-Fi memory settings after an ESP32 build."""

import argparse
from pathlib import Path


def read_config(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdkconfig", type=Path)
    parser.add_argument(
        "--profile",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ports/esp32/boards/sdkconfig.ble_wifi_coex",
    )
    args = parser.parse_args()
    expected = read_config(args.profile)
    actual = read_config(args.sdkconfig)
    mismatches = [
        f"{key}: expected {value}, got {actual.get(key, 'missing')}"
        for key, value in expected.items()
        if actual.get(key) != value
    ]
    if mismatches:
        parser.exit(1, "BLE/Wi-Fi configuration mismatch:\n" + "\n".join(mismatches) + "\n")
    print(f"BLE/Wi-Fi profile verified: {len(expected)} settings")


if __name__ == "__main__":
    main()
