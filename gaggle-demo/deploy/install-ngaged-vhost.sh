#!/usr/bin/env bash
# Install PHP (if missing), systemd unit, nginx vhost, optional TLS for ngaged.pmediaplus.com
set -euo pipefail

APP_ROOT="/opt/apps/gaggle-demo"
PRIVATE="/opt/apps/private/gaggle-demo"
DOMAIN="ngaged.pmediaplus.com"

if ! command -v php >/dev/null 2>&1; then
  echo "==> Installing php-cli + php-curl"
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y php-cli php-curl
fi

echo "==> Ensure secrets dir"
sudo install -d -m 700 -o cursorbot -g cursorbot "$PRIVATE/data"

if [[ ! -f "$PRIVATE/publora.env" ]]; then
  cp "$APP_ROOT/deploy/publora.env.example" "$PRIVATE/publora.env"
  chmod 600 "$PRIVATE/publora.env"
  echo "WARNING: Edit $PRIVATE/publora.env with real PUBLORA_API_KEY"
fi

echo "==> systemd gaggle-demo"
sudo cp "$APP_ROOT/deploy/gaggle-demo.service" /etc/systemd/system/gaggle-demo.service
sudo systemctl daemon-reload
sudo systemctl enable --now gaggle-demo.service

echo "==> nginx vhost"
sudo cp "$APP_ROOT/deploy/nginx-ngaged.pmediaplus.com.conf" \
  "/etc/nginx/sites-available/${DOMAIN}"
sudo ln -sf "/etc/nginx/sites-available/${DOMAIN}" "/etc/nginx/sites-enabled/${DOMAIN}"
sudo nginx -t
sudo systemctl reload nginx

if command -v certbot >/dev/null 2>&1; then
  echo "==> TLS (requires DNS ${DOMAIN} -> this server)"
  if sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m hello@parvusmedia.com --redirect 2>/dev/null; then
    echo "Certbot OK"
  else
    echo "Certbot skipped or failed — fix DNS A record then run:"
    echo "  sudo certbot --nginx -d ${DOMAIN}"
  fi
else
  echo "certbot not installed; site available on HTTP until SSL is configured."
fi

curl -fsS "http://127.0.0.1:8790/api/health" && echo
echo "Done. Public URL: https://${DOMAIN}/ (after DNS + cert)"
