# TLS certificate (prepared before going offline)

Setup Wizard must trust the chain without any CA being sideloaded (LAN-04). Use a publicly
trusted certificate for a hostname in a domain you control, issued while you are online.

1. Pick a hostname, e.g. `enroll.yourdomain.tld`. It never needs a public A record.
2. Issue a certificate with DNS-01 validation (no inbound port needed), for example:
   `certbot certonly --manual --preferred-challenges dns -d enroll.yourdomain.tld`
   or `lego`/`acme.sh` with your DNS provider's API.
3. Copy `fullchain.pem` and `privkey.pem` into this folder (`server/tls/`). Both are git-ignored.
   Restrict the key: `chmod 600 privkey.pem`.
4. Put the same hostname in `server/nginx.conf` (`server_name`) and pass it to `tools/generate_qr.py --host`.

Expiry: Let's Encrypt certificates last 90 days or less. Renew on a separate online
maintenance computer before expiry and copy the new files here; the server never runs ACME
itself. Check expiry with `openssl x509 -enddate -noout -in fullchain.pem`.

Never use `https://<ip>` with a self-signed certificate; Setup Wizard will not trust it.
