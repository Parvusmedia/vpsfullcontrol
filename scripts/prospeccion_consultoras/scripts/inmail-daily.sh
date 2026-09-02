#!/usr/bin/env bash
# Envía hasta 20 InMails SME/día con pausa fija de 3 minutos entre cada uno.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${CONSULTORAS_LOG_DIR:-$ROOT/data/logs}"
LOCK_FILE="${CONSULTORAS_INMAIL_LOCK:-/tmp/prospeccion-consultoras-inmail.lock}"
LIMIT="${CONSULTORAS_INMAIL_DAILY_LIMIT:-20}"
WAIT="${CONSULTORAS_INMAIL_WAIT_SECONDS:-180}"

mkdir -p "$LOG_DIR"
export PYTHONUNBUFFERED=1
set -a
[[ -f /etc/linkedinreport/app.env ]] && . /etc/linkedinreport/app.env
[[ -f "$ROOT/.env" ]] && . "$ROOT/.env"
set +a

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "==== $(date -Is) inmail-daily SKIP (already running) ===="
  exit 0
fi

{
  echo "==== $(date -Is) consultoras inmail-daily limit=$LIMIT wait=${WAIT}s ===="
  "$ROOT/run.sh" inmail --limit "$LIMIT" --live --wait-seconds "$WAIT"
  echo "==== $(date -Is) consultoras inmail-daily done ===="
} >>"$LOG_DIR/inmail-daily.log" 2>&1
