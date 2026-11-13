#!/usr/bin/env bash
# Deploy gaggle-demo to Parvus VPS (/opt/apps/gaggle-demo)
set -euo pipefail

REMOTE="${REMOTE:-parvus-vps}"
DEST="/opt/apps/gaggle-demo"
PRIVATE="/opt/apps/private/gaggle-demo"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Sync gaggle-demo to ${REMOTE}:${DEST}"
ssh "$REMOTE" "mkdir -p '$DEST' '$PRIVATE/data' && chmod 700 '$PRIVATE' '$PRIVATE/data'"

if command -v rsync >/dev/null 2>&1; then
  rsync -avz --delete \
    --exclude 'private/publora.env' \
    --exclude 'private/data/*.json' \
    "$ROOT/" "$REMOTE:$DEST/"
else
  tar -C "$ROOT" -czf - \
    --exclude='private/publora.env' \
    --exclude='private/data/*.json' \
    . | ssh "$REMOTE" "tar -xzf - -C '$DEST'"
fi

ssh "$REMOTE" "test -f '$PRIVATE/publora.env' || cp '$DEST/deploy/publora.env.example' '$PRIVATE/publora.env' && chmod 600 '$PRIVATE/publora.env'"

cat <<'NOTE'

Deploy sync complete.

1. Edit secrets on VPS (never commit):
   ssh parvus-vps 'nano /opt/apps/private/gaggle-demo/publora.env'

2. Serve public/ (pick one):
   - nginx location → /opt/apps/gaggle-demo/public
   - or: php -S 0.0.0.0:8790 -t /opt/apps/gaggle-demo/public /opt/apps/gaggle-demo/public/router.php

3. Health: GET /api/health

NOTE
