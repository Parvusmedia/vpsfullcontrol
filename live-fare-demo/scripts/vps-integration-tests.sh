#!/usr/bin/env bash
# Runs on the VPS as root after deploy.
set -euo pipefail
DOMAIN="${LIVE_FARE_DOMAIN:-flights.pmediaplus.com}"
APP="${1:-/opt/apps/live-fare-demo}"
PY=(sudo -u cursorbot /usr/bin/python3 "$APP/feed/updater/update.py")
CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

if [[ -f "$CERT" && -f "$KEY" ]]; then
  BASE="https://${DOMAIN}"
  RESOLVE=(--resolve "${DOMAIN}:443:127.0.0.1")
  INSECURE=(-k)
else
  BASE="http://${DOMAIN}"
  RESOLVE=(--resolve "${DOMAIN}:80:127.0.0.1")
  INSECURE=()
fi
export LIVE_FARE_TEST_BASE="$BASE"

curl_h() {
  curl -fsS "${INSECURE[@]}" "${RESOLVE[@]}" "$@"
}

echo "=== using $BASE (--resolve → 127.0.0.1) ==="
echo "=== headers ==="
curl -sS "${INSECURE[@]}" -D - -o /dev/null "${RESOLVE[@]}" "$BASE/fares/network.json" | tr -d '\r' | tee /tmp/live-fare-headers.txt
python3 - <<'PY'
from pathlib import Path
text = Path("/tmp/live-fare-headers.txt").read_text().lower()
assert "access-control-allow-origin: *" in text, text
assert "content-type: application/json" in text, text
assert "max-age=30" in text, text
print("CORS/cache OK")
PY

echo "=== creative standalone ==="
curl_h "$BASE/creative/index.html" | grep -q "Saudia"
curl_h "$BASE/creative/index.html" | grep -q "saudia-logo.svg"
curl_h "$BASE/creative/index.html" | grep -q "السعودية"
curl_h "$BASE/creative/index.html" | grep -q 'aria-label="Saudia"'
curl_h "$BASE/creative/assets/saudia-logo.svg" | grep -q '<svg'
curl_h "$BASE/creative/app.js" | grep -q "cityLabel"
curl_h "$BASE/creative/app.js" | grep -q "B_LOCATION"
curl_h "$BASE/creative/app.js" | grep -q "network.json"
curl_h "$BASE/demo/" | grep -q "DV360 Live Fare POC"
echo "creative/demo HTML OK"

echo "=== pin fare JED-RUH 299 ==="
"${PY[@]}" --set JED RUH 2026-10 299
curl_h -o /tmp/live-fare-jed.json "$BASE/fares/JED.json"
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/tmp/live-fare-jed.json").read_text())
hit = next(f for f in data["fares"] if f["destination"] == "RUH" and f["month"] == "2026-10")
assert hit["price"] == 299, hit
print("pinned", hit["price"], hit.get("currency"))
PY

echo "=== restore JED-RUH 380 ==="
"${PY[@]}" --set JED RUH 2026-10 380

echo "=== stale then refresh ==="
"${PY[@]}" --stale 45
curl_h -o /tmp/live-fare-network.json "$BASE/fares/network.json"
python3 - <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
data = json.loads(Path("/tmp/live-fare-network.json").read_text())
updated = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
age_min = (datetime.now(timezone.utc) - updated).total_seconds() / 60
assert age_min >= 40, age_min
print("stale age_min", round(age_min, 1), "fares", len(data["fares"]))
PY
"${PY[@]}" --no-jitter

echo "=== missing feed 404 ==="
mv "$APP/feed/public/network.json" "$APP/feed/public/network.json.bak"
code="$(curl -sS "${INSECURE[@]}" -o /dev/null -w "%{http_code}" "${RESOLVE[@]}" "$BASE/fares/network.json" || true)"
mv "$APP/feed/public/network.json.bak" "$APP/feed/public/network.json"
chown cursorbot:cursorbot "$APP/feed/public/network.json"
[[ "$code" == "404" ]] || { echo "expected 404, got $code"; exit 1; }
echo "offline feed returns 404 OK"

echo "=== zip ==="
python3 - <<'PY'
from pathlib import Path
p = Path("/opt/apps/live-fare-demo/dist/dv360-creative.zip")
assert p.is_file()
print(f"zip_bytes={p.stat().st_size}")
PY

echo "INTEGRATION_OK"
