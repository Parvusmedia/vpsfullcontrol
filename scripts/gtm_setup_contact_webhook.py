#!/usr/bin/env python3
"""Idempotent GTM workspace setup: contact form -> n8n webhook (POST JSON)."""
from __future__ import annotations

import os
import sys

from gtm_api import load_env_file, service

WEBHOOK_ENV = "N8N_CONTACT_WEBHOOK_URL"
DEFAULT_WEBHOOK = (
    "https://pmedia.app.n8n.cloud/webhook/915f36a9-1e65-4a9f-9908-2ca92fd541df"
)

VAR_EMAIL = "dlv - form_email"
VAR_URL = "dlv - page_url"
TRIGGER_NAME = "CE - contact_form_submit"
TAG_NAME = "HTML - n8n contact webhook"


def workspace_path() -> str:
    aid = os.environ["GTM_ACCOUNT_ID"]
    cid = os.environ["GTM_CONTAINER_ID"]
    wid = os.environ["GTM_WORKSPACE_ID"]
    return f"accounts/{aid}/containers/{cid}/workspaces/{wid}"


def list_entities(list_api, parent: str, collection_key: str) -> list:
    return list_api.list(parent=parent).execute().get(collection_key, [])


def find_named(items: list, name: str):
    for item in items:
        if item.get("name") == name:
            return item
    return None


def dlv(name: str, display: str) -> dict:
    return {
        "name": display,
        "type": "v",
        "parameter": [
            {"type": "integer", "key": "dataLayerVersion", "value": "2"},
            {"type": "boolean", "key": "setDefaultValue", "value": "false"},
            {"type": "template", "key": "name", "value": name},
        ],
    }


def ensure_variable(api, parent: str, display: str, body: dict) -> str:
    items = list_entities(
        api.accounts().containers().workspaces().variables(), parent, "variable"
    )
    found = find_named(items, display)
    if found:
        return found["variableId"]
    created = (
        api.accounts()
        .containers()
        .workspaces()
        .variables()
        .create(parent=parent, body=body)
        .execute()
    )
    return created["variableId"]


def ensure_trigger(api, parent: str) -> str:
    items = list_entities(
        api.accounts().containers().workspaces().triggers(), parent, "trigger"
    )
    found = find_named(items, TRIGGER_NAME)
    if found:
        return found["triggerId"]
    body = {
        "name": TRIGGER_NAME,
        "type": "customEvent",
        "customEventFilter": [
            {
                "type": "equals",
                "parameter": [
                    {"type": "template", "key": "arg0", "value": "{{_event}}"},
                    {
                        "type": "template",
                        "key": "arg1",
                        "value": "contact_form_submit",
                    },
                ],
            }
        ],
    }
    created = (
        api.accounts()
        .containers()
        .workspaces()
        .triggers()
        .create(parent=parent, body=body)
        .execute()
    )
    return created["triggerId"]


def html_tag_body(webhook: str, trigger_id: str) -> dict:
    gtm_email = "{{" + VAR_EMAIL + "}}"
    gtm_url = "{{" + VAR_URL + "}}"
    html = (
        "<script>\n"
        "(function () {\n"
        f"  var email = '{gtm_email}';\n"
        f"  var pageUrl = '{gtm_url}';\n"
        "  if (!email) return;\n"
        f"  fetch('{webhook}', {{\n"
        "    method: 'POST',\n"
        "    headers: { 'Content-Type': 'application/json' },\n"
        "    body: JSON.stringify({ email: email, url: pageUrl }),\n"
        "    keepalive: true\n"
        "  }).catch(function () {});\n"
        "})();\n"
        "</script>"
    )
    return {
        "name": TAG_NAME,
        "type": "html",
        "parameter": [
            {"type": "template", "key": "html", "value": html},
            {"type": "boolean", "key": "supportDocumentWrite", "value": "false"},
        ],
        "firingTriggerId": [trigger_id],
    }


def ensure_tag(api, parent: str, webhook: str, trigger_id: str) -> str:
    items = list_entities(
        api.accounts().containers().workspaces().tags(), parent, "tag"
    )
    body = html_tag_body(webhook, trigger_id)
    found = find_named(items, TAG_NAME)
    if found:
        updated = (
            api.accounts()
            .containers()
            .workspaces()
            .tags()
            .update(path=found["path"], body={**body, "tagId": found["tagId"]})
            .execute()
        )
        return updated["tagId"]
    created = (
        api.accounts()
        .containers()
        .workspaces()
        .tags()
        .create(parent=parent, body=body)
        .execute()
    )
    return created["tagId"]


def publish(api, ws_path: str) -> None:
    version = (
        api.accounts()
        .containers()
        .workspaces()
        .create_version(
            path=ws_path,
            body={"name": "contact webhook n8n", "notes": "GTM agent setup"},
        )
        .execute()
    )
    ver_path = version["containerVersion"]["path"]
    api.accounts().containers().versions().publish(path=ver_path).execute()
    print(f"published: {ver_path}")


def main() -> int:
    load_env_file("/opt/apps/private/parvusmedia-web/gtm-api.env")
    for key in ("GTM_ACCOUNT_ID", "GTM_CONTAINER_ID", "GTM_WORKSPACE_ID"):
        if not os.environ.get(key):
            print(f"Missing {key} in gtm-api.env", file=sys.stderr)
            return 1
    webhook = os.environ.get(WEBHOOK_ENV, DEFAULT_WEBHOOK)
    api = service()
    parent = workspace_path()
    ensure_variable(api, parent, VAR_EMAIL, dlv("form_email", VAR_EMAIL))
    ensure_variable(api, parent, VAR_URL, dlv("page_url", VAR_URL))
    trigger_id = ensure_trigger(api, parent)
    tag_id = ensure_tag(api, parent, webhook, trigger_id)
    print(f"trigger_id={trigger_id} tag_id={tag_id}")
    try:
        publish(api, parent)
    except Exception as exc:  # noqa: BLE001
        print(f"publish skipped or failed: {exc}", file=sys.stderr)
        print("Publish manually in GTM if needed.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
