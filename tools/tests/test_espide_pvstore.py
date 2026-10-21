"""Persistent variable compatibility and English error reporting."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import tempfile
import unittest

PVSTORE = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "ports/esp32/boards/ESPIDE/modules/pvstore.py")
)


class PersistentVariableTests(unittest.TestCase):
    def test_legacy_boolean_aliases_are_retained(self):
        for text in ("true", "yes", "1", "on", "ano"):
            self.assertTrue(PVSTORE["_bool"](text))
        for text in ("false", "no", "0", "off", "ne"):
            self.assertFalse(PVSTORE["_bool"](text))

    def test_save_load_round_trip(self):
        values = {"count": 12, "enabled": True, "label": "ESP IDE", "items": [1, 2, 3]}
        with tempfile.TemporaryDirectory() as directory:
            filename = str(Path(directory) / "variables.ini")
            self.assertTrue(PVSTORE["save"](filename, values, None, list(values)))
            restored = {}
            self.assertTrue(PVSTORE["load"](filename, restored))
            self.assertEqual(restored, values)

    def test_missing_file_reports_english_message(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                result = PVSTORE["load"](str(Path(directory) / "missing.ini"), {})
            self.assertFalse(result)
            self.assertIn("Failed to load variables: file not found", output.getvalue())


if __name__ == "__main__":
    unittest.main()
