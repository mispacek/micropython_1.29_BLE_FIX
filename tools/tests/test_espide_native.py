"""Regressions for odd-sized RISC-V frozen code and final ELF alignment."""

from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS.parent / "py"))


def load_tool(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MPY = load_tool("espide_mpy_tool", "mpy-tool.py")
VERIFY = load_tool("espide_native_verify", "verify_esp32_frozen_native.py")


def elf_fixture(address, size, machine=243):
    image = bytearray(512)
    image[:6] = b"\x7fELF\x01\x01"
    struct.pack_into("<H", image, 18, machine)
    struct.pack_into("<I", image, 32, 64)
    struct.pack_into("<HH", image, 46, 40, 4)
    struct.pack_into("<10I", image, 104, 0, 1, 6, 0x42000000, 400, 16, 0, 0, 2, 0)
    struct.pack_into("<10I", image, 144, 0, 3, 0, 0, 256, 64, 0, 0, 1, 0)
    struct.pack_into("<10I", image, 184, 0, 2, 0, 0, 320, 32, 2, 0, 4, 16)
    name = b"\x00fun_data_ble_write\x00"
    image[256 : 256 + len(name)] = name
    struct.pack_into("<IIIBBH", image, 336, 1, address, size, 1, 0, 1)
    return image


class FrozenNativeTests(unittest.TestCase):
    def test_storage_padding_preserves_code_bytes(self):
        for arch, size, storage_size in (
            (MPY.MP_NATIVE_ARCH_RV32IMC, 5, 6),
            (MPY.MP_NATIVE_ARCH_RV64IMC, 5, 6),
            (MPY.MP_NATIVE_ARCH_RV32IMC, 6, 6),
            (MPY.MP_NATIVE_ARCH_XTENSAWIN, 5, 5),
        ):
            with self.subTest(arch=arch, size=size):
                code = MPY.RawCodeNative.__new__(MPY.RawCodeNative)
                code.scope_flags = code.type_sig = 0
                code.code_kind = MPY.MP_CODE_NATIVE_ASM
                code.qstr_table = [SimpleNamespace(str="test.py")]
                code.escaped_name = "test"
                code.fun_data = bytes(range(size))
                code.fun_data_attributes = ""
                code.freeze_children = lambda _: None
                code.freeze_raw_code = lambda *_: None
                output = io.StringIO()
                previous_arch = MPY.config.native_arch if hasattr(MPY.config, "native_arch") else 0
                try:
                    MPY.config.native_arch = arch
                    with redirect_stdout(output):
                        code.freeze()
                finally:
                    MPY.config.native_arch = previous_arch
                self.assertIn("fun_data_test[%d]" % storage_size, output.getvalue())
                self.assertEqual(code.fun_data, bytes(range(size)))
                emitted = output.getvalue().split("= {", 1)[1].split("};", 1)[0]
                import re

                emitted_bytes = bytes(int(x, 16) for x in re.findall(r"0x([0-9a-f]{2})", emitted))
                self.assertEqual(emitted_bytes, bytes(range(size)) + bytes(storage_size - size))

    def test_final_elf_accepts_aligned_native_code(self):
        self.assertEqual(VERIFY.verify(elf_fixture(0x420557E4, 548))[0][1], 0x420557E4)

    def test_final_elf_rejects_reported_crash_address(self):
        with self.assertRaisesRegex(ValueError, "address=0x420557e3"):
            VERIFY.verify(elf_fixture(0x420557E3, 547))

    def test_final_elf_rejects_odd_storage_size(self):
        with self.assertRaisesRegex(ValueError, "size=547"):
            VERIFY.verify(elf_fixture(0x420557E4, 547))

    def test_xtensa_accepts_word_aligned_odd_length_code(self):
        self.assertEqual(VERIFY.verify(elf_fixture(0x420557E4, 547, 94))[0][1], 0x420557E4)

    def test_xtensa_rejects_halfword_only_alignment(self):
        with self.assertRaisesRegex(ValueError, "address=0x420557e2"):
            VERIFY.verify(elf_fixture(0x420557E2, 548, 94))

    def test_unsupported_machine_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported ELF machine"):
            VERIFY.verify(elf_fixture(0x420557E4, 548, 3))


if __name__ == "__main__":
    unittest.main()
