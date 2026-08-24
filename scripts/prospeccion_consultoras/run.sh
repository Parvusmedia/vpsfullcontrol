#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec /opt/apps/linkedinreport/.venv/bin/python3 "${ROOT}/scripts/prospeccion_consultoras/pipeline.py" "$@"
