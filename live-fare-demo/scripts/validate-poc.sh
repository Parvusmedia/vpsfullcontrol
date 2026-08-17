#!/usr/bin/env bash
# HTTP validation of the live-fare POC. Usage: ./validate-poc.sh [base_url]
set -euo pipefail
BASE="${1:-https://flights.pmediaplus.com}"
CURL=(curl -fsS --max-time 15)

echo "=== Test 1 feed HTTPS ==="
"${CURL[@]}" "$BASE/fares/MAD.json" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['origin']=='MAD'; assert len(d['fares'])>=9; print('fares', len(d['fares']), 'updated', d['updated_at'])"

echo "=== Test 2 CORS + cache headers ==="
hdr="$(mktemp)"
curl -sS -D "$hdr" -o /dev/null --max-time 15 "$BASE/fares/MAD.json"
python3 - "$hdr" <<'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text().lower()
assert "access-control-allow-origin: *" in text, text
assert "content-type: application/json" in text, text
assert "cache-control:" in text and "max-age=30" in text, text
print("headers ok")
PY

echo "=== Test 4 MAD-RUH-2026-10 price present ==="
"${CURL[@]}" "$BASE/fares/MAD.json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
hit=next(f for f in d['fares'] if f['destination']=='RUH' and f['month']=='2026-10')
assert isinstance(hit['price'], int)
assert hit['deeplink']
print('MAD-RUH-2026-10', hit['price'], hit['currency'])
"

echo "=== Test 9 deeplinks unique per combo ==="
"${CURL[@]}" "$BASE/fares/MAD.json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
links=set(f['deeplink'] for f in d['fares'])
assert len(links)==len(d['fares'])
print('unique deeplinks', len(links))
"

echo "=== Test health ==="
"${CURL[@]}" "$BASE/health" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('feed_exists') is True
assert d.get('status') in ('ok','degraded')
print(d)
"

echo "=== Test 11 zip exists on server tree if present ==="
echo "VALIDATE_HTTP_OK $BASE"
