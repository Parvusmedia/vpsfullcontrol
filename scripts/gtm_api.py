#!/usr/bin/env python3
"""Minimal Google Tag Manager API v2 CLI for Parvus agents."""
from __future__ import annotations

import argparse
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.readonly",
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.publish",
]


def load_env_file(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def credentials():
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.isfile(creds_path):
        print(
            "Missing GOOGLE_APPLICATION_CREDENTIALS or file not found.\n"
            "See docs/GTM_API_CURSOR.md",
            file=sys.stderr,
        )
        sys.exit(1)
    return service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )


def service():
    return build("tagmanager", "v2", credentials=credentials(), cache_discovery=False)


def cmd_accounts(_args):
    api = service()
    res = api.accounts().list().execute()
    for acc in res.get("account", []):
        print(f"{acc.get('accountId')}\t{acc.get('name')}\t{acc.get('path')}")


def cmd_containers(args):
    api = service()
    parent = f"accounts/{args.account_id}"
    res = api.accounts().containers().list(parent=parent).execute()
    for c in res.get("container", []):
        print(
            f"{c.get('containerId')}\t{c.get('publicId')}\t{c.get('name')}\t{c.get('path')}"
        )


def cmd_workspaces(args):
    api = service()
    parent = f"accounts/{args.account_id}/containers/{args.container_id}"
    res = api.accounts().containers().workspaces().list(parent=parent).execute()
    for w in res.get("workspace", []):
        print(f"{w.get('workspaceId')}\t{w.get('name')}\t{w.get('path')}")


def main():
    default_env = "/opt/apps/private/parvusmedia-web/gtm-api.env"
    if os.path.isfile(default_env):
        load_env_file(default_env)

    parser = argparse.ArgumentParser(description="GTM API helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("accounts", help="List GTM accounts").set_defaults(func=cmd_accounts)

    p_cont = sub.add_parser("containers", help="List containers in an account")
    p_cont.add_argument("--account-id", required=True)
    p_cont.set_defaults(func=cmd_containers)

    p_ws = sub.add_parser("workspaces", help="List workspaces in a container")
    p_ws.add_argument("--account-id", required=True)
    p_ws.add_argument("--container-id", required=True)
    p_ws.set_defaults(func=cmd_workspaces)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
