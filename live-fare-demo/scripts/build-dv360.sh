#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/dist"
ZIP="$OUT_DIR/dv360-creative.zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$OUT_DIR" "$STAGE/creative"
cp "$ROOT/creative/index.html" "$ROOT/creative/styles.css" "$ROOT/creative/app.js" "$STAGE/creative/"
if [[ -d "$ROOT/creative/assets" ]]; then
  mkdir -p "$STAGE/creative/assets"
  find "$ROOT/creative/assets" -type f ! -name '.gitkeep' -exec cp {} "$STAGE/creative/assets/" \;
  rmdir "$STAGE/creative/assets" 2>/dev/null || true
fi

rm -f "$ZIP"
(
  cd "$STAGE/creative"
  zip -X -r "$ZIP" . -x "*.DS_Store" -x "**/.DS_Store" -x "**/.gitkeep" -x ".gitkeep"
)

BYTES="$(wc -c < "$ZIP" | tr -d ' ')"
echo "Wrote $ZIP"
echo "ZIP bytes=$BYTES"
python3 - <<PY
from pathlib import Path
p = Path("$ZIP")
kb = p.stat().st_size / 1024
print(f"ZIP size: {kb:.1f} KB")
PY
unzip -l "$ZIP"
unzip -l "$ZIP" | grep -q "saudia-logo.svg"
