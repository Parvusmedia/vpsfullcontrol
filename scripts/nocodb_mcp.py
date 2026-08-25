#!/usr/bin/env python3
"""Single-entry NocoDB MCP helper for Cloud Agents and local CLI.

Usage examples:
  python3 scripts/nocodb_mcp.py status
  python3 scripts/nocodb_mcp.py tools
  python3 scripts/nocodb_mcp.py base
  python3 scripts/nocodb_mcp.py tables
  python3 scripts/nocodb_mcp.py schema --table-id <id>
  python3 scripts/nocodb_mcp.py query --table-id <id> --page-size 10
  python3 scripts/nocodb_mcp.py call --name queryRecords --args '{"tableId":"..."}'
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PROTOCOL = "2025-06-18"


def _print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def _parse_mcp_body(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return {}
    if "data:" in raw:
        datas = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
        joined = "\n".join(part for part in datas if part)
        if joined:
            try:
                return json.loads(joined)
            except json.JSONDecodeError:
                return {"raw": joined}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw[:1000]}


def _unwrap_tool_result(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    if "error" in data and data.get("error"):
        return data
    result = data.get("result", data)
    if not isinstance(result, dict):
        return result
    if isinstance(result.get("structuredContent"), dict):
        return result["structuredContent"]
    content = result.get("content")
    if isinstance(content, list):
        text_parts = [
            entry.get("text", "")
            for entry in content
            if isinstance(entry, dict) and entry.get("type") == "text"
        ]
        merged = "\n".join(part for part in text_parts if part)
        if merged:
            try:
                return json.loads(merged)
            except json.JSONDecodeError:
                return {"text": merged}
    return result


class NocoDBMcpClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self.session_id: str | None = None

    def _request(self, payload: dict[str, Any]) -> tuple[int, Any]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "xc-mcp-token": self.token,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                session = response.headers.get("Mcp-Session-Id")
                if session:
                    self.session_id = session
                raw = response.read().decode("utf-8", errors="replace")
                return response.status, _parse_mcp_body(raw)
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8", errors="replace")
                data = _parse_mcp_body(raw) if raw else {}
            except Exception:  # pragma: no cover - defensive
                data = {"error": "http_error", "status": exc.code}
            return exc.code, data
        except urllib.error.URLError as exc:
            return 0, {"error": "url_error", "detail": str(exc)}

    def initialize(self) -> tuple[int, Any]:
        return self._request(
            {
                "jsonrpc": "2.0",
                "id": "init-1",
                "method": "initialize",
                "params": {
                    "protocolVersion": DEFAULT_PROTOCOL,
                    "capabilities": {},
                    "clientInfo": {"name": "nocodb-mcp-helper", "version": "1.0.0"},
                },
            }
        )

    def tools_list(self) -> tuple[int, Any]:
        return self._request(
            {"jsonrpc": "2.0", "id": "tools-list-1", "method": "tools/list", "params": {}}
        )

    def tool_call(self, name: str, arguments: dict[str, Any] | None = None) -> tuple[int, Any]:
        status, data = self._request(
            {
                "jsonrpc": "2.0",
                "id": f"tool-{name}",
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }
        )
        if status != 200:
            return status, data
        return status, _unwrap_tool_result(data)

    def probe(self) -> tuple[bool, str, list[str]]:
        init_status, init_data = self.initialize()
        if init_status != 200:
            if init_status == 401:
                return False, "unauthorized", []
            if init_status == 0:
                return False, "unreachable", []
            return False, f"http_{init_status}", []

        list_status, list_data = self.tools_list()
        if list_status != 200:
            return False, f"tools_list_http_{list_status}", []
        tools = []
        if isinstance(list_data, dict):
            result = list_data.get("result", {})
            if isinstance(result, dict) and isinstance(result.get("tools"), list):
                tools = [t.get("name") for t in result["tools"] if isinstance(t, dict) and t.get("name")]
        if not tools:
            return False, "no_tools", []
        server = {}
        if isinstance(init_data, dict):
            result = init_data.get("result", {})
            if isinstance(result, dict):
                server = result.get("serverInfo") or {}
        label = "ok"
        if isinstance(server, dict) and server.get("name"):
            label = f"ok:{server.get('name')}"
        return True, label, tools


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_mcp_json() -> tuple[str | None, str | None]:
    path = _repo_root() / ".cursor" / "mcp.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        return None, None
    for server in servers.values():
        if not isinstance(server, dict):
            continue
        url = server.get("url")
        headers = server.get("headers") if isinstance(server.get("headers"), dict) else {}
        token = headers.get("xc-mcp-token")
        if isinstance(url, str) and url.startswith("http") and isinstance(token, str) and token and "${" not in token:
            return url, token
    return None, None


def _require_client() -> NocoDBMcpClient | None:
    url = os.getenv("NOCODB_MCP_URL")
    token = os.getenv("NOCODB_MCP_TOKEN")
    file_url, file_token = _load_mcp_json()
    url = url or file_url
    token = token or file_token
    missing = [name for name, value in (("NOCODB_MCP_URL", url), ("NOCODB_MCP_TOKEN", token)) if not value]
    if missing:
        _print_json(
            {
                "error": "Faltan URL o token de NocoDB MCP.",
                "missing": missing,
                "hint": "Usa .cursor/mcp.json o secrets NOCODB_MCP_URL / NOCODB_MCP_TOKEN.",
            }
        )
        return None
    return NocoDBMcpClient(url, token)


def cmd_status(client: NocoDBMcpClient) -> int:
    ok, result, tools = client.probe()
    token_source = "env" if os.getenv("NOCODB_MCP_TOKEN") else "mcp.json"
    _print_json(
        {
            "nocodb_mcp_url": client.url,
            "token": "set",
            "token_source": token_source,
            "probe": {"ok": ok, "result": result},
            "tool_count": len(tools),
            "tools": tools,
        }
    )
    return 0 if ok else 1


def cmd_tools(client: NocoDBMcpClient) -> int:
    status, data = client.tools_list()
    if status != 200:
        _print_json({"error": "Fallo tools/list", "status": status, "payload": data})
        return 1
    result = data.get("result", data) if isinstance(data, dict) else data
    tools = result.get("tools", []) if isinstance(result, dict) else []
    summary = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        schema = tool.get("inputSchema") or {}
        summary.append(
            {
                "name": tool.get("name"),
                "description": tool.get("description"),
                "required": schema.get("required") or [],
                "properties": list((schema.get("properties") or {}).keys()),
            }
        )
    _print_json({"count": len(summary), "tools": summary})
    return 0


def _tool_cmd(client: NocoDBMcpClient, name: str, arguments: dict[str, Any] | None = None) -> int:
    status, payload = client.tool_call(name, arguments)
    if status != 200:
        _print_json({"error": f"Fallo {name}", "status": status, "payload": payload})
        return 1
    _print_json({"ok": True, "tool": name, "data": payload})
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NocoDB MCP helper (HTTP, not mcp-remote).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Validar token y listar tools MCP.")
    sub.add_parser("tools", help="Listar tools y sus argumentos.")
    sub.add_parser("base", help="getBaseInfo")
    sub.add_parser("tables", help="getTablesList")

    schema_p = sub.add_parser("schema", help="getTableSchema")
    schema_p.add_argument("--table-id", required=True)

    query_p = sub.add_parser("query", help="queryRecords")
    query_p.add_argument("--table-id", required=True)
    query_p.add_argument("--page", type=int, default=None)
    query_p.add_argument("--page-size", type=int, default=None)
    query_p.add_argument("--where", default=None)
    query_p.add_argument("--sort", default=None)
    query_p.add_argument("--fields", default=None)

    get_p = sub.add_parser("get", help="getRecord")
    get_p.add_argument("--table-id", required=True)
    get_p.add_argument("--record-id", required=True)
    get_p.add_argument("--fields", default=None)

    count_p = sub.add_parser("count", help="countRecords")
    count_p.add_argument("--table-id", required=True)
    count_p.add_argument("--where", default=None)

    call_p = sub.add_parser("call", help="Llamar cualquier tool MCP por nombre.")
    call_p.add_argument("--name", required=True)
    call_p.add_argument("--args", default="{}", help="JSON object con argumentos")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = _require_client()
    if client is None:
        return 1

    if args.command == "status":
        return cmd_status(client)
    if args.command == "tools":
        return cmd_tools(client)
    if args.command == "base":
        return _tool_cmd(client, "getBaseInfo")
    if args.command == "tables":
        return _tool_cmd(client, "getTablesList")
    if args.command == "schema":
        return _tool_cmd(client, "getTableSchema", {"tableId": args.table_id})
    if args.command == "query":
        payload: dict[str, Any] = {"tableId": args.table_id}
        if args.page is not None:
            payload["page"] = args.page
        if args.page_size is not None:
            payload["pageSize"] = args.page_size
        if args.where:
            payload["where"] = args.where
        if args.sort:
            payload["sort"] = args.sort
        if args.fields:
            payload["fields"] = args.fields
        return _tool_cmd(client, "queryRecords", payload)
    if args.command == "get":
        payload = {"tableId": args.table_id, "recordId": args.record_id}
        if args.fields:
            payload["fields"] = args.fields
        return _tool_cmd(client, "getRecord", payload)
    if args.command == "count":
        payload = {"tableId": args.table_id}
        if args.where:
            payload["where"] = args.where
        return _tool_cmd(client, "countRecords", payload)
    if args.command == "call":
        try:
            arguments = json.loads(args.args)
        except json.JSONDecodeError:
            _print_json({"error": "--args debe ser JSON válido."})
            return 1
        if not isinstance(arguments, dict):
            _print_json({"error": "--args debe ser un objeto JSON."})
            return 1
        return _tool_cmd(client, args.name, arguments)

    _print_json({"error": "Comando no soportado."})
    return 1


if __name__ == "__main__":
    sys.exit(main())
