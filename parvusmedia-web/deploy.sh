#!/usr/bin/env bash
# Deploy parvusmedia-web to Plesk httpdocs on nextconvers-vps.
# Run from this directory, or from a machine that can SSH to parvus-vps.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
REMOTE_SRC="/opt/apps/parvusmedia-web"
DEST="nextconvers-vps:/var/www/vhosts/parvusmedia.com/httpdocs"

echo "Syncing source to $REMOTE_SRC on parvus-vps…"
ssh parvus-vps "mkdir -p '$REMOTE_SRC/css' '$REMOTE_SRC/js' '$REMOTE_SRC/chatgpt-ads'"
scp -q \
  "$ROOT/index.html" \
  "$ROOT/contact.php" \
  "$ROOT/robots.txt" \
  "$ROOT/README.md" \
  "$ROOT/.htaccess" \
  parvus-vps:"$REMOTE_SRC/"
scp -q "$ROOT/css/main.css" parvus-vps:"$REMOTE_SRC/css/main.css"
scp -q "$ROOT/js/main.js" parvus-vps:"$REMOTE_SRC/js/main.js"
scp -q "$ROOT/chatgpt-ads/index.html" parvus-vps:"$REMOTE_SRC/chatgpt-ads/index.html"

echo "Rsync to production…"
ssh parvus-vps bash -s <<EOF
set -euo pipefail
cd '$REMOTE_SRC'
rsync -avz index.html contact.php robots.txt '$DEST/'
rsync -avz css/main.css '$DEST/css/main.css'
rsync -avz js/main.js '$DEST/js/main.js'
rsync -avz chatgpt-ads/ '$DEST/chatgpt-ads/'
ssh nextconvers-vps 'chown -R parvusadmin:psacln /var/www/vhosts/parvusmedia.com/httpdocs/{index.html,contact.php,robots.txt,css/main.css,js/main.js,chatgpt-ads}'
EOF

echo "Deployed ChatGPT Ads pages to https://parvusmedia.com/ and https://parvusmedia.com/chatgpt-ads/"
