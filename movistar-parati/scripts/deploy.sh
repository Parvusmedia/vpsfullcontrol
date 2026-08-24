#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_DIR="/opt/apps/movistar-parati"

echo "==> Sync to VPS"
rsync -az --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.env' \
  "$ROOT/" parvus-vps:"$REMOTE_DIR/"

echo "==> Install deps + restart"
ssh parvus-vps "bash -s" <<'REMOTE'
set -euo pipefail
cd /opt/apps/movistar-parati/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
sudo cp /opt/apps/movistar-parati/deploy/movistar-parati-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable movistar-parati-api
sudo systemctl restart movistar-parati-api
sleep 2
curl -fsS http://127.0.0.1:8020/health
REMOTE

echo "Done."
