#!/usr/bin/env python3
"""Check final ELF addresses of frozen RISC-V native functions."""

import argparse
from pathlib import Path
import struct


def verify(data):
    if data[:6] != b"\x7fELF\x01\x01" or struct.unpack_from("<H", data, 18)[0] != 243:
        raise ValueError("Expected a little-endian ELF32 RISC-V image")
    section_offset = struct.unpack_from("<I", data, 32)[0]
    section_size, section_count = struct.unpack_from("<HH", data, 46)
    sections = [
        struct.unpack_from("<10I", data, section_offset + i * section_size)
        for i in range(section_count)
    ]
    symbols = []
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        strings_section = sections[section[6]]
        strings = data[strings_section[4] : strings_section[4] + strings_section[5]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name_offset, address, size, info, _, index = struct.unpack_from(
                "<IIIBBH", data, offset
            )
            if index == 0 or index >= len(sections) or not sections[index][2] & 4:
                continue  # Only symbols stored in executable sections.
            name = strings[name_offset : strings.find(b"\x00", name_offset)].decode()
            if info & 15 == 1 and name.startswith("fun_data_"):  # STT_OBJECT
                symbols.append((name, address, size))
    if not symbols:
        raise ValueError("No frozen native code symbols found; an unstripped ELF is required")
    errors = [
        "%s: address=0x%x size=%d" % (name, address, size)
        for name, address, size in symbols
        if address & 1 or size & 1
    ]
    if errors:
        raise ValueError("Unaligned frozen RISC-V native code:\n" + "\n".join(errors))
    return symbols


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    try:
        symbols = verify(args.elf.read_bytes())
    except (ValueError, struct.error) as error:
        parser.exit(1, "%s\n" % error)
    for name, address, size in symbols:
        print("0x%08x %5d %s" % (address, size, name))
    print("Verified %d aligned frozen native functions" % len(symbols))


if __name__ == "__main__":
    main()
