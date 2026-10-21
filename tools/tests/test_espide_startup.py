"""Host-side startup contract tests; these do not simulate the BLE radio."""

import errno
import io
from contextlib import ExitStack
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

MAIN = Path(__file__).resolve().parents[2] / "ports/esp32/boards/ESPIDE/filesystem/main.py"
CODE = compile(MAIN.read_text(), str(MAIN), "exec")


class StartupTests(unittest.TestCase):
    def run_startup(self, name=None, program=None, start_error=None, read_error=None):
        start = Mock(side_effect=start_error)
        run = Mock()
        module = types.SimpleNamespace(start_ble_repl=start)

        def open_file(path, mode):
            if path == "/cfg/ble_name.cfg":
                if read_error:
                    raise read_error
                if name is None:
                    raise OSError(errno.ENOENT)
                return io.BytesIO(name)
            if path == "idecode" and program is not None:
                return io.StringIO(program)
            raise OSError(errno.ENOENT)

        namespace = {"run_code": run}
        with ExitStack() as stack:
            stack.enter_context(patch("builtins.open", side_effect=open_file))
            stack.enter_context(patch("time.sleep_ms", create=True))
            stack.enter_context(patch("time.sleep"))
            stack.enter_context(patch("builtins.print"))
            stack.enter_context(patch.dict(sys.modules, {"ble_repl_bletime": module}))
            exec(CODE, namespace)
            # Repeat the public start helper: a successful start must be idempotent.
            if namespace["_ble_started"]:
                namespace["start_BLE"]()
        return namespace, start, run

    def test_valid_name_starts_once_on_slot_zero(self):
        namespace, start, _ = self.run_startup(b"  ESPIDE\r\n")
        start.assert_called_once_with(name=b"ESPIDE", slot=0)
        self.assertTrue(namespace["_ble_started"])
        self.assertEqual(namespace["_ble_name"], "ESPIDE")

    def test_missing_or_invalid_config_does_not_start_ble(self):
        for name in (None, b"", b"AB", b"123456789", b"ESP\x00IDE", b"ESP\xffIDE"):
            with self.subTest(name=name):
                namespace, start, _ = self.run_startup(name)
                start.assert_not_called()
                self.assertFalse(namespace["_ble_started"])

    def test_config_io_error_does_not_start_ble(self):
        _, start, _ = self.run_startup(read_error=OSError(errno.EIO))
        start.assert_not_called()

    def test_driver_failure_does_not_prevent_program_autostart(self):
        namespace, start, run = self.run_startup(
            b"ESPIDE", "#autostart*\nprint(1)", OSError(errno.ENOMEM)
        )
        start.assert_called_once()
        self.assertFalse(namespace["_ble_started"])
        run.assert_called_once_with()

    def test_program_autostart_without_ble(self):
        _, start, run = self.run_startup(program="#autostart*\nprint(1)")
        start.assert_not_called()
        run.assert_called_once_with()

    def test_program_without_marker_does_not_autostart(self):
        _, _, run = self.run_startup(program="print(1)")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
