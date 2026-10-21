# ESP IDE: MicroPython v1.29.0 for ESP32-C3 and ESP32-C6

This repository starts at the official `v1.29.0` release, commit
`0fd6c573ea815774668bbb16b8e197c8822368b2`. The release tag is retained unchanged.
Custom firmware uses the existing `ESP32_GENERIC_C3` and `ESP32_GENERIC_C6` board
names, with ESP-IDF **v5.5.2**. Other board configurations are unchanged.

## Memory profile

Both boards append `ports/esp32/boards/sdkconfig.ble_wifi_coex` after their
standard configuration and start the Python GC heap at **48 KiB**. The split
heap can still grow automatically. The profile retains the final settings from
`mispacek/micropython_BLE_FIX` at `403ac1335`, including one NimBLE connection,
three sockets, four active TCP connections, and reduced Wi-Fi/TCP buffers.

This is the selected legacy profile, not the whole upstream `sdkconfig.free_ram`
profile. The build workflow verifies the effective `sdkconfig`, so an ignored
or overridden setting fails the firmware job. Runtime RAM savings and radio
coexistence still require tests on both physical chips.

## Frozen Python modules

Both boards use one manifest at `ports/esp32/boards/ESPIDE/manifest.py`. It keeps
the standard MicroPython networking and driver modules, then freezes:

- `ble_repl_bletime.py` and `bletime.py`: the user-selected sources from
  `instalace_new/esp32_s3_1_29_BLE`, copied on 2026-10-21.
- `eyes_optimized.py`, `fm_rpc.py`, `espide_monofont.py`, `pvstore.py`,
  `oled_spi.py`, `oled.py`, `oled_charts.py`, `vl53l0x.py`, and `tcs34725.py`:
  refreshed from the same user-selected S3 installation on 2026-10-21, with
  English comments, descriptions and diagnostics.
- `AccelStepper.py`: source from the old repository at `403ac1335`, with a MIT
  header and English comments.

There are **12 custom frozen modules** in total. All nine selected libraries
were checked against their source snapshots; translation preserves their
non-string AST, APIs and protocol tokens. `pvstore` deliberately retains the
legacy `ano`/`ne` boolean input aliases for existing configuration files, as
requested. All of its diagnostics are English. `espide_monofont` freezes the
renderer; MFNT font data files are still loaded from the device filesystem.

`ble_flag.py` is not included: the selected BLE driver and time compatibility
module use native interruption. The legacy `fm_rpc.py` treats its `ble_flag`
import as optional. No other peripheral library versions are silently updated.

The copyright holder authorized MIT licensing of the imported ESP IDE code
for this fork on 2026-10-21. Comments, diagnostics and error hints are in
English for the global firmware distribution. Translation changes only
comments and human-readable strings; APIs and protocol tokens are preserved.
The existing MIT BLE driver and
time proxy remain byte-for-byte copies. The Moonbench attribution and MIT
notice for `oled_charts.py` are retained in `ports/esp32/boards/ESPIDE/LICENSE`.
`SOURCES.json` records origins, original source hashes and current fork hashes;
these snapshots are excluded from automatic Python reformatting and linting.
The new manifest, startup file, verifier and host tests remain checked.

## Filesystem startup files

`ports/esp32/boards/ESPIDE/filesystem/` contains `boot.py`, `main.py`, a MIT
`LICENSE`, and a small `files.lst` for the two startup files. They are **not frozen**. The firmware binary
does not install them into the device filesystem automatically.

Upload `boot.py` as `/boot.py` and `main.py` as `/main.py`. The supplied `boot.py`
is the ESP IDE source from the same S3 installation with its MIT license header
and English diagnostics and comments. Its control flow is unchanged. It provides
`run_code()` and the usual ESP IDE REPL helpers. The adapted `main.py` imports
its dependencies explicitly and uses a C3/C6 banner.

- BLE starts only when `/cfg/ble_name.cfg` contains a stripped name of 3-8
  printable ASCII characters. Invalid names are rejected instead of truncated
  or repaired. Missing configuration leaves BLE disabled.
- The frozen `ble_repl_bletime.start_ble_repl(name=name, slot=0)` is loaded only
  after valid configuration. Calling `start_BLE()` again after success is safe.
- A user program whose first 16 characters contain `#autostart*` still starts
  through `run_code()` after two seconds, including when BLE is disabled or its
  startup fails.
- Other filesystem libraries from the normal ESP IDE installation remain
  separate. This directory is a startup-file package, not a full web installer.

When updating an existing installation, remove obsolete filesystem copies of
the twelve frozen modules from `/` and `/lib/` (including `.mpy` copies), or make
sure they are the intended versions. Filesystem copies can shadow frozen code.
Keep the other, non-frozen ESP IDE libraries installed.

## Build and artifacts

For installation, flash the combined **`firmware.bin` at `0x0`**, then reset.
`micropython.bin` is only the application at `0x10000`; it requires the matching
bootloader and partition table. Each firmware artifact includes `FLASHING.txt`.

The frozen-code generator pads RISC-V native arrays to an even storage size.
Without this padding, odd-length arrays can leave later functions at odd
addresses despite their alignment attributes. The C3 crash was reproduced by
calling the frozen BLE stream's `write(b"")` before a connection, with its
entry point at `0x420557e3`. The workflow now checks every frozen native code
symbol's address and size in the final ELF and retains that ELF for diagnosis.
BLE protocol and driver sources are unchanged by this build fix.

Use the MicroPython ESP32 build instructions with ESP-IDF v5.5.2 and the pinned
submodules from this checkout. After sourcing the IDF environment:

```sh
make -C mpy-cross
make -C ports/esp32 submodules
make -C ports/esp32 BOARD=ESP32_GENERIC_C3
make -C ports/esp32 BOARD=ESP32_GENERIC_C6
python tools/verify_esp32_ble_wifi.py ports/esp32/build-ESP32_GENERIC_C3/sdkconfig
python tools/verify_esp32_ble_wifi.py ports/esp32/build-ESP32_GENERIC_C6/sdkconfig
```

The **ESP32 BLE Wi-Fi firmware** GitHub Actions workflow builds both boards,
checks their effective configuration, and uploads separate firmware and
filesystem artifacts. Firmware artifacts include `firmware.bin`,
`micropython.bin`, bootloader/partition files, `sdkconfig`, build identity,
submodule versions and SHA-256 checksums. Build identity records the actual
custom commit; `v1.29.0` identifies the unchanged upstream base.

Host startup checks can also run without ESP-IDF:

```sh
python -m unittest discover -s tools/tests -p 'test_espide_*.py' -v
python tools/verify_espide_english.py
```

Before adding a frozen library, review all comments, docstrings and diagnostics
for English text. The source guard checks every Python file in the shared
modules and filesystem directories, including newly added files. It rejects
non-ASCII source and known Czech phrases, but does not replace language review.

Host tests and successful firmware builds do not prove BLE file transfer,
Ctrl+C, print-flood recovery, or simultaneous Wi-Fi/BLE operation on hardware.
