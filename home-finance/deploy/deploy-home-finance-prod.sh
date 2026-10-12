#!/bin/bash
# Deploy Hogar Finanzas to home.pmediaplus.com (parvus-vps)
set -euo pipefail

REMOTE="${HOME_FINANCE_REMOTE:-parvus-vps}"
LOCAL="/workspace/home-finance/public"
# Ajusta si el vhost en producción usa otra ruta:
APP_ROOT="${HOME_FINANCE_APP_ROOT:-/opt/apps/home-finance}"
DOCROOT="${HOME_FINANCE_DOCROOT:-$APP_ROOT/public}"
PRIVATE="${HOME_FINANCE_PRIVATE:-/opt/apps/private/home-finance}"
ENV_FILE="$PRIVATE/app.env"

echo "==> Ensure private dir and env on $REMOTE"
ssh "$REMOTE" "install -d -m 700 $PRIVATE $PRIVATE/data && \
  if [ ! -f $ENV_FILE ]; then \
    echo 'HOME_FINANCE_API_TOKEN='\$(openssl rand -hex 32) >> $ENV_FILE; \
    echo 'HOME_FINANCE_DATA_DIR=$PRIVATE/data' >> $ENV_FILE; \
    chmod 600 $ENV_FILE; \
    echo 'Created $ENV_FILE — guarda el token para entrar en la app'; \
  fi"

echo "==> Rsync public files"
ssh "$REMOTE" "mkdir -p $DOCROOT"
rsync -avz --delete \
  --exclude '.git' \
  "$LOCAL/" "$REMOTE:$DOCROOT/"

echo "==> Set PHP env for vhost (si usas PHP-FPM, exporta HOME_FINANCE_ENV en el pool)"
echo "    HOME_FINANCE_ENV=$ENV_FILE"
echo "Done. Abre https://home.pmediaplus.com y usa HOME_FINANCE_API_TOKEN como clave."
