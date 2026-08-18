#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
if [[ -f /etc/flightsdemobot/app.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source /etc/flightsdemobot/app.env
  set +a
fi
PY="$ROOT/.venv/bin/python3"
if [[ ! -x "$PY" ]]; then
  PY=python3
fi
exec "$PY" "$ROOT/src/main.py"
