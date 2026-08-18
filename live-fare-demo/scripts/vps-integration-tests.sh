#!/usr/bin/env bash
# Runs on the VPS as root after deploy.
set -euo pipefail
DOMAIN="${LIVE_FARE_DOMAIN:-flights.pmediaplus.com}"
APP="${1:-/opt/apps/live-fare-demo}"
PY=(sudo -u cursorbot /usr/bin/python3 "$APP/feed/updater/update.py")
H=(-H "Host: $DOMAIN")
INSECURE=()
BASE="http://127.0.0.1"
if curl -skI --max-time 5 "${H[@]}" "https://127.0.0.1/health" | grep -qi "200 OK"; then
  BASE="https://127.0.0.1"
  INSECURE=(-k)
fi
export LIVE_FARE_TEST_BASE="$BASE"

curl_h() {
  curl -fsS "${INSECURE[@]}" "${H[@]}" "$@"
}

echo "=== using $BASE ==="
echo "=== headers ==="
curl -sS "${INSECURE[@]}" -D - -o /dev/null "${H[@]}" "$BASE/fares/network.json" | tr -d '\r' | tee /tmp/live-fare-headers.txt
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
curl_h "$BASE/creative/app.js" | grep -q "network.json"
curl_h "$BASE/demo/" | grep -q "DV360 Live Fare POC"
echo "creative/demo HTML OK"

echo "=== pin fare JED-RUH 299 ==="
"${PY[@]}" --set JED RUH 2026-10 299
python3 - <<'PY'
import json, os, ssl, urllib.request
base = os.environ["LIVE_FARE_TEST_BASE"]
ctx = ssl._create_unverified_context() if base.startswith("https") else None
req = urllib.request.Request(base + "/fares/JED.json", headers={"Host": "flights.pmediaplus.com"})
data = json.load(urllib.request.urlopen(req, timeout=10, context=ctx))
hit = next(f for f in data["fares"] if f["destination"] == "RUH" and f["month"] == "2026-10")
assert hit["price"] == 299, hit
print("pinned", hit["price"], hit.get("currency"))
PY

echo "=== restore JED-RUH 380 ==="
"${PY[@]}" --set JED RUH 2026-10 380

echo "=== stale then refresh ==="
"${PY[@]}" --stale 45
python3 - <<'PY'
from datetime import datetime, timezone
import json, os, ssl, urllib.request
base = os.environ["LIVE_FARE_TEST_BASE"]
ctx = ssl._create_unverified_context() if base.startswith("https") else None
req = urllib.request.Request(base + "/fares/network.json", headers={"Host": "flights.pmediaplus.com"})
data = json.load(urllib.request.urlopen(req, timeout=10, context=ctx))
updated = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
age_min = (datetime.now(timezone.utc) - updated).total_seconds() / 60
assert age_min >= 40, age_min
print("stale age_min", round(age_min, 1), "fares", len(data["fares"]))
PY
"${PY[@]}" --no-jitter

echo "=== missing feed 404 ==="
mv "$APP/feed/public/network.json" "$APP/feed/public/network.json.bak"
code="$(curl -sS "${INSECURE[@]}" -o /dev/null -w "%{http_code}" "${H[@]}" "$BASE/fares/network.json" || true)"
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
