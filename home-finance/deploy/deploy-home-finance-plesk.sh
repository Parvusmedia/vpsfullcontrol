#!/bin/bash
# Despliega Hogar Finanzas en Plesk (nextconvers-vps): home.pmediaplus.com
set -euo pipefail

JUMP="${HOME_FINANCE_JUMP:-parvus-vps}"
PROD="${HOME_FINANCE_PROD:-nextconvers-vps}"
DOCROOT="/var/www/vhosts/parvusmedia.com/home"
PRIVATE="/var/www/vhosts/parvusmedia.com/private/home-finance"
LOCAL="/workspace/home-finance"
DOMAIN="home.pmediaplus.com"

echo "==> Private dir + token (no sobrescribe token existente)"
ssh "$JUMP" "ssh $PROD \"install -d -m 700 $PRIVATE $PRIVATE/data && \
  if [ ! -f $PRIVATE/app.env ]; then \
    umask 077; \
    { echo HOME_FINANCE_API_TOKEN=\\\$(openssl rand -hex 32); echo HOME_FINANCE_DATA_DIR=$PRIVATE/data; } > $PRIVATE/app.env; \
    chown parvusadmin:psaserv $PRIVATE/app.env; \
    echo 'Token nuevo en $PRIVATE/app.env'; \
  fi\""

echo "==> Sync public files"
tar -C "$LOCAL/public" -cf - . | ssh "$JUMP" "ssh $PROD \"tar -C $DOCROOT -xf -\""
ssh "$JUMP" "ssh $PROD \"chown -R parvusadmin:psaserv $DOCROOT && find $DOCROOT -type f -exec chmod 644 {} \\\\; && find $DOCROOT -type d -exec chmod 755 {} \\\;\""

echo "==> PHP 8.3 FPM (no usar .user.ini: provoca SIGSEGV en este Plesk)"
ssh "$JUMP" "ssh $PROD \"rm -f $DOCROOT/.user.ini; plesk bin site --update $DOMAIN -php true -php_handler_id plesk-php83-fpm; plesk repair web -y $DOMAIN\""

echo "==> Let's Encrypt"
ssh "$JUMP" "ssh $PROD \"plesk ext sslit --certificate -issue -domain $DOMAIN -secure-domain 2>/dev/null || true\""

echo "==> Done. Clave: grep HOME_FINANCE_API_TOKEN $PRIVATE/app.env en $PROD"
echo "    URL: https://$DOMAIN/"
