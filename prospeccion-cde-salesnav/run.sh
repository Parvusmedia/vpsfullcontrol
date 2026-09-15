#!/usr/bin/env bash
# CDE SalesNav prospecting CLI — uses linkedinreport venv (httpx).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PY="${LINKEDINREPORT_VENV:-/opt/apps/linkedinreport/.venv/bin/python}"
if [[ ! -x "$VENV_PY" ]]; then
  VENV_PY="${PYTHON:-python3}"
fi
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
exec "$VENV_PY" -m cde_salesnav "$@"
