# Prebuilt APK goes here

Put the signed `sidemdm.apk` in this folder (the one attached to the project's
[Releases](../../releases) page). `sidemdm.py` serves whatever APK it finds here.

Building your own instead? See [docs/release.md](../docs/release.md), then copy your
`app-release.apk` here as `sidemdm-<version>.apk`. The QR pins the APK by SHA-256, so the
QR always matches the exact file you serve.
