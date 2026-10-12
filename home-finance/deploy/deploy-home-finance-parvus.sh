#!/bin/bash
# Sincroniza Hogar Finanzas a parvus-vps (/opt/apps/home-finance)
set -euo pipefail

REMOTE="${HOME_FINANCE_REMOTE:-parvus-vps}"
APP_ROOT="/opt/apps/home-finance"
PRIVATE="/opt/apps/private/home-finance"
LOCAL="/workspace/home-finance"

echo "==> Private data + token"
ssh "$REMOTE" "install -d -m 700 $PRIVATE $PRIVATE/data && \
  if [ ! -f $PRIVATE/app.env ]; then \
    umask 077; \
    { echo HOME_FINANCE_API_TOKEN=\$(openssl rand -hex 32); echo HOME_FINANCE_DATA_DIR=$PRIVATE/data; } > $PRIVATE/app.env; \
    echo 'Nuevo token en $PRIVATE/app.env'; \
  fi"

echo "==> Sync application"
ssh "$REMOTE" "mkdir -p $APP_ROOT/public"
if command -v rsync >/dev/null 2>&1; then
  rsync -avz --delete \
    --exclude '.git' \
    --exclude 'private' \
    "$LOCAL/public/" "$REMOTE:$APP_ROOT/public/"
else
  tar -C "$LOCAL/public" -cf - . | ssh "$REMOTE" "tar -C $APP_ROOT/public -xf -"
fi

echo "==> Sync Python API"
ssh "$REMOTE" "mkdir -p $APP_ROOT/server"
tar -C "$LOCAL/server" -cf - . | ssh "$REMOTE" "tar -C $APP_ROOT/server -xf -"
ssh "$REMOTE" "chmod +x $APP_ROOT/server/home_finance_api.py"

echo "==> Systemd unit"
tar -C "$LOCAL/deploy" -cf - home-finance-api.service | ssh "$REMOTE" "tar -C /tmp -xf - && sudo mv /tmp/home-finance-api.service /etc/systemd/system/home-finance-api.service && sudo systemctl daemon-reload && sudo systemctl enable --now home-finance-api.service" 2>/dev/null || echo "    (instala el servicio manualmente desde deploy/home-finance-api.service)"

echo "==> Nginx (manual si aún no existe el vhost)"
echo "    Copia deploy/nginx-home-finance.conf al servidor y recarga nginx."
echo "    DNS: A/AAAA de home.pmediaplus.com → este VPS."
echo "Done."
