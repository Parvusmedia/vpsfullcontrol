#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MINUTES="${1:-45}"
python3 "$ROOT/feed/updater/update.py" --stale "$MINUTES"
