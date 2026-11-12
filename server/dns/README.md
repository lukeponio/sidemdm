# LAN DNS (no public DNS at enrollment)

The phone must resolve the QR hostname to the server's private address using only the LAN.

Preferred: add a local A record on the router and let DHCP hand out the router as resolver.

| Router firmware | Where |
|---|---|
| OpenWrt / dnsmasq | `/etc/dnsmasq.conf`: `address=/enroll.yourdomain.tld/192.168.50.10` |
| pfSense / OPNsense | Services → DNS Resolver → Host Overrides |
| UniFi | Settings → Routing → DNS (local records) |
| Consumer routers | Look for "Local DNS", "DNS rewrite" or "Host mapping"; if missing, use the alternative below |

Alternative: run dnsmasq on the provisioning host and set the router's DHCP DNS option to that
host. Only use this when DHCP reliably advertises it.

Also:
- Give the server a DHCP reservation or static IP.
- Turn off guest mode / client isolation on the SSID the phone uses.
- Do not rely on `.local` (mDNS) names.

Check from another LAN client with WAN unplugged:
`nslookup enroll.yourdomain.tld` must return only the private address.
