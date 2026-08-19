#!/usr/bin/env python3
"""Carga config/n8n.local.env para scripts n8n (sin imprimir secretos)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ENV = ROOT / "config" / "n8n.local.env"


def load_n8n_env() -> Path | None:
    """Carga variables desde config/n8n.local.env si existen."""
    if not LOCAL_ENV.exists():
        return None

    for line in LOCAL_ENV.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
    return LOCAL_ENV


def n8n_config_status() -> dict[str, str]:
    load_n8n_env()
    return {
        "env_file": "present" if LOCAL_ENV.exists() else "missing",
        "n8n_url": "set" if os.getenv("N8N_URL") else "missing",
        "n8n_api_key": "set" if os.getenv("N8N_API_KEY") else "missing",
        "n8n_rest_api_key": "set" if os.getenv("N8N_REST_API_KEY") else "missing",
        "n8n_mcp_token": "set" if os.getenv("N8N_MCP_TOKEN") else "missing",
    }
