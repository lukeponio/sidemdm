#!/usr/bin/env python3
"""sidemdm: one command to enroll a phone from this computer and hand it back unmanaged.

It finds this machine's LAN address, builds the provisioning QR for the APK in dist/, serves
the APK over the LAN, and prints the QR in the terminal to scan. The phone downloads the APK,
creates a work profile, and you remove that profile from the app to end up with a clean,
unmanaged phone that keeps its personal profile.

    python sidemdm.py                 # auto-detect IP, port 8080, APK from dist/
    python sidemdm.py --ip 192.168.0.22 --port 8080 --apk dist/sidemdm.apk

Requires: Python 3.10+ and `segno` (pip install -r tools/requirements.txt). No Android SDK,
no domain, no certificate. The QR pins the APK by SHA-256, so a swapped file is rejected.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import generate_qr as g  # noqa: E402

APK_MIME = "application/vnd.android.package-archive"


def detect_lan_ip() -> str | None:
    """Best-effort private IPv4 of this machine (no traffic is actually sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("192.168.255.255", 9))  # a UDP connect just picks the outbound interface
            ip = s.getsockname()[0]
        finally:
            s.close()
        import ipaddress

        if ipaddress.ip_address(ip).is_private:
            return ip
    except OSError:
        pass
    return None


def find_apk(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise SystemExit(f"APK not found: {p}")
        return p
    candidates = sorted((ROOT / "dist").glob("*.apk"))
    if not candidates:
        raise SystemExit(
            "No APK in dist/. Download sidemdm.apk from the project's Releases page into dist/, "
            "or build one (see docs/release.md) and pass --apk."
        )
    if len(candidates) > 1:
        raise SystemExit(f"Multiple APKs in dist/ ({[c.name for c in candidates]}); pass --apk to choose one.")
    return candidates[0]


class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        if str(path).endswith(".apk"):
            return APK_MIME
        return super().guess_type(path)

    def log_message(self, fmt, *args):  # quiet, no client identifiers
        sys.stderr.write(f"  {self.command} {self.path} -> {args[1]}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ip", help="this computer's LAN IP (auto-detected if omitted)")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--apk", help="path to the signed APK (default: the one in dist/)")
    ap.add_argument("--component", default=g.DEFAULT_COMPONENT)
    a = ap.parse_args(argv)

    ip = a.ip or detect_lan_ip()
    if not ip:
        return _fail("Could not detect a LAN IP. Pass --ip <your 192.168.x.x address> (run `ipconfig`/`ip addr`).")

    apk = find_apk(a.apk)
    version = _version_from_name(apk.name)
    host = f"{ip}:{a.port}"
    url = f"http://{host}/releases/dpc-{version}.apk"
    try:
        g.validate_lan_http_url(url)
    except g.ConfigError as e:
        return _fail(str(e))

    # Build the release into the served site, and get the QR text.
    site = ROOT / "server" / "site"
    out = ROOT / f"release-{version}-{ip}-{a.port}"
    rc = g.main([
        "--apk", str(apk), "--version", version, "--host", host, "--lan-http",
        "--component", a.component, "--out", str(out), "--site", str(site),
    ])
    if rc != 0:
        return rc

    import segno

    with (out / "enrollment.json").open() as f:
        qr_text = _compact(f.read())
    qr = segno.make(qr_text, error="m")

    print("\n" + "=" * 64)
    print("  Scan this QR on a factory-reset phone's welcome screen")
    print("  (tap the screen 6 times first to open the scanner):")
    print("=" * 64 + "\n")
    qr.terminal(compact=True)
    print(f"\n  Serving the app at  http://{host}/")
    print(f"  Download URL:       {url}")
    print(f"  QR image:           {out / 'enrollment.png'}")
    print("\n  After enrollment, open the app in the Work tab and tap Remove Work Profile")
    print("  to end up with a clean, unmanaged phone. Press Ctrl+C here when done.\n")

    handler = functools.partial(Handler, directory=str(site))
    try:
        httpd = http.server.ThreadingHTTPServer((ip, a.port), handler)
    except OSError as e:
        return _fail(f"Could not bind {host}: {e}. Is the port free, and is {ip} this machine's address?")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


def _version_from_name(name: str) -> str:
    import re

    m = re.search(r"(\d+\.\d+\.\d+)", name)
    return m.group(1) if m else "1.0.0"


def _compact(canonical_json: str) -> str:
    import json

    return json.dumps(json.loads(canonical_json), separators=(",", ":"), sort_keys=True)


def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
