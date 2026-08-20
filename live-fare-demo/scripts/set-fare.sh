#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ORIGIN="${1:?origin}"
DEST="${2:?destination}"
MONTH="${3:?month YYYY-MM}"
PRICE="${4:?price}"
python3 "$ROOT/feed/updater/update.py" --set "$ORIGIN" "$DEST" "$MONTH" "$PRICE"
