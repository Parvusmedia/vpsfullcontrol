#!/usr/bin/env bash
# Install flightsdemobot on Parvus VPS (does not touch fly456).
set -euo pipefail

APP_ROOT="/opt/apps/flightsdemobot"
ENV_FILE="/etc/flightsdemobot/app.env"
SERVICE="flightsdemobot.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root or via sudo" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$APP_ROOT" /etc/flightsdemobot /var/lib/flightsdemobot
rsync -a --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude 'app.env' \
  "$SRC_ROOT/" "$APP_ROOT/"

chown -R cursorbot:cursorbot "$APP_ROOT" /var/lib/flightsdemobot

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$APP_ROOT/app.env.example" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  chown root:root "$ENV_FILE"
  echo "Created $ENV_FILE — set TELEGRAM_BOT_TOKEN and ACCESS_KEY before start."
fi

python3 -m venv "$APP_ROOT/.venv"
"$APP_ROOT/.venv/bin/pip" install -q -r "$APP_ROOT/requirements.txt"

install -m 644 "$APP_ROOT/systemd/flightsdemobot.service" "/etc/systemd/system/$SERVICE"
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"
systemctl is-active --quiet "$SERVICE" && echo "flightsdemobot: active"
