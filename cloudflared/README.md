# Cloudflare Tunnel Setup for Self-Hosted Services

Securely expose local services (like Flask apps, dashboards, etc.) using Cloudflare Tunnel.

## Requirements

- A domain on [Cloudflare](https://dash.cloudflare.com)
- A running self-hosted app (e.g. on localhost:5000)
- A Linux server with `systemd`

## 1. Install Cloudflared

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
cloudflared version
```

## 2. Authenticate CloudFlare
This opens a browser to authorize Cloudflared with your Cloudflare account.


```bash
cloudflared tunnel login
```

This creates a certificate file and a credentials json file for your tunnel. Specifically, it stores the private key and other details that Cloudflare uses to authenticate and authorize your tunnel. This file is critical for the tunnel's operation because it ensures that only your Cloudflare account can manage the tunnel.
```bash
ls ~/.cloudflared/
cert.pem  <SOME HASH>.json

------------ for convenience
cp <SOME HASH>.json raspberrypi-tunnel.json
```

## 3. Create config file
Edit /etc/cloudflared/config.yml. NOTE - use correct home path and do NOT use `~/.`, as we are running it later from systemD.

```yaml
tunnel: raspberrypi-tunnel
credentials-file: /home/mnalavadi/.cloudflared/raspberrypi-tunnel.json

ingress:
  - hostname: app1.mnalavadi.org
    service: http://localhost:5000
  - hostname: app2.mnalavadi.org
    service: http://localhost:6000
  - service: http_status:404

```

4. Add a DNS record for each hostname:

```bash
cloudflared tunnel route dns raspberrypi-tunnel app1.mnalavadi.org
cloudflared tunnel route dns raspberrypi-tunnel app2.mnalavadi.org
```

5. Install and enable systemd service

```bash
sudo cloudflared --config /etc/cloudflared/config.yml service install
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl restart cloudflared
sudo systemctl enable cloudflared

systemctl status cloudflared
journalctl -u cloudflared -f
```

## Add a New Hostname to Your Cloudflare Tunnel

To add a new hostname (subdomain) to your Cloudflare tunnel:

1. Update the Cloudflare Tunnel Configuration and add new hostname entry.
```bash
sudo nano /etc/cloudflared/config.yml
```

```
...
ingress:
  - hostname: newapp.example.com
    service: http://localhost:5001
  - service: http_status:404
```

2. Update DNS Records in Cloudflare
```
cloudflared tunnel route dns raspberrypi-tunnel newapp.mnalavadi.org
```

3. Restart SystemD Cloudflare Tunnel service:
```
sudo systemctl restart cloudflared
```

---
Notes
- Use cloudflared tunnel list to see registered tunnels
- Use cloudflared tunnel delete <name> to remove one
- Logs: journalctl -u cloudflared -f

