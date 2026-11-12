# Testing and evidence (spec 9)

## Automated checks (run on every build)

| Check | Command | Covers |
|---|---|---|
| DPC unit tests | `./gradlew :app:testDebugUnitTest` | AT-04 (only fully managed allowed → cancel), removal predicates (FR-12) |
| QR tool tests | `python -m unittest tools/test_generate_qr.py` | FR-14 URL rules, checksum format, immutability (AT-11 guard) |
| Live server check | `python tools/generate_qr.py ... --verify` | LAN-03, OFF-02, OFF-03, AT-11 against the real host |
| Safety grep | see [release.md](release.md) step 3 | FR-09, NFR-05 |

## P0 feasibility (do this first)

1. Capture device facts once ADB is available (redact before sharing):
   ```bash
   adb shell getprop ro.product.model; adb shell getprop ro.build.fingerprint
   adb shell getprop ro.build.version.release; adb shell getprop ro.build.version.sdk
   adb shell pm list users; adb shell dumpsys device_policy
   ```
2. OFF-01 / AT-01 / MT-02: cold reset, no WAN, no cellular, six taps. Scanner opens offline? Record exactly what appears.
3. AT-02 / MT-03 / OFF-06: scan the release QR. Allowlist accepts the APK, or "App blocked"?
4. AT-03 / MT-04: work profile mode offered and completed.

Any failure in 2–4 is a NO-GO for the architecture. Model B/C diagnostic runs must be labelled
noncompliant and never replace OFF-01.

## Device test report

Copy this table into `release-<version>/test-report.md` and fill it in.

| Test | Result (PASS/FAIL/NOT RUN) | Notes / evidence file |
|---|---|---|
| Device: model, build fingerprint, patch, carrier, date | | |
| OFF-01 cold offline scanner | | |
| OFF-02 LAN DNS only | | |
| OFF-03 APK 200 + checksum | | |
| OFF-04 no internet traffic needed (capture) | | |
| OFF-05 TLS/time with no WAN | | |
| OFF-06 unapproved DPC behaviour | | |
| OFF-07 COPE, not Device Owner | | |
| OFF-08 removal with server off, no network | | |
| OFF-09 not reachable from WAN | | |
| OFF-10 prewarmed diagnostic (noncompliant) | | |
| AT-01 … AT-12 | | |
| MT-01 … MT-07 | | |

### Work profile checks

- AT-05: open the work-badged "Work Profile" app: Role WORK PROFILE OWNER, State Active.
- AT-06: open the personal copy (if visible): Role NOT MANAGED, no Remove button.
- AT-07/08: create a test file + app in each profile; add a personal account.
- AT-09/10, MT-06: server off, Wi-Fi off, Remove Work Profile → Continue → Remove Work Profile.
  Work profile gone; personal baseline intact; no Setup Wizard restart.
  `adb shell pm list users` shows only user 0; `dumpsys device_policy` shows no profile owner.
- AT-12: stop the server mid-provisioning; setup fails safely, no reset from the DPC.
- MT-07: reboot and after the next security update, recheck no ownership remnants.
