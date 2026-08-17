#!/usr/bin/env bash
# Runs on the VPS as root after deploy. Uses Host header (no public DNS required).
set -euo pipefail
DOMAIN="${LIVE_FARE_DOMAIN:-flights.pmediaplus.com}"
APP="${1:-/opt/apps/live-fare-demo}"
PY=(sudo -u cursorbot /usr/bin/python3 "$APP/feed/updater/update.py")
H=(-H "Host: $DOMAIN")

feed() {
  curl -fsS "${H[@]}" "http://127.0.0.1/fares/MAD.json"
}

echo "=== headers ==="
curl -sS -D - -o /dev/null "${H[@]}" "http://127.0.0.1/fares/MAD.json" | tr -d '\r' | tee /tmp/live-fare-headers.txt
python3 - <<'PY'
from pathlib import Path
text = Path("/tmp/live-fare-headers.txt").read_text().lower()
assert "access-control-allow-origin: *" in text
assert "content-type: application/json" in text
assert "max-age=30" in text
print("CORS/cache OK")
PY

echo "=== creative standalone ==="
curl -fsS "${H[@]}" "http://127.0.0.1/creative/index.html" | grep -q "Riyadh Air"
curl -fsS "${H[@]}" "http://127.0.0.1/creative/app.js" | grep -q "feedUrl"
curl -fsS "${H[@]}" "http://127.0.0.1/demo/" | grep -q "DV360 Live Fare POC"
echo "creative/demo HTML OK"

echo "=== pin fare 299 ==="
"${PY[@]}" --set MAD RUH 2026-10 299
python3 - <<'PY'
import json, urllib.request
req = urllib.request.Request("http://127.0.0.1/fares/MAD.json", headers={"Host": "flights.pmediaplus.com"})
data = json.load(urllib.request.urlopen(req, timeout=10))
hit = next(f for f in data["fares"] if f["destination"] == "RUH" and f["month"] == "2026-10")
assert hit["price"] == 299, hit
assert "destination=RUH" in hit["deeplink"]
print("pinned", hit["price"])
PY

echo "=== restore 379 ==="
"${PY[@]}" --set MAD RUH 2026-10 379

echo "=== stale then refresh ==="
"${PY[@]}" --stale 45
python3 - <<'PY'
from datetime import datetime, timezone
import json, urllib.request
req = urllib.request.Request("http://127.0.0.1/fares/MAD.json", headers={"Host": "flights.pmediaplus.com"})
data = json.load(urllib.request.urlopen(req, timeout=10))
updated = datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
age_min = (datetime.now(timezone.utc) - updated).total_seconds() / 60
assert age_min >= 40, age_min
print("stale age_min", round(age_min, 1))
PY
"${PY[@]}" --no-jitter

echo "=== missing feed 404 ==="
mv "$APP/feed/public/MAD.json" "$APP/feed/public/MAD.json.bak"
code="$(curl -sS -o /dev/null -w "%{http_code}" "${H[@]}" "http://127.0.0.1/fares/MAD.json" || true)"
mv "$APP/feed/public/MAD.json.bak" "$APP/feed/public/MAD.json"
chown cursorbot:cursorbot "$APP/feed/public/MAD.json"
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
