# sidemdm

**Sideload a work profile onto your own Android phone from your own computer, then remove it — no cloud, no account, no company.**

sidemdm turns the phone's built-in "six-tap QR" enterprise setup into something you run entirely on your own LAN. You scan a QR shown by your computer, the phone creates a work profile owned by this app, and then you tap **Remove Work Profile**. You end up with an ordinary, unmanaged phone whose personal side was never touched.

It is three small things: a tiny Android app (the Device Policy Controller), a one-command launcher that serves it over your LAN and prints the QR, and a QR/release tool. There is no management server, no telemetry, and the app has no internet permission.

> **Status: works, but barely tested.** It has been run end to end on exactly one device — a **Motorola moto g power (2026)** on Android 16 — with the computer on the internet. Whether it works on other phones, and whether the fully offline case works, is **unproven**. See [Known limits](#known-limits). This is a personal-use tool for phones **you own**.

## Why

Android's QR enrollment is built for companies. If you just want a throwaway work profile — or you want to prove to yourself that a phone can be enrolled and then cleanly un-enrolled without a factory data loss on the personal side — there was no simple local way to do it. sidemdm is that local way.

## What you need

- A computer (Windows, macOS or Linux) on the same Wi-Fi/LAN as the phone.
- **Python 3.10+** and one package: `pip install -r tools/requirements.txt`.
- The signed `sidemdm.apk` — download it from the [Releases](../../releases) page into `dist/`.
- An Android phone you are willing to **factory reset** (enrollment starts from the first-run setup screen).

That's it. No Android SDK, no domain name, no HTTPS certificate.

## Use it (the short version)

```bash
pip install -r tools/requirements.txt
# put sidemdm.apk in dist/ (from the Releases page)
python sidemdm.py
```

`sidemdm.py` detects your computer's LAN IP, serves the APK, and prints a QR right in the terminal. Then, on the phone:

1. **Back up the phone, then factory reset it.** (Enrollment only works from the first-run setup.)
2. On the welcome screen, **tap the screen six times** to open the QR scanner.
3. If asked, join the **same Wi-Fi** as your computer, then **scan the QR** in your terminal.
4. Accept the work-profile setup and finish. A **Work** tab appears in your app drawer.
5. Open the **Work Profile** app in that tab and tap **Remove Work Profile** (two confirmations). The work profile is deleted; your personal profile stays.

Press **Ctrl+C** in the terminal to stop the server. It isn't needed after the APK downloads, and removal needs no network at all.

If auto-detection picks the wrong address, pass it yourself:

```bash
python sidemdm.py --ip 192.168.0.22 --port 8080
```

## How it stays safe

- The app can **only** create a work profile (`PROVISIONING_MODE_MANAGED_PROFILE`). It refuses and cancels if the phone offers only full-device mode — it never becomes a device owner.
- The only destructive action is **Remove Work Profile**, which calls `wipeData` on the work profile alone, after re-checking it really owns a managed profile, behind two confirmations. It never calls a device-wide wipe.
- The QR pins the APK by **SHA-256**, so a tampered or wrong file is rejected even over plain HTTP.
- The app requests **no internet permission** and phones home to nothing.

## Build it yourself

Prefer not to trust a prebuilt binary? Build and sign your own APK, then drop it in `dist/`:

```bash
./gradlew :app:testDebugUnitTest :app:assembleRelease   # Windows: gradlew.bat ...
cp app/build/outputs/apk/release/app-release.apk dist/sidemdm-1.0.1.apk
```

Signing is read from `keystore.properties` or environment variables — see [docs/release.md](docs/release.md). Requires JDK 17 and Android SDK Platform 36.

## Known limits

- **One device, one condition.** Verified only on a moto g power (2026), Android 16, with the computer online. Other OEMs and the no-internet case are untested. Your phone's setup wizard may behave differently.
- **Plain HTTP.** The default mode serves the APK over HTTP on your LAN (the SHA-256 pin is what guarantees integrity). Some firmware may refuse an HTTP provisioning download. An HTTPS mode exists for that case — see [docs/offline-lan-setup.md](docs/offline-lan-setup.md) — but it needs a hostname and certificate.
- **Approved-DPC allowlist.** Google only permits approved enterprise DPCs during enrollment on some devices/firmware. If your phone shows "App blocked to protect your device," this method won't work on it, and there is no bypass.
- **Factory reset required.** The six-tap flow only starts from first-run setup. Back up anything important first.
- **No warranty.** See [LICENSE](LICENSE). Use on phones you own and data you've backed up.

## Repository layout

| Path | What it is |
|---|---|
| `sidemdm.py`, `run.sh`, `run.bat` | The launcher: detect IP, build QR, serve the APK. |
| `app/` | The Android Device Policy Controller (Kotlin). |
| `tools/generate_qr.py` | QR + immutable release builder, with a LAN-safety check. |
| `server/` | Optional Docker/nginx server (plain-HTTP and HTTPS configs). |
| `docs/` | [Offline LAN setup](docs/offline-lan-setup.md), [release](docs/release.md), [testing](docs/testing.md). |
| `dist/` | Where the prebuilt `sidemdm.apk` goes. |

## License

[MIT](LICENSE).
