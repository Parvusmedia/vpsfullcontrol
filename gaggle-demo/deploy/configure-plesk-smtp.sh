#!/usr/bin/env bash
# Añade variables SMTP Plesk a /opt/apps/private/gaggle-demo/publora.env (no imprime la contraseña).
set -euo pipefail

ENV_FILE="${ENV_FILE:-/opt/apps/private/gaggle-demo/publora.env}"
HOST="${NGAGED_SMTP_HOST:-mail.pmediaplus.com}"
PORT="${NGAGED_SMTP_PORT:-587}"
SECURE="${NGAGED_SMTP_SECURE:-tls}"
USER="${NGAGED_SMTP_USER:-alerts@pmediaplus.com}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "No existe $ENV_FILE"
  exit 1
fi

if [[ -z "${NGAGED_SMTP_PASSWORD:-}" ]]; then
  echo "Define NGAGED_SMTP_PASSWORD (contraseña del buzón Plesk $USER) y vuelve a ejecutar."
  echo 'Ejemplo: NGAGED_SMTP_PASSWORD="..." ./deploy/configure-plesk-smtp.sh'
  exit 1
fi

upsert() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

upsert NGAGED_SMTP_HOST "$HOST"
upsert NGAGED_SMTP_PORT "$PORT"
upsert NGAGED_SMTP_SECURE "$SECURE"
upsert NGAGED_SMTP_USER "$USER"
upsert NGAGED_SMTP_PASSWORD "$NGAGED_SMTP_PASSWORD"

chmod 600 "$ENV_FILE"
echo "SMTP Plesk configurado en $ENV_FILE (host=$HOST user=$USER)."
