#!/usr/bin/env python3
"""Remove duplicate n8n HTML tag from GTM (webhook handled server-side)."""
from __future__ import annotations

import os
import sys

from gtm_api import load_env_file, service

TAG_NAME = "HTML - n8n contact webhook"


def main() -> int:
    load_env_file("/opt/apps/private/parvusmedia-web/gtm-api.env")
    api = service()
    parent = (
        f"accounts/{os.environ['GTM_ACCOUNT_ID']}/containers/"
        f"{os.environ['GTM_CONTAINER_ID']}/workspaces/{os.environ['GTM_WORKSPACE_ID']}"
    )
    tags = (
        api.accounts()
        .containers()
        .workspaces()
        .tags()
        .list(parent=parent)
        .execute()
        .get("tag", [])
    )
    target = next((t for t in tags if t.get("name") == TAG_NAME), None)
    if not target:
        print("tag not found (already removed)")
        return 0
    api.accounts().containers().workspaces().tags().delete(path=target["path"]).execute()
    print("deleted", TAG_NAME)
    ws_path = parent
    version = (
        api.accounts()
        .containers()
        .workspaces()
        .create_version(
            path=ws_path,
            body={"name": "remove duplicate n8n tag", "notes": "server-side webhook only"},
        )
        .execute()
    )
    api.accounts().containers().versions().publish(
        path=version["containerVersion"]["path"]
    ).execute()
    print("published", version["containerVersion"]["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
