#!/usr/bin/env python3
"""Read the private NocoDB accesos catalog. Never prints secret values.

Usage:
  scripts/accesos status
  scripts/accesos list [--entorno X] [--servicio Y] [--clave Z] [--query texto]
  scripts/accesos get --clave UNIPILE_API_KEY [--entorno nextconvers-vps] --out /tmp/secret
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

NOCO_BASE = os.environ.get("NOCODB_BASE_URL", "https://mpa.parvusmedia.com").rstrip("/")
TABLE_ID = os.environ.get("NOCODB_ACCESOS_TABLE_ID", "m6956l2gfi8d96c")
UI_URL = (
    "https://mpa.parvusmedia.com/w1yr9d7k/pluyg9y6o3thd5o/"
    "m6956l2gfi8d96c/vwb7btk1zh9yc601/accesos-accesos"
)
TOKEN_HINT_FILES = [
    "/opt/apps/prospeccion-alarmas/.env",
    "/opt/apps/prospeccion-cde-salesnav/.env",
    "/opt/apps/prospeccion-consultoras/.env",
    "/opt/apps/prospeccion-usj-universidades/.env",
    "/opt/apps/movistar-parati/backend/.env",
    "/etc/linkedinreport/app.env",
]


def _print_json(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _request(token: str, method: str, path: str, payload: Any | None = None) -> tuple[int, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "xc-token": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(NOCO_BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"error": "http_error", "status": exc.code}
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, {"error": "url_error", "detail": str(exc)}


def _token_from_vps() -> str | None:
    remote = r"""
python3 - <<'PY'
import pathlib, re
files = %s
pat = re.compile(r'^(?:NOCODB_API_TOKEN|NOCODB_TOKEN)\s*=\s*(.*)$')
for p in files:
    path = pathlib.Path(p)
    if not path.is_file():
        continue
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        continue
    for line in text.splitlines():
        m = pat.match(line.strip())
        if not m:
            continue
        val = m.group(1).strip().strip('"').strip("'")
        if val and len(val) > 8:
            print(val)
            raise SystemExit(0)
raise SystemExit(1)
PY
""" % json.dumps(TOKEN_HINT_FILES)
    try:
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "parvus-vps", "bash", "-s"],
            input=remote,
            text=True,
            capture_output=True,
            timeout=25,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    token = (proc.stdout or "").strip().splitlines()
    return token[-1] if token else None


def resolve_token() -> str | None:
    env = (os.environ.get("NOCODB_API_TOKEN") or os.environ.get("NOCODB_TOKEN") or "").strip()
    if env:
        return env
    marker = Path("/tmp/noco_token_path")
    if marker.is_file():
        try:
            return Path(marker.read_text().strip()).read_text().strip()
        except OSError:
            pass
    return _token_from_vps()


def fetch_all(token: str, fields: str) -> tuple[int, list[dict[str, Any]]]:
    out: list[dict[str, Any]] = []
    offset = 0
    while True:
        qs = urllib.parse.urlencode({"limit": 100, "offset": offset, "fields": fields})
        status, body = _request(token, "GET", f"/api/v2/tables/{TABLE_ID}/records?{qs}")
        if status >= 400 or not isinstance(body, dict):
            return status, []
        chunk = body.get("list") or []
        out.extend(chunk)
        info = body.get("pageInfo") or {}
        if info.get("isLastPage", True) or not chunk:
            break
        offset += len(chunk)
    return 200, out


def cmd_status() -> int:
    token = resolve_token()
    if not token:
        _print_json(
            {
                "ok": False,
                "error": "Sin NOCODB_API_TOKEN. Prueba ssh parvus-vps o exporta el secret.",
                "ui": UI_URL,
                "table_id": TABLE_ID,
            }
        )
        return 1
    status, rows = fetch_all(token, "Id,Title,Entorno,Servicio,Clave")
    if status != 200:
        _print_json({"ok": False, "http": status, "table_id": TABLE_ID})
        return 1
    entornos = sorted({str(r.get("Entorno") or "") for r in rows if r.get("Entorno")})
    servicios = sorted({str(r.get("Servicio") or "") for r in rows if r.get("Servicio")})
    _print_json(
        {
            "ok": True,
            "base": NOCO_BASE,
            "table_id": TABLE_ID,
            "ui": UI_URL,
            "rows": len(rows),
            "entornos": entornos,
            "servicios": servicios,
            "token_source": "env" if os.environ.get("NOCODB_API_TOKEN") else "bootstrap",
        }
    )
    return 0


def _match(row: dict[str, Any], entorno: str | None, servicio: str | None, clave: str | None, query: str | None) -> bool:
    if entorno and str(row.get("Entorno") or "").lower() != entorno.lower():
        return False
    if servicio and str(row.get("Servicio") or "").lower() != servicio.lower():
        return False
    if clave and str(row.get("Clave") or "").lower() != clave.lower():
        return False
    if query:
        blob = " ".join(str(row.get(k) or "") for k in ("Title", "Entorno", "Servicio", "Clave", "Fuente", "URL", "Notas"))
        if query.lower() not in blob.lower():
            return False
    return True


def cmd_list(entorno: str | None, servicio: str | None, clave: str | None, query: str | None) -> int:
    token = resolve_token()
    if not token:
        _print_json({"ok": False, "error": "Sin NOCODB_API_TOKEN"})
        return 1
    status, rows = fetch_all(token, "Id,Title,Entorno,Servicio,Clave,URL,Fuente,Notas")
    if status != 200:
        _print_json({"ok": False, "http": status})
        return 1
    filtered = [r for r in rows if _match(r, entorno, servicio, clave, query)]
    safe = [
        {
            "Id": r.get("Id"),
            "Title": r.get("Title"),
            "Entorno": r.get("Entorno"),
            "Servicio": r.get("Servicio"),
            "Clave": r.get("Clave"),
            "URL": r.get("URL"),
            "Fuente": r.get("Fuente"),
            "Notas": r.get("Notas"),
        }
        for r in filtered
    ]
    _print_json({"ok": True, "count": len(safe), "rows": safe})
    return 0


def cmd_get(clave: str, entorno: str | None, servicio: str | None, out: str) -> int:
    token = resolve_token()
    if not token:
        _print_json({"ok": False, "error": "Sin NOCODB_API_TOKEN"})
        return 1
    status, rows = fetch_all(token, "Id,Title,Entorno,Servicio,Clave,Valor,URL,Fuente,Notas")
    if status != 200:
        _print_json({"ok": False, "http": status})
        return 1
    matches = [r for r in rows if _match(r, entorno, servicio, clave, None)]
    if not matches:
        _print_json({"ok": False, "error": "No hay filas", "clave": clave})
        return 1
    if len(matches) > 1 and not entorno and not servicio:
        _print_json(
            {
                "ok": False,
                "error": "Varias filas; pasa --entorno y/o --servicio",
                "matches": [
                    {"Id": r.get("Id"), "Title": r.get("Title"), "Entorno": r.get("Entorno"), "Servicio": r.get("Servicio")}
                    for r in matches
                ],
            }
        )
        return 1
    row = matches[0]
    dest = Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="accesos-", dir=str(dest.parent))
    os.close(fd)
    tmp_path = Path(tmp)
    tmp_path.write_text(str(row.get("Valor") or ""), encoding="utf-8")
    tmp_path.chmod(0o600)
    tmp_path.replace(dest)
    dest.chmod(0o600)
    _print_json(
        {
            "ok": True,
            "Id": row.get("Id"),
            "Title": row.get("Title"),
            "Entorno": row.get("Entorno"),
            "Servicio": row.get("Servicio"),
            "Clave": row.get("Clave"),
            "URL": row.get("URL"),
            "Fuente": row.get("Fuente"),
            "out": str(dest),
            "bytes": dest.stat().st_size,
        }
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Catalogo privado de accesos (NocoDB). No imprime secretos.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Comprobar token y recuento.")
    list_p = sub.add_parser("list", help="Listar filas sin el campo Valor.")
    list_p.add_argument("--entorno")
    list_p.add_argument("--servicio")
    list_p.add_argument("--clave")
    list_p.add_argument("--query")
    get_p = sub.add_parser("get", help="Escribir un secreto a un archivo 0600.")
    get_p.add_argument("--clave", required=True)
    get_p.add_argument("--entorno")
    get_p.add_argument("--servicio")
    get_p.add_argument("--out", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "status":
        return cmd_status()
    if args.command == "list":
        return cmd_list(args.entorno, args.servicio, args.clave, args.query)
    if args.command == "get":
        return cmd_get(args.clave, args.entorno, args.servicio, args.out)
    _print_json({"error": "Comando no soportado."})
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
