"""Self-checks for sidemdm.py. Run: python -m unittest tools/test_sidemdm.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root
import sidemdm  # noqa: E402


class SafeLogTest(unittest.TestCase):
    def test_passes_through_normal_text(self):
        self.assertEqual(sidemdm._safe("GET"), "GET")
        self.assertEqual(sidemdm._safe("/releases/dpc-1.0.1.apk"), "/releases/dpc-1.0.1.apk")

    def test_strips_escape_and_newlines(self):
        # A path carrying an ANSI escape must not reach the terminal verbatim.
        self.assertEqual(sidemdm._safe("/a\x1b[31mX"), "/a�[31mX")
        out = sidemdm._safe("/x\r\n\ty")
        self.assertNotIn("\n", out)
        self.assertNotIn("\r", out)
        self.assertNotIn("\t", out)

    def test_handles_non_str(self):
        self.assertEqual(sidemdm._safe(None), "None")


if __name__ == "__main__":
    unittest.main()
