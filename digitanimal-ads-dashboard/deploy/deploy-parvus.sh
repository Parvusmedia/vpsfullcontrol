#!/usr/bin/env bash
# Deploy digitanimal-ads-dashboard to parvus-vps → digitanimal.pmediaplus.com
set -euo pipefail

REMOTE="${REMOTE:-parvus-vps}"
REMOTE_DIR="/opt/apps/digitanimal-ads-dashboard"
PRIVATE_DIR="/opt/apps/private/digitanimal"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Ensure remote paths"
ssh "$REMOTE" "mkdir -p '$REMOTE_DIR' '$PRIVATE_DIR'"

if [[ -n "${WINDSOR_API_KEY:-}" ]]; then
  echo "==> Sync Windsor env on VPS (not printing key)"
  ssh "$REMOTE" "umask 077 && printf '%s\n' 'WINDSOR_API_KEY=${WINDSOR_API_KEY}' > '$PRIVATE_DIR/windsor.env'"
else
  echo "==> WINDSOR_API_KEY not set locally; leaving existing $PRIVATE_DIR/windsor.env if any"
fi

echo "==> Upload app sources (tar)"
tar -C "$ROOT" \
  --exclude=node_modules \
  --exclude=dist \
  --exclude=.next \
  --exclude=public/dashboard.json \
  -czf - . | ssh "$REMOTE" "tar -xzf - -C '$REMOTE_DIR'"

echo "==> npm ci + build on VPS"
ssh "$REMOTE" "bash -lc '
  set -euo pipefail
  cd \"$REMOTE_DIR\"
  if [[ -f \"$PRIVATE_DIR/windsor.env\" ]]; then set -a; source \"$PRIVATE_DIR/windsor.env\"; set +a; fi
  npm ci
  npm run build
'"

echo "==> systemd + nginx"
ssh "$REMOTE" "sudo cp '$REMOTE_DIR/deploy/digitanimal-ads.service' /etc/systemd/system/digitanimal-ads.service"
ssh "$REMOTE" "sudo cp '$REMOTE_DIR/deploy/nginx-digitanimal.conf' /etc/nginx/sites-available/digitanimal"
ssh "$REMOTE" "sudo ln -sf /etc/nginx/sites-available/digitanimal /etc/nginx/sites-enabled/digitanimal"
ssh "$REMOTE" "sudo systemctl daemon-reload && sudo systemctl enable --now digitanimal-ads.service"
ssh "$REMOTE" "sudo systemctl restart digitanimal-ads.service"
ssh "$REMOTE" "sudo nginx -t && sudo systemctl reload nginx"

echo "==> Optional TLS"
if ssh "$REMOTE" "sudo test -d /etc/letsencrypt/live/digitanimal.pmediaplus.com" 2>/dev/null; then
  echo "    cert already present for digitanimal.pmediaplus.com"
else
  echo "    run on VPS if DNS is ready: sudo certbot --nginx -d digitanimal.pmediaplus.com"
fi

echo "==> Done. Smoke: curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:3025/api/dashboard (on VPS)"
