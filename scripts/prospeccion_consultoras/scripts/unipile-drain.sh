#!/usr/bin/env bash
# Poll acceptances → follow-up → pending invites (consultoras).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${CONSULTORAS_LOG_DIR:-$ROOT/data/logs}"
mkdir -p "$LOG_DIR"
set -a
[[ -f /etc/linkedinreport/app.env ]] && . /etc/linkedinreport/app.env
[[ -f "$ROOT/.env" ]] && . "$ROOT/.env"
set +a
{
  echo "==== $(date -Is) consultoras unipile-drain ===="
  "$ROOT/run.sh" outreach --live --contact-limit 6 --followup-limit 3
} >>"$LOG_DIR/unipile-drain.log" 2>&1
