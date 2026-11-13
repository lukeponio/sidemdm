#!/usr/bin/env python3
"""Build the immutable release folder and Setup Wizard provisioning QR for the DPC (spec 5.4, 5.5).

Usage (typical):
  python tools/generate_qr.py \
      --apk android/app/build/outputs/apk/release/app-release.apk \
      --version 1.0.0 --host enroll.devices.example.com \
      --site server/site --verify

Outputs release-<version>/ with dpc-<version>.apk, enrollment.json, enrollment.png,
sha256.txt and manifest.json, and (with --site) publishes the APK and QR into the static site.
--verify downloads the URL over LAN with normal TLS validation and no redirects, and refuses
to finish unless the served bytes hash to the checksum in the QR.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import http.client
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

# Use the vendored segno (no pip install needed); fall back to an installed one.
_VENDOR = str(Path(__file__).resolve().parent / "_vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

DEFAULT_COMPONENT = "com.example.personalprofile/.AdminReceiver"
APK_MIME = "application/vnd.android.package-archive"
EXTRA = "android.app.extra."


class ConfigError(ValueError):
    pass


def apk_checksum(data: bytes) -> str:
    """URL-safe Base64 of the raw SHA-256 digest, no padding (spec 5.4)."""
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")


def validate_version(version: str) -> str:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ConfigError(f"version must look like 1.0.0, got {version!r}")
    return version


def validate_component(component: str) -> str:
    if not re.fullmatch(r"[A-Za-z][\w.]*/\.?[A-Za-z][\w.$]*", component):
        raise ConfigError(f"component name {component!r} is not package/.Class form")
    return component


def validate_lan_url(url: str) -> str:
    """Reject non-HTTPS, credentials, IP-literal and mDNS hosts, and hosts that resolve publicly (FR-14)."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise ConfigError("download URL must use https://")
    if not parts.hostname:
        raise ConfigError("download URL has no hostname")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ConfigError("download URL must not contain credentials, query or fragment")
    if not parts.path.endswith(".apk"):
        raise ConfigError("download URL must point at a versioned .apk file")
    host = parts.hostname.lower()
    try:
        ipaddress.ip_address(host)
        is_ip = True
    except ValueError:
        is_ip = False
    if is_ip:
        raise ConfigError(
            "use a DNS hostname covered by an Android-trusted certificate, not an IP literal (spec 3.1)"
        )
    if host.endswith(".local") or "." not in host:
        raise ConfigError("Setup Wizard cannot be assumed to resolve mDNS/.local or single-label names")
    return url


def validate_lan_http_url(url: str) -> str:
    """Self-contained LAN mode: plain HTTP to a private IP literal, no domain or certificate.
    Integrity still rests on the SHA-256 package checksum in the QR; the network path is not encrypted."""
    parts = urlsplit(url)
    if parts.scheme != "http":
        raise ConfigError("LAN HTTP mode URL must use http://")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ConfigError("download URL must not contain credentials, query or fragment")
    if not parts.path.endswith(".apk"):
        raise ConfigError("download URL must point at a versioned .apk file")
    try:
        ip = ipaddress.ip_address(parts.hostname or "")
    except ValueError:
        raise ConfigError("LAN HTTP mode needs the server's private IP address, e.g. 192.168.1.50") from None
    if not ip.is_private or ip.is_loopback or ip.is_link_local:
        raise ConfigError(f"{ip} is not a private LAN address")
    return url


def check_resolves_to_lan(host: str) -> list[str]:
    """When the host resolves from this machine, every address must be private (RFC1918/ULA)."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise ConfigError(f"{host} does not resolve from this machine: {e}") from e
    addrs = sorted({i[4][0] for i in infos})
    public = [a for a in addrs if not ipaddress.ip_address(a).is_private]
    if public:
        raise ConfigError(f"{host} resolves to non-LAN address(es) {public}; LAN DNS must point at the server")
    return addrs


def fetch_hosted_apk(url: str, timeout: float = 30.0) -> bytes:
    """GET with standard TLS validation; any redirect or non-200 is an error (LAN-03)."""
    parts = urlsplit(url)
    host = parts.hostname
    check_resolves_to_lan(host)
    if parts.scheme == "http":
        conn = http.client.HTTPConnection(host, parts.port or 80, timeout=timeout)
    else:
        conn = http.client.HTTPSConnection(host, parts.port or 443, timeout=timeout,
                                           context=ssl.create_default_context())
    try:
        conn.request("GET", parts.path, headers={"User-Agent": "dpc-release-check"})
        resp = conn.getresponse()
        if 300 <= resp.status < 400:
            raise ConfigError(f"server redirected ({resp.status} -> {resp.getheader('Location')}); redirects are not allowed")
        if resp.status != 200:
            raise ConfigError(f"server returned HTTP {resp.status} for {url}")
        ctype = (resp.getheader("Content-Type") or "").split(";")[0].strip()
        if ctype != APK_MIME:
            raise ConfigError(f"server sent Content-Type {ctype!r}, expected {APK_MIME}")
        return resp.read()
    finally:
        conn.close()


def signer_cert_sha256(apk: Path, apksigner: str) -> list[str]:
    out = subprocess.run([apksigner, "verify", "--print-certs", str(apk)],
                         check=True, capture_output=True, text=True).stdout
    return [m.lower() for m in re.findall(r"certificate SHA-256 digest: ([0-9a-fA-F]{64})", out)]


def build_payload(component: str, url: str, checksum: str,
                  wifi_ssid: str | None = None, wifi_security: str | None = None,
                  wifi_password: str | None = None) -> dict:
    if not checksum:
        raise ConfigError("empty checksum")
    payload = {
        EXTRA + "PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": validate_component(component),
        EXTRA + "PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION":
            validate_lan_http_url(url) if url.startswith("http://") else validate_lan_url(url),
        EXTRA + "PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": checksum,
    }
    if wifi_ssid:
        payload[EXTRA + "PROVISIONING_WIFI_SSID"] = wifi_ssid
        payload[EXTRA + "PROVISIONING_WIFI_SECURITY_TYPE"] = wifi_security or "WPA"
        if wifi_password:
            payload[EXTRA + "PROVISIONING_WIFI_PASSWORD"] = wifi_password
    # Never PROVISIONING_USE_MOBILE_DATA in a strict-offline payload (spec 5.4).
    return payload


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_qr_png(text: str, path: Path) -> None:
    import segno  # imported lazily so validation tests run without it

    segno.make(text, error="m", micro=False).save(str(path), scale=8, border=4)


def publish_immutable(src: Path, dest: Path) -> None:
    """Copy, refusing to overwrite an existing file with different bytes (spec 5.5)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.read_bytes() != src.read_bytes():
            raise ConfigError(f"{dest} already exists with different bytes; bump the version instead")
        return
    shutil.copyfile(src, dest)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--apk", required=True, type=Path, help="signed release APK")
    p.add_argument("--version", required=True)
    p.add_argument("--host", required=True,
                   help="LAN hostname (HTTPS mode) or the server's private IP (--lan-http mode)")
    p.add_argument("--lan-http", action="store_true",
                   help="self-contained mode: http://<private IP>, no domain or certificate needed")
    p.add_argument("--component", default=DEFAULT_COMPONENT)
    p.add_argument("--out", type=Path, default=None, help="release folder (default release-<version>)")
    p.add_argument("--site", type=Path, help="static site root to publish into (server/site)")
    p.add_argument("--verify", action="store_true",
                   help="download the hosted APK over the LAN and require an exact checksum match")
    p.add_argument("--pin-cert-sha256", help="expected signing certificate SHA-256 (hex); needs apksigner")
    p.add_argument("--apksigner", default=shutil.which("apksigner") or "apksigner")
    p.add_argument("--wifi-ssid")
    p.add_argument("--wifi-security", choices=["WPA", "WEP", "NONE", "SAE"], default=None)
    p.add_argument("--wifi-password", help="TEST-ONLY password; it is visible to anyone who sees the QR")
    a = p.parse_args(argv)

    try:
        version = validate_version(a.version)
        if not a.apk.is_file():
            raise ConfigError(f"APK not found: {a.apk}")
        apk_bytes = a.apk.read_bytes()
        if apk_bytes[:2] != b"PK":
            raise ConfigError(f"{a.apk} is not an APK (zip) file")
        scheme = "http" if a.lan_http else "https"
        url = f"{scheme}://{a.host}/releases/dpc-{version}.apk"
        url = validate_lan_http_url(url) if a.lan_http else validate_lan_url(url)

        if a.pin_cert_sha256:
            certs = signer_cert_sha256(a.apk, a.apksigner)
            if a.pin_cert_sha256.lower().replace(":", "") not in certs:
                raise ConfigError(f"APK signer {certs} does not match pinned certificate")

        checksum = apk_checksum(apk_bytes)
        payload = build_payload(a.component, url, checksum, a.wifi_ssid, a.wifi_security, a.wifi_password)
        if a.wifi_password:
            print("WARNING: Wi-Fi password is embedded in the QR; use a test-only network.", file=sys.stderr)

        out = a.out or Path(f"release-{version}")
        out.mkdir(parents=True, exist_ok=True)
        apk_out = out / f"dpc-{version}.apk"
        publish_immutable(a.apk, apk_out)
        text = canonical_json(payload)
        # Compact JSON keeps the QR at a lower density, which scans more reliably.
        qr_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        (out / "enrollment.json").write_text(text)
        write_qr_png(qr_text, out / "enrollment.png")
        hexdigest = hashlib.sha256(apk_bytes).hexdigest()
        (out / "sha256.txt").write_text(f"{hexdigest}  dpc-{version}.apk\n")
        manifest = {
            "app_version": version,
            "component": a.component,
            "hostname": a.host,
            "download_url": url,
            "sha256_hex": hexdigest,
            "package_checksum_b64url": checksum,
            "apk_bytes": len(apk_bytes),
            "wifi_extras": bool(a.wifi_ssid),
            "generated_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

        if a.site:
            publish_immutable(apk_out, a.site / "releases" / f"dpc-{version}.apk")
            shutil.copyfile(out / "enrollment.png", a.site / "enroll.png")
            (a.site / "release.json").write_text(json.dumps(
                {"version": version, "url": url, "sha256_hex": hexdigest}, indent=2) + "\n")

        if a.verify:
            served = fetch_hosted_apk(url)
            if apk_checksum(served) != checksum:
                raise ConfigError("hosted APK checksum does not match the QR payload; do not use this QR")
            print(f"Verified: {url} serves the exact APK ({len(served)} bytes).")
        else:
            print("Not verified against the live server yet. Re-run with --verify once the LAN server is up.")
    except (ConfigError, subprocess.CalledProcessError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Release written to {out}/  checksum={checksum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
