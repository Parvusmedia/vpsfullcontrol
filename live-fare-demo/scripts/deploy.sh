#!/usr/bin/env bash
# Idempotent deploy onto the Parvus VPS. Does not restart unrelated services.
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

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-running with sudo"
  exec sudo --preserve-env=LIVE_FARE_DOMAIN,VPS_IP "$0" "$@"
fi

echo "=== deploy live-fare-demo → $DEST ($DOMAIN) ==="
mkdir -p "$DEST"
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
install -m 644 "$DEST/deploy/nginx-live-fare-demo.conf" "$SITE_AVAIL"
ln -sfn "$SITE_AVAIL" "$SITE_EN"

# First feed publish (atomic) before nginx reload.
sudo -u cursorbot /usr/bin/python3 "$DEST/feed/updater/update.py" --once

nginx -t
systemctl reload nginx

systemctl daemon-reload
systemctl enable live-fare-updater.timer
systemctl start live-fare-updater.timer
systemctl start live-fare-updater.service || true

echo "=== local smoke (Host: $DOMAIN) ==="
SMOKE_BASE="http://127.0.0.1"
SMOKE_OPTS=(-fsS -H "Host: $DOMAIN")
if curl -skI -H "Host: $DOMAIN" --max-time 5 "https://127.0.0.1/health" | grep -qi "200 OK"; then
  SMOKE_BASE="https://127.0.0.1"
  SMOKE_OPTS=(-fsSk -H "Host: $DOMAIN")
fi
curl "${SMOKE_OPTS[@]}" "$SMOKE_BASE/fares/network.json" | head -c 200
echo
curl "${SMOKE_OPTS[@]}" "$SMOKE_BASE/health"
echo

resolved="$(dig +short "$DOMAIN" A 2>/dev/null | tail -n1 || true)"
echo "DNS $DOMAIN -> ${resolved:-none} (want $VPS_IP)"
if [[ "$resolved" == "$VPS_IP" ]]; then
  certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    --redirect \
    --keep-until-expiring
  nginx -t
  systemctl reload nginx
  echo "TLS OK"
else
  echo "SKIP certbot: create DNS A record $DOMAIN → $VPS_IP then re-run this script."
fi

echo "DEPLOY_OK"

echo "=== integration tests ==="
bash "$DEST/scripts/vps-integration-tests.sh" "$DEST"
