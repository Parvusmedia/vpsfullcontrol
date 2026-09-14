#!/usr/bin/env bash
# Sync Smartlead bounces → Unipile queue, then drain (respects automation_limits).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${RECKITT_LOG_DIR:-$ROOT/data/logs}"
mkdir -p "$LOG_DIR"
# shellcheck disable=SC1091
set -a
[[ -f /etc/linkedinreport/app.env ]] && . /etc/linkedinreport/app.env
[[ -f "$ROOT/.env" ]] && . "$ROOT/.env"
set +a
export RECKITT_UNIPILE_DAILY_CAP="${RECKITT_UNIPILE_DAILY_CAP:-10}"
{
  echo "==== $(date -Is) unipile-drain ===="
  "$ROOT/run.sh" sync-bounces --live
  "$ROOT/run.sh" unipile-drain --live
} >>"$LOG_DIR/unipile-drain.log" 2>&1
