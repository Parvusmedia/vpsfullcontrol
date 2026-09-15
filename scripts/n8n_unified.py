#!/usr/bin/env python3
"""Single-entry n8n helper for MCP + REST workflows.

Usage examples:
  python3 scripts/n8n_unified.py status
  python3 scripts/n8n_unified.py list --limit 20
  python3 scripts/n8n_unified.py details --workflow-id <id>
  python3 scripts/n8n_unified.py export --out /workspace/n8n_export_latest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
import os


def _is_jwt(value: str) -> bool:
    return value.count(".") == 2


def _safe_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_") or "workflow"


class N8NClient:
    def __init__(self, base_url: str, rest_key: str | None, mcp_token: str | None) -> None:
        self.base_url = base_url.rstrip("/")
        self.rest_key = rest_key
        self.mcp_token = mcp_token

    def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return response.status, {}
                try:
                    return response.status, json.loads(raw)
                except json.JSONDecodeError:
                    return response.status, {"raw": raw}
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
            except Exception:  # pragma: no cover - defensive
                data = {"error": "http_error", "status": exc.code}
            return exc.code, data
        except urllib.error.URLError as exc:
            return 0, {"error": "url_error", "detail": str(exc)}

    def healthz(self) -> tuple[int, Any]:
        return self._request("GET", f"{self.base_url}/healthz")

    def rest_get(self, path: str, params: dict[str, Any] | None = None) -> tuple[int, Any]:
        if not self.rest_key:
            return 0, {"error": "missing_rest_key"}
        url = f"{self.base_url}{path}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        return self._request("GET", url, headers={"X-N8N-API-KEY": self.rest_key})

    def _mcp_raw(self, method: str, params: dict[str, Any] | None = None, req_id: str = "1") -> tuple[int, Any]:
        if not self.mcp_token:
            return 0, {"error": "missing_mcp_token"}
        url = f"{self.base_url}/mcp-server/http"
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        headers = {
            "Authorization": f"Bearer {self.mcp_token}",
            "Accept": "application/json, text/event-stream",
        }
        status, data = self._request("POST", url, headers=headers, payload=payload)
        if status != 200:
            return status, data
        if isinstance(data, dict) and "raw" in data and "result" not in data:
            parsed = self._parse_mcp_sse(str(data.get("raw") or ""))
            if parsed is not None:
                return status, parsed
        return status, data

    @staticmethod
    def _parse_mcp_sse(raw: str) -> dict[str, Any] | None:
        data_lines = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
        if not data_lines:
            return None
        try:
            parsed = json.loads(data_lines[-1])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def mcp_initialize(self) -> tuple[int, Any]:
        params = {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "n8n-unified", "version": "1.0.0"},
        }
        return self._mcp_raw("initialize", params=params, req_id="init-1")

    def mcp_tools_list(self) -> tuple[int, Any]:
        return self._mcp_raw("tools/list", params={}, req_id="tools-list-1")

    def mcp_tool_call(self, name: str, arguments: dict[str, Any]) -> tuple[int, Any]:
        status, data = self._mcp_raw(
            "tools/call",
            params={"name": name, "arguments": arguments},
            req_id=f"tool-{name}",
        )
        if status != 200:
            return status, data

        if not isinstance(data, dict):
            return status, data
        result = data.get("result", {})
        if isinstance(result, dict):
            if "structuredContent" in result and isinstance(result["structuredContent"], dict):
                return status, result["structuredContent"]
            content = result.get("content")
            if isinstance(content, list):
                text_parts = []
                for entry in content:
                    if isinstance(entry, dict) and entry.get("type") == "text":
                        text_parts.append(entry.get("text", ""))
                merged = "\n".join(part for part in text_parts if part)
                if merged:
                    try:
                        return status, json.loads(merged)
                    except json.JSONDecodeError:
                        return status, {"text": merged}
        return status, data

    def probe_rest(self) -> tuple[bool, str]:
        status, _ = self.rest_get("/api/v1/workflows", {"limit": 1})
        if status == 200:
            return True, "ok"
        if status == 401:
            return False, "unauthorized"
        if status == 0:
            return False, "unreachable"
        return False, f"http_{status}"

    def probe_mcp(self) -> tuple[bool, str]:
        init_status, _ = self.mcp_initialize()
        if init_status != 200:
            if init_status == 401:
                return False, "unauthorized"
            if init_status == 0:
                return False, "unreachable"
            return False, f"http_{init_status}"
        list_status, _ = self.mcp_tools_list()
        if list_status == 200:
            return True, "ok"
        return False, f"http_{list_status}"


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _extract_rest_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload.get("workflows"), list):
            return payload["workflows"]
        if isinstance(payload.get("items"), list):
            return payload["items"]
    if isinstance(payload, list):
        return payload
    return []


def _detect_tokens() -> tuple[str | None, str | None]:
    rest_key = os.getenv("N8N_REST_API_KEY")
    mcp_token = os.getenv("N8N_MCP_TOKEN")
    legacy = os.getenv("N8N_API_KEY")

    if legacy:
        if not rest_key and legacy.startswith("n8n_api_"):
            rest_key = legacy
        if not mcp_token and _is_jwt(legacy):
            mcp_token = legacy
    return rest_key, mcp_token


def cmd_status(client: N8NClient) -> int:
    health_status, _ = client.healthz()
    rest_ok, rest_msg = client.probe_rest() if client.rest_key else (False, "missing")
    mcp_ok, mcp_msg = client.probe_mcp() if client.mcp_token else (False, "missing")

    _print_json(
        {
            "n8n_url": client.base_url,
            "healthz": health_status,
            "tokens": {
                "rest": "set" if client.rest_key else "missing",
                "mcp": "set" if client.mcp_token else "missing",
            },
            "probes": {
                "rest": {"ok": rest_ok, "result": rest_msg},
                "mcp": {"ok": mcp_ok, "result": mcp_msg},
            },
        }
    )
    return 0


def cmd_list(client: N8NClient, limit: int, query: str | None) -> int:
    if client.rest_key:
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["filter"] = query
        status, payload = client.rest_get("/api/v1/workflows", params=params)
        if status == 200:
            _print_json({"mode": "rest", "count": len(_extract_rest_list(payload)), "data": _extract_rest_list(payload)})
            return 0

    if client.mcp_token:
        status, payload = client.mcp_tool_call(
            "search_workflows",
            {"limit": limit, **({"query": query} if query else {})},
        )
        if status == 200:
            _print_json({"mode": "mcp", **(payload if isinstance(payload, dict) else {"data": payload})})
            return 0

    _print_json({"error": "No se pudo listar workflows con los tokens disponibles."})
    return 1


def cmd_details(client: N8NClient, workflow_id: str) -> int:
    if client.rest_key:
        status, payload = client.rest_get(f"/api/v1/workflows/{workflow_id}")
        if status == 200:
            _print_json({"mode": "rest", "data": payload})
            return 0

    if client.mcp_token:
        status, payload = client.mcp_tool_call("get_workflow_details", {"workflowId": workflow_id})
        if status == 200:
            _print_json({"mode": "mcp", **(payload if isinstance(payload, dict) else {"data": payload})})
            return 0

    _print_json({"error": f"No se pudo obtener detalles para workflow {workflow_id}."})
    return 1


def _rest_export(client: N8NClient, out_dir: Path) -> int:
    all_items: list[dict[str, Any]] = []
    next_cursor: str | None = None
    seen: set[str] = set()

    while True:
        params: dict[str, Any] = {"limit": 100}
        if next_cursor:
            params["cursor"] = next_cursor
        status, payload = client.rest_get("/api/v1/workflows", params=params)
        if status != 200:
            _print_json({"error": "Fallo listando workflows por REST", "status": status, "payload": payload})
            return 1
        chunk = _extract_rest_list(payload)
        all_items.extend(chunk)

        if isinstance(payload, dict):
            candidate = payload.get("nextCursor") or payload.get("next_cursor") or payload.get("cursor")
            if isinstance(candidate, str) and candidate and candidate not in seen:
                seen.add(candidate)
                next_cursor = candidate
                if chunk:
                    continue
        break

    by_id = {item["id"]: item for item in all_items if isinstance(item, dict) and item.get("id")}
    workflows_path = out_dir / "workflows"
    workflows_path.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []

    for workflow_id, preview in sorted(by_id.items(), key=lambda kv: kv[0]):
        status, detail_payload = client.rest_get(f"/api/v1/workflows/{workflow_id}")
        if status != 200:
            continue
        detail = detail_payload.get("data") if isinstance(detail_payload, dict) and isinstance(detail_payload.get("data"), dict) else detail_payload
        if not isinstance(detail, dict):
            continue
        file_name = f"{_safe_name(detail.get('name', 'workflow'))}__{workflow_id}.json"
        with (workflows_path / file_name).open("w", encoding="utf-8") as f:
            json.dump(detail, f, ensure_ascii=False, indent=2)
        index.append(
            {
                "id": workflow_id,
                "name": detail.get("name"),
                "active": detail.get("active"),
                "updatedAt": detail.get("updatedAt"),
                "file": f"workflows/{file_name}",
            }
        )

    manifest = {
        "mode": "rest",
        "exportedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseUrl": client.base_url,
        "workflowCount": len(index),
        "workflows": index,
    }
    with (out_dir / "index.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    _print_json({"ok": True, "mode": "rest", "export_dir": str(out_dir), "workflow_count": len(index)})
    return 0


def _mcp_export(client: N8NClient, out_dir: Path) -> int:
    status, search_payload = client.mcp_tool_call("search_workflows", {"limit": 200})
    if status != 200 or not isinstance(search_payload, dict):
        _print_json({"error": "Fallo listando workflows por MCP", "status": status, "payload": search_payload})
        return 1

    items = search_payload.get("data", [])
    workflows_path = out_dir / "workflows"
    workflows_path.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        workflow_id = item["id"]
        detail_status, detail_payload = client.mcp_tool_call("get_workflow_details", {"workflowId": workflow_id})
        if detail_status != 200 or not isinstance(detail_payload, dict):
            continue
        detail = detail_payload.get("workflow")
        if not isinstance(detail, dict):
            continue
        file_name = f"{_safe_name(detail.get('name', 'workflow'))}__{workflow_id}.json"
        with (workflows_path / file_name).open("w", encoding="utf-8") as f:
            json.dump(detail_payload, f, ensure_ascii=False, indent=2)
        index.append(
            {
                "id": workflow_id,
                "name": detail.get("name"),
                "active": detail.get("active"),
                "updatedAt": detail.get("updatedAt"),
                "file": f"workflows/{file_name}",
            }
        )

    manifest = {
        "mode": "mcp",
        "exportedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseUrl": client.base_url,
        "workflowCount": len(index),
        "workflows": index,
        "note": "Export MCP incluye workflows visibles para ese token MCP.",
    }
    with (out_dir / "index.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    _print_json({"ok": True, "mode": "mcp", "export_dir": str(out_dir), "workflow_count": len(index)})
    return 0


def cmd_export(client: N8NClient, out: str | None) -> int:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path(out) if out else Path.cwd() / f"n8n_export_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    if client.rest_key:
        rest_ok, _ = client.probe_rest()
        if rest_ok:
            return _rest_export(client, out_dir)

    if client.mcp_token:
        mcp_ok, _ = client.probe_mcp()
        if mcp_ok:
            return _mcp_export(client, out_dir)

    _print_json(
        {
            "error": "No se pudo exportar: falta token válido de REST o MCP.",
            "expected_env": ["N8N_URL", "N8N_REST_API_KEY o N8N_MCP_TOKEN (o N8N_API_KEY legacy)"],
        }
    )
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="n8n single-entry helper (MCP + REST).")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Validar tokens y conectividad.")

    list_p = sub.add_parser("list", help="Listar workflows.")
    list_p.add_argument("--limit", type=int, default=50)
    list_p.add_argument("--query", type=str, default=None)

    details_p = sub.add_parser("details", help="Ver detalle de un workflow.")
    details_p.add_argument("--workflow-id", required=True)

    export_p = sub.add_parser("export", help="Exportar workflows a JSON.")
    export_p.add_argument("--out", type=str, default=None)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    n8n_url = os.getenv("N8N_URL")
    if not n8n_url:
        _print_json({"error": "Falta N8N_URL en entorno."})
        return 1

    rest_key, mcp_token = _detect_tokens()
    client = N8NClient(n8n_url, rest_key, mcp_token)

    if args.command == "status":
        return cmd_status(client)
    if args.command == "list":
        return cmd_list(client, args.limit, args.query)
    if args.command == "details":
        return cmd_details(client, args.workflow_id)
    if args.command == "export":
        return cmd_export(client, args.out)

    _print_json({"error": "Comando no soportado."})
    return 1


if __name__ == "__main__":
    sys.exit(main())
