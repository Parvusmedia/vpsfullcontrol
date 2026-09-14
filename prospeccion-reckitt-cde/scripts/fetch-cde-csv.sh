#!/usr/bin/env bash
# Copy the Reckitt CDE Sales Nav export from nextconvers-vps into data/ (gitignored).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK_ID="${RECKITT_CDE_TASK_ID:-tsk_fb6268304961e568}"
REMOTE_CSV="/var/www/vhosts/companydataenrichment.com/private/cde/salesnav_exports/${TASK_ID}.csv"
DEST="${RECKITT_CSV_PATH:-$ROOT/data/${TASK_ID}.csv}"
mkdir -p "$(dirname "$DEST")"

fetch_via() {
  local host="$1"
  ssh -o BatchMode=yes -o ConnectTimeout=12 "$host" "cat '$REMOTE_CSV'"
}

if [[ "$(hostname -s 2>/dev/null || true)" == "mail" ]] || [[ -f "$REMOTE_CSV" ]]; then
  cp -f "$REMOTE_CSV" "$DEST"
elif ssh -o BatchMode=yes -o ConnectTimeout=8 nextconvers-vps "test -f '$REMOTE_CSV'" 2>/dev/null; then
  fetch_via nextconvers-vps > "$DEST"
elif ssh -o BatchMode=yes -o ConnectTimeout=8 parvus-vps "ssh -o BatchMode=yes nextconvers-vps \"test -f '$REMOTE_CSV'\"" 2>/dev/null; then
  ssh -o BatchMode=yes parvus-vps "ssh -o BatchMode=yes nextconvers-vps \"cat '$REMOTE_CSV'\"" > "$DEST"
else
  echo "Cannot reach $REMOTE_CSV (try from parvus-vps or nextconvers-vps)" >&2
  exit 1
fi

chmod 600 "$DEST"
echo "Wrote $DEST ($(wc -l < "$DEST") lines)"
