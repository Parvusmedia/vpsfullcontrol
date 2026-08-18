#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-https://usj-advisor.pmediaplus.com}"
curl -fsS "$BASE/api/health"
echo
python3 - "$BASE" <<'PY'
import json, urllib.request, ssl, sys
base = sys.argv[1]
ctx = ssl.create_default_context()
def post(path, body):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        return json.load(r)
physio = post("/api/recommend", {"message": "I'm a physiotherapist with three years of experience. I work with athletes and I'd like to specialize without leaving my current job."})
assert physio["best"]["programme_id"] == "biomechanics", physio
print("physio OK", physio["best"]["score_pct"])
dev = post("/api/recommend", {"message": "I studied software engineering and currently work as a developer. I want to understand how to apply AI to real business problems."})
assert dev["best"]["programme_id"] == "ai-applied", dev
print("dev OK", dev["best"]["score_pct"])
mkt = post("/api/recommend", {"message": "I studied Business Administration and work in digital marketing. I want to progress into a marketing management role."})
assert mkt["best"]["programme_id"] == "marketing", mkt
print("mkt OK", mkt["best"]["score_pct"])
edge = post("/api/recommend", {"message": "I'm a chef and want to become an architect."})
assert edge["has_strong_match"] is False
print("edge OK")
print("VALIDATE_OK")
PY
