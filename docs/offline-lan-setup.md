# Offline LAN setup and enrollment (spec 3.1, 6A)

## Topology

One Wi-Fi AP/router with DHCP, one provisioning host (laptop, Pi, or any always-on machine), the phone,
and a second screen to show the QR. WAN cable unplugged. Phone SIM/eSIM inactive.

## Prepare while online

1. Build and sign the APK and generate the release ([release.md](release.md)).
2. Get a publicly trusted certificate for your hostname by DNS-01 ([server/tls/README.md](../server/tls/README.md)).
3. `cd server && docker compose pull` so the nginx image is cached locally.
4. Set the hostname in `server/nginx.conf` `server_name`.

## Prepare the LAN

5. DHCP reservation for the host; local DNS A record for the hostname
   ([server/dns/README.md](../server/dns/README.md)); client isolation off; TCP 443 allowed.

## Start and prove isolation

6. `LAN_IP=<host private IP> docker compose up -d`, then `curl https://<host>/healthz` from another LAN client.
7. Unplug WAN. Check the QR page and `generate_qr.py ... --verify` still pass from another LAN client.
8. OFF-09: from outside the LAN (e.g. phone hotspot, no VPN) confirm the hostname does not reach the server.

## Enroll (Model A, the only compliant run)

9. Factory-reset the backed-up test phone. Boot with no SIM data and no WAN.
10. On the welcome screen tap six times. If it asks to download a QR reader or for internet, **stop:
    record Model A NO-GO** (do not connect WAN; see [testing.md](testing.md)).
11. Show `https://<host>/` on another device. Join the LAN Wi-Fi if prompted, scan, accept work profile setup.
12. If you see "App blocked to protect your device", record NO-GO (allowlist). Do not bypass Play Protect.

## Afterwards

The server can be shut down once the profile is created. Removal needs no network (LAN-07).

## Troubleshooting ladder

(a) scanner won't open: platform/Google component. (b) Wi-Fi won't join: AP/DHCP. (c) hostname fails:
LAN DNS. (d) HTTPS fails: certificate trust, name, or phone clock. (e) APK GET fails: firewall/path,
check `server/logs/access.log`. (f) checksum fails: regenerate from hosted bytes. (g) app blocked:
approved-DPC allowlist. (h) no work-profile option: Motorola/Android mode restriction, the DPC cancels by
design. (i) removal behaves unexpectedly: stop and keep evidence. Never weaken TLS or switch to Device Owner.
