# Agent guide

For AI coding agents (Claude Code, Codex, Grok, and others) driving sidemdm for a user.
You can perform every computer-side step; the phone steps are physical and must be done by the user.

## You can do (on the user's computer)

1. Verify `python3` is 3.10+. No pip installs needed — the QR library (segno) is vendored in `tools/_vendor/`.
2. Ensure a signed APK is in `dist/`. If none, fetch it from Releases:
   `gh release download --repo lukeponio/sidemdm --pattern '*.apk' --dir dist`
   (No release yet? Build it per README "Build it yourself": JDK 17 + Android SDK 36.)
3. Find the computer's LAN IP on the phone's network (`ipconfig` / `ip addr`), a `192.168.x.x`/`10.x.x.x`.
4. Start the server as a visible long-running process:
   `python sidemdm.py --ip <IP> [--port 8080]`  (choose a free port; 80 is often taken by IIS/Apache).
   It prints a scannable QR and serves the APK until Ctrl+C.
5. Have the user open `http://<IP>:<port>/` on the phone to confirm reachability. If it fails, it is almost
   always the computer firewall — tell them to allow inbound TCP on that port for the private network.

## The user must do (you cannot)

Back up + factory-reset the phone; tap the welcome screen six times; scan the QR you showed; join the same
Wi-Fi when it asks; accept the work-profile setup; then open the app in the **Work** tab and tap **Remove Work Profile**.
Lay these out step by step and wait for the user between them.

## Optional read-only check (ask first; it's their device)

With the phone on USB and USB debugging on:
`adb shell pm list users` and `adb shell dumpsys device_policy` confirm the work profile exists, and after
removal that no profile/device owner remains. Never install, wipe, clear data, or run `dpm`/set-owner.

## Never

Weaken TLS, switch the app to device-owner mode, or bypass "App blocked to protect your device". If that
message appears, this method cannot work on that phone — say so.
