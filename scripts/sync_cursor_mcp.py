#!/usr/bin/env python3
"""Genera .cursor/mcp.json desde config/n8n.local.env para reutilizar MCP en Cursor."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from n8n_env import LOCAL_ENV, load_n8n_env  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MCP_FILE = ROOT / ".cursor" / "mcp.json"


def build_mcp_config() -> dict:
    load_n8n_env()
    url = os.getenv("N8N_MCP_ENDPOINT", "https://pmedia.app.n8n.cloud/mcp-server/http")
    token = os.getenv("N8N_MCP_TOKEN", "").strip()

    server: dict = {
        "type": "streamable-http",
        "url": url,
    }
    if token:
        server["headers"] = {"Authorization": f"Bearer {token}"}

    return {"mcpServers": {"N8N_": server}}


def main() -> int:
    if not LOCAL_ENV.exists():
        print(f"No existe {LOCAL_ENV}; crea el archivo desde config/n8n.local.env.example", file=sys.stderr)
        return 1

    MCP_FILE.parent.mkdir(parents=True, exist_ok=True)
    MCP_FILE.write_text(json.dumps(build_mcp_config(), indent=2) + "\n", encoding="utf-8")
    print(f"Escrito {MCP_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
