# Release procedure (spec 5.5, FR-15, NFR-09)

## One-time: release keystore

Keep this key forever and back it up offline. A different key means a different signer and a new
enrollment for any future update.

```bash
keytool -genkeypair -v -keystore ~/keys/personal-dpc.jks -alias dpc \
  -keyalg RSA -keysize 4096 -validity 10000
```

Create `keystore.properties` in the repo root (git-ignored):

```properties
storeFile=/home/you/keys/personal-dpc.jks
storePassword=...
keyAlias=dpc
keyPassword=...
```

Or set `DPC_KEYSTORE`, `DPC_KEYSTORE_PASSWORD`, `DPC_KEY_ALIAS`, `DPC_KEY_PASSWORD`.

Record the signer certificate SHA-256 once and pin it:

```bash
apksigner verify --print-certs android/app/build/outputs/apk/release/app-release.apk
```

## Each release

1. Bump `versionCode` and `versionName` in `android/app/build.gradle.kts`.
2. Build and test (from `android/`): `(cd android && ./gradlew :app:testDebugUnitTest :app:lintRelease :app:assembleRelease)`.
3. Safety grep (must print nothing):
   `grep -rnE "\.wipeDevice\(|getParentProfileInstance|clearProfileOwner\(|android.permission.INTERNET" android/app/src/main`
4. Generate and publish:
   ```bash
   python tools/generate_qr.py --apk android/app/build/outputs/apk/release/app-release.apk \
     --version 1.0.1 --host enroll.yourdomain.tld --site server/site \
     --pin-cert-sha256 <hex from apksigner>
   ```
   The tool refuses to overwrite an existing `dpc-<version>.apk` with different bytes. A new build
   always gets a new version, URL and QR.
5. With the server running, from another LAN client: rerun with `--verify`. It resolves the host
   (must be a private address), validates TLS normally, rejects redirects, checks the
   `application/vnd.android.package-archive` type and compares the hash of the served bytes with the QR.
6. Keep `release-<version>/` (APK, `enrollment.json`, `enrollment.png`, `sha256.txt`, `manifest.json`)
   with the test evidence.
