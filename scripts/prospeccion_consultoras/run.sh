#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${CONSULTORAS_PYTHON:-/opt/apps/linkedinreport/.venv/bin/python3}"
exec "$PYTHON" "${DIR}/pipeline.py" "$@"
