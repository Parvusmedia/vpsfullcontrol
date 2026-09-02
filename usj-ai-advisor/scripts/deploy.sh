#!/usr/bin/env bash
# Idempotent deploy. Does not restart unrelated services.
# TLS: never certbot --nginx. Webroot only, then write our 443 block.
set -euo pipefail

ROOT=""
if [[ $# -ge 1 && -d "$1" ]]; then
  ROOT="$(cd "$1" && pwd)"
elif [[ "$(basename "$(cd "$(dirname "$0")" && pwd)")" == "scripts" ]]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
else
  echo "Usage: $0 /path/to/usj-ai-advisor" >&2
  exit 1
fi

DEST="/opt/apps/usj-ai-advisor"
DOMAIN="${USJ_ADVISOR_DOMAIN:-usjdemo.pmediaplus.com}"
VPS_IP="${VPS_IP:-87.106.194.137}"
PORT="${USJ_ADVISOR_PORT:-8021}"
SITE_AVAIL="/etc/nginx/sites-available/usj-ai-advisor"
SITE_EN="/etc/nginx/sites-enabled/usj-ai-advisor"
SNIPPET="/etc/nginx/snippets/usj-ai-advisor-locations.conf"
CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-running with sudo"
  exec sudo --preserve-env=USJ_ADVISOR_DOMAIN,VPS_IP,USJ_ADVISOR_PORT "$0" "$@"
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
  install -D -m 644 "$DEST/deploy/nginx-usj-locations.conf" "$SNIPPET"
  sed -i "s/127.0.0.1:8021/127.0.0.1:${PORT}/g" "$SNIPPET"
  if [[ -f "$CERT" && -f "$KEY" ]]; then
    write_ssl_site
    echo "nginx site: HTTPS (${DOMAIN})"
  else
    install -m 644 "$DEST/deploy/nginx-usj-ai-advisor.conf" "$SITE_AVAIL"
    sed -i "s/usjdemo.pmediaplus.com/${DOMAIN}/g" "$SITE_AVAIL"
    echo "nginx site: HTTP only (no cert yet)"
  fi
  ln -sfn "$SITE_AVAIL" "$SITE_EN"
}

echo "=== deploy usj-ai-advisor → $DEST ($DOMAIN :$PORT) ==="
echo "Note: demo host is ${DOMAIN} (not usj.pmediaplus.com, which already has another app)."
mkdir -p "$DEST" /var/www/html "$DEST/backend/storage"
if [[ ! -f "$DEST/.env" ]]; then
  cp "$ROOT/.env.example" "$DEST/.env"
fi

rsync -a \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '*.pyc' \
  "$ROOT/" "$DEST/"

chown -R cursorbot:cursorbot "$DEST"
chmod 755 "$DEST/scripts/"*.sh

python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install -q --upgrade pip
"$DEST/.venv/bin/pip" install -q -r "$DEST/backend/requirements.txt"
chown -R cursorbot:cursorbot "$DEST/.venv" "$DEST/backend/storage"

install -m 644 "$DEST/deploy/usj-ai-advisor.service" /etc/systemd/system/usj-ai-advisor.service
sed -i "s/--port 8021/--port ${PORT}/" /etc/systemd/system/usj-ai-advisor.service
systemctl daemon-reload
systemctl enable usj-ai-advisor.service
systemctl restart usj-ai-advisor.service

install_nginx_site
nginx -t
systemctl reload nginx

for i in $(seq 1 25); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null; then
    echo "API up on 127.0.0.1:${PORT}"
    break
  fi
  sleep 0.4
  if [[ "$i" -eq 25 ]]; then
    systemctl status usj-ai-advisor.service --no-pager -l | sed -n '1,80p'
    exit 1
  fi
done

resolved=""
for i in $(seq 1 20); do
  resolved="$(dig +short "$DOMAIN" A @82.223.3.205 2>/dev/null | awk 'NF && $1 !~ /[A-Za-z]/ {print; exit}')"
  if [[ -z "$resolved" ]]; then
    resolved="$(dig +short "$DOMAIN" A @1.1.1.1 2>/dev/null | awk 'NF && $1 !~ /[A-Za-z]/ {print; exit}')"
  fi
  echo "DNS $DOMAIN -> ${resolved:-none} (want $VPS_IP) try $i"
  if [[ "$resolved" == "$VPS_IP" ]]; then
    break
  fi
  sleep 3
done
if [[ "$resolved" == "$VPS_IP" ]]; then
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

echo "DEPLOY_OK"
