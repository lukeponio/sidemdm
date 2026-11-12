"""Self-checks for generate_qr.py. Run: python -m unittest tools/test_generate_qr.py"""
import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_qr as g  # noqa: E402


class ChecksumTest(unittest.TestCase):
    def test_urlsafe_no_padding(self):
        data = b"\xff" * 1000
        c = g.apk_checksum(data)
        self.assertNotIn("=", c)
        self.assertNotIn("+", c)
        self.assertNotIn("/", c)
        self.assertEqual(base64.urlsafe_b64decode(c + "="), hashlib.sha256(data).digest())


class UrlValidationTest(unittest.TestCase):
    def test_accepts_lan_hostname(self):
        g.validate_lan_url("https://enroll.devices.example.com/releases/dpc-1.0.0.apk")

    def test_rejects(self):
        for bad in [
            "http://enroll.devices.example.com/releases/dpc-1.0.0.apk",
            "https://192.168.50.10/releases/dpc-1.0.0.apk",
            "https://enroll.local/releases/dpc-1.0.0.apk",
            "https://enroll/releases/dpc-1.0.0.apk",
            "https://user:pw@enroll.devices.example.com/releases/dpc-1.0.0.apk",
            "https://enroll.devices.example.com/releases/dpc-1.0.0.apk?x=1",
            "https://enroll.devices.example.com/releases/",
        ]:
            with self.subTest(bad), self.assertRaises(g.ConfigError):
                g.validate_lan_url(bad)

    def test_public_resolution_rejected(self):
        orig = g.socket.getaddrinfo
        g.socket.getaddrinfo = lambda *a, **k: [(0, 0, 0, "", ("8.8.8.8", 443))]
        try:
            with self.assertRaises(g.ConfigError):
                g.check_resolves_to_lan("enroll.devices.example.com")
            g.socket.getaddrinfo = lambda *a, **k: [(0, 0, 0, "", ("192.168.50.10", 443))]
            self.assertEqual(g.check_resolves_to_lan("x.example.com"), ["192.168.50.10"])
        finally:
            g.socket.getaddrinfo = orig


class LanHttpTest(unittest.TestCase):
    def test_accepts_private_ip(self):
        g.validate_lan_http_url("http://192.168.1.50/releases/dpc-1.0.0.apk")
        p = g.build_payload(g.DEFAULT_COMPONENT, "http://10.0.0.5/releases/dpc-1.0.0.apk", "abc")
        self.assertTrue(p[g.EXTRA + "PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION"].startswith("http://10."))

    def test_rejects_hostname_public_and_loopback(self):
        for bad in ["http://enroll.example.com/releases/dpc-1.0.0.apk",
                    "http://8.8.8.8/releases/dpc-1.0.0.apk",
                    "http://127.0.0.1/releases/dpc-1.0.0.apk"]:
            with self.subTest(bad), self.assertRaises(g.ConfigError):
                g.validate_lan_http_url(bad)


class PayloadTest(unittest.TestCase):
    def test_payload_keys_and_no_mobile_data(self):
        p = g.build_payload(g.DEFAULT_COMPONENT, "https://e.example.com/releases/dpc-1.0.0.apk", "abc")
        self.assertEqual(set(p), {
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME",
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION",
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM",
        })
        self.assertNotIn("USE_MOBILE_DATA", json.dumps(p))

    def test_empty_checksum_rejected(self):
        with self.assertRaises(g.ConfigError):
            g.build_payload(g.DEFAULT_COMPONENT, "https://e.example.com/releases/dpc-1.0.0.apk", "")


class CliTest(unittest.TestCase):
    def test_missing_apk_and_immutability(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self.assertEqual(g.main(["--apk", str(d / "nope.apk"), "--version", "1.0.0",
                                     "--host", "e.example.com", "--out", str(d / "r")]), 1)
            apk = d / "a.apk"
            apk.write_bytes(b"PK\x03\x04fake")
            site = d / "site"
            (site / "qr").mkdir(parents=True)
            args = ["--apk", str(apk), "--version", "1.0.0", "--host", "e.example.com",
                    "--out", str(d / "r"), "--site", str(site)]
            self.assertEqual(g.main(args), 0)
            self.assertTrue((d / "r" / "enrollment.png").read_bytes().startswith(b"\x89PNG"))
            payload = json.loads((d / "r" / "enrollment.json").read_text())
            self.assertEqual(payload["android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM"],
                             g.apk_checksum(apk.read_bytes()))
            # AT-11 staging guard: changed bytes under the same version are refused.
            apk.write_bytes(b"PK\x03\x04changed")
            self.assertEqual(g.main(args), 1)


if __name__ == "__main__":
    unittest.main()
