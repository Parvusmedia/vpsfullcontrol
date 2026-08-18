#!/usr/bin/env bash
# Idempotent deploy onto the Parvus VPS. Does not restart unrelated services.
#
# TLS: never `certbot --nginx` (it mutates this vhost and the next rsync
# overwrites it). Issue/renew with webroot, then write our own 443 server
# block whenever /etc/letsencrypt/live/$DOMAIN/fullchain.pem exists.
set -euo pipefail

ROOT=""
if [[ $# -ge 1 && -d "$1" ]]; then
  ROOT="$(cd "$1" && pwd)"
elif [[ "$(basename "$(cd "$(dirname "$0")" && pwd)")" == "scripts" ]]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
else
  echo "Usage: $0 /path/to/live-fare-demo" >&2
  exit 1
fi
DEST="/opt/apps/live-fare-demo"
DOMAIN="${LIVE_FARE_DOMAIN:-flights.pmediaplus.com}"
VPS_IP="${VPS_IP:-87.106.194.137}"
SITE_AVAIL="/etc/nginx/sites-available/live-fare-demo"
SITE_EN="/etc/nginx/sites-enabled/live-fare-demo"
SNIPPET="/etc/nginx/snippets/live-fare-locations.conf"
CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-running with sudo"
  exec sudo --preserve-env=LIVE_FARE_DOMAIN,VPS_IP "$0" "$@"
fi

write_ssl_site() {
  local ssl_extra=""
  if [[ -f /etc/letsencrypt/options-ssl-nginx.conf ]]; then
    ssl_extra="${ssl_extra}
    include /etc/letsencrypt/options-ssl-nginx.conf;"
  else
    ssl_extra="${ssl_extra}
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;"
  fi
  if [[ -f /etc/letsencrypt/ssl-dhparams.pem ]]; then
    ssl_extra="${ssl_extra}
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;"
  fi

  cat >"$SITE_AVAIL" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name ${DOMAIN};

    ssl_certificate ${CERT};
    ssl_certificate_key ${KEY};
${ssl_extra}

    include ${SNIPPET};
}
EOF
}

install_nginx_site() {
  install -D -m 644 "$DEST/deploy/nginx-live-fare-locations.conf" "$SNIPPET"
  if [[ -f "$CERT" && -f "$KEY" ]]; then
    write_ssl_site
    echo "nginx site: HTTPS (${DOMAIN})"
  else
    install -m 644 "$DEST/deploy/nginx-live-fare-demo.conf" "$SITE_AVAIL"
    echo "nginx site: HTTP only (no cert yet)"
  fi
  ln -sfn "$SITE_AVAIL" "$SITE_EN"
}

local_curl() {
  # Real hostname so SNI + Host match the vhost (https://127.0.0.1 hits default_server).
  if [[ -f "$CERT" && -f "$KEY" ]]; then
    curl -fsSk --max-time 15 --resolve "${DOMAIN}:443:127.0.0.1" "$@"
  else
    curl -fsS --max-time 15 --resolve "${DOMAIN}:80:127.0.0.1" "$@"
  fi
}

local_base() {
  if [[ -f "$CERT" && -f "$KEY" ]]; then
    echo "https://${DOMAIN}"
  else
    echo "http://${DOMAIN}"
  fi
}

echo "=== deploy live-fare-demo → $DEST ($DOMAIN) ==="
mkdir -p "$DEST" /var/www/html
if [[ ! -f "$DEST/.env" ]]; then
  cp "$ROOT/.env.example" "$DEST/.env"
fi

rsync -a \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  "$ROOT/" "$DEST/"

chown -R cursorbot:cursorbot "$DEST"
chmod 755 "$DEST/scripts/"*.sh "$DEST/feed/updater/update.py"

install -m 644 "$DEST/deploy/live-fare-updater.service" /etc/systemd/system/live-fare-updater.service
install -m 644 "$DEST/deploy/live-fare-updater.timer" /etc/systemd/system/live-fare-updater.timer

# First feed publish (atomic) before nginx reload.
sudo -u cursorbot /usr/bin/python3 "$DEST/feed/updater/update.py" --once

install_nginx_site
nginx -t
systemctl reload nginx

systemctl daemon-reload
systemctl enable live-fare-updater.timer
systemctl start live-fare-updater.timer
systemctl start live-fare-updater.service || true

resolved="$(dig +short "$DOMAIN" A 2>/dev/null | tail -n1 || true)"
echo "DNS $DOMAIN -> ${resolved:-none} (want $VPS_IP)"
if [[ "$resolved" == "$VPS_IP" ]]; then
  # Webroot only: keep our CORS / TTL / locations intact.
  certbot certonly \
    --webroot \
    -w /var/www/html \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    --keep-until-expiring
  install_nginx_site
  nginx -t
  systemctl reload nginx
  echo "TLS OK"
else
  echo "SKIP certbot: create DNS A record $DOMAIN → $VPS_IP then re-run this script."
fi

echo "=== local smoke (SNI $DOMAIN → 127.0.0.1) ==="
SMOKE_JSON="$(mktemp)"
local_curl -o "$SMOKE_JSON" "$(local_base)/fares/network.json"
python3 - "$SMOKE_JSON" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
n = len(data["fares"])
assert n >= 200, n
print("smoke fares", n, "updated", data.get("updated_at"))
PY
rm -f "$SMOKE_JSON"
local_curl "$(local_base)/health"
echo

echo "DEPLOY_OK"

echo "=== integration tests ==="
bash "$DEST/scripts/vps-integration-tests.sh" "$DEST"
