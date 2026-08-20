#!/usr/bin/env bash
# HTTP validation of the live-fare POC. Usage: ./validate-poc.sh [base_url]
set -euo pipefail
BASE="${1:-https://flights.pmediaplus.com}"
CURL=(curl -fsS --max-time 15)

echo "=== Test 1 network feed HTTPS ==="
"${CURL[@]}" "$BASE/fares/network.json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert len(d['fares'])>=200
assert {o['code'] for o in d['origins']} >= {'JED','RUH','DXB','JFK'}
print('fares', len(d['fares']), 'origins', len(d['origins']), 'updated', d['updated_at'])
"

echo "=== Test 2 CORS + cache headers ==="
hdr="$(mktemp)"
curl -sS -D "$hdr" -o /dev/null --max-time 15 "$BASE/fares/network.json"
python3 - "$hdr" <<'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text().lower()
assert "access-control-allow-origin: *" in text, text
assert "content-type: application/json" in text, text
assert "cache-control:" in text and "max-age=30" in text, text
print("headers ok")
PY

echo "=== Test 4 JED-RUH-2026-10 ==="
"${CURL[@]}" "$BASE/fares/JED.json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d['origin']=='JED'
hit=next(f for f in d['fares'] if f['destination']=='RUH' and f['month']=='2026-10')
assert isinstance(hit['price'], int)
print('JED-RUH-2026-10', hit['price'], hit['currency'])
"

echo "=== Test UAE/US origins ==="
"${CURL[@]}" "$BASE/fares/DXB.json" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['origin']=='DXB'; print('DXB fares', len(d['fares']))"
"${CURL[@]}" "$BASE/fares/JFK.json" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['origin']=='JFK'; print('JFK fares', len(d['fares']))"

echo "=== Test health ==="
"${CURL[@]}" "$BASE/health" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('feed_exists') is True
assert d.get('fares_count',0)>=200
print(d)
"

echo "VALIDATE_HTTP_OK $BASE"
