#!/usr/bin/env python3
"""Read the private NocoDB accesos catalog. Never prints secret values.

Usage:
  scripts/accesos status
  scripts/accesos list [--entorno X] [--servicio Y] [--clave Z] [--query texto]
  scripts/accesos get --clave UNIPILE_API_KEY [--entorno nextconvers-vps] --out /tmp/secret
  scripts/accesos seal [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Falta el paquete cryptography (pip install cryptography)") from exc

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
MASTER_KEY_REMOTE = os.environ.get(
    "ACCESOS_MASTER_KEY_REMOTE",
    "/opt/apps/private/accesos.master.key",
)
ENC_PREFIX = "enc:v1:"
ENC_AAD = b"parvus-accesos-v1"


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


def _ssh_parvus(script: str, timeout: int = 25) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "parvus-vps", "bash", "-s"],
        input=script,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


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
        proc = _ssh_parvus(remote)
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


def _aes_key(master: str) -> bytes:
    return hashlib.sha256(master.encode("utf-8")).digest()


def is_encrypted(value: str) -> bool:
    return value.startswith(ENC_PREFIX)


def encrypt_value(plaintext: str, master: str) -> str:
    nonce = os.urandom(12)
    blob = AESGCM(_aes_key(master)).encrypt(nonce, plaintext.encode("utf-8"), ENC_AAD)
    return ENC_PREFIX + base64.b64encode(nonce + blob).decode("ascii")


def decrypt_value(value: str, master: str | None) -> str:
    if not value or not is_encrypted(value):
        return value
    if not master:
        raise ValueError("Falta ACCESOS_MASTER_KEY para descifrar Valor")
    raw = base64.b64decode(value[len(ENC_PREFIX) :])
    if len(raw) < 13:
        raise ValueError("Ciphertext accesor corrupto")
    nonce, blob = raw[:12], raw[12:]
    try:
        return AESGCM(_aes_key(master)).decrypt(nonce, blob, ENC_AAD).decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - surface as decrypt failure
        raise ValueError("No se pudo descifrar Valor (clave maestra incorrecta o dato corrupto)") from exc


def _master_from_vps() -> str | None:
    remote = f"test -s {MASTER_KEY_REMOTE!s} && cat {MASTER_KEY_REMOTE!s}\n"
    try:
        proc = _ssh_parvus(remote)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    key = (proc.stdout or "").strip()
    return key or None


def resolve_master_key() -> tuple[str | None, str]:
    env = (os.environ.get("ACCESOS_MASTER_KEY") or "").strip()
    if env:
        return env, "env"
    path = (os.environ.get("ACCESOS_MASTER_KEY_FILE") or "").strip()
    if path:
        try:
            text = Path(path).read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        if text:
            return text, "file"
    local = Path("/tmp/accesos.master.key")
    if local.is_file():
        try:
            text = local.read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        if text:
            return text, "tmp"
    vps = _master_from_vps()
    if vps:
        return vps, "vps"
    return None, "missing"


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
    status, rows = fetch_all(token, "Id,Title,Entorno,Servicio,Clave,Valor")
    if status != 200:
        _print_json({"ok": False, "http": status, "table_id": TABLE_ID})
        return 1
    entornos = sorted({str(r.get("Entorno") or "") for r in rows if r.get("Entorno")})
    servicios = sorted({str(r.get("Servicio") or "") for r in rows if r.get("Servicio")})
    encrypted = sum(1 for r in rows if is_encrypted(str(r.get("Valor") or "")))
    plaintext = len(rows) - encrypted
    master, master_source = resolve_master_key()
    _print_json(
        {
            "ok": True,
            "base": NOCO_BASE,
            "table_id": TABLE_ID,
            "ui": UI_URL,
            "rows": len(rows),
            "encrypted_rows": encrypted,
            "plaintext_rows": plaintext,
            "encryption": ENC_PREFIX.rstrip(":"),
            "master_key": master_source if master else "missing",
            "master_key_path_vps": MASTER_KEY_REMOTE,
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
    status, rows = fetch_all(token, "Id,Title,Entorno,Servicio,Clave,Valor,URL,Fuente,Notas")
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
            "cifrado": is_encrypted(str(r.get("Valor") or "")),
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
    raw = str(row.get("Valor") or "")
    master, master_source = resolve_master_key()
    try:
        plaintext = decrypt_value(raw, master)
    except ValueError as exc:
        _print_json({"ok": False, "error": str(exc), "cifrado": is_encrypted(raw), "master_key": master_source})
        return 1
    dest = Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="accesos-", dir=str(dest.parent))
    os.close(fd)
    tmp_path = Path(tmp)
    tmp_path.write_text(plaintext, encoding="utf-8")
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
            "cifrado": is_encrypted(raw),
            "master_key": master_source if is_encrypted(raw) else "unused",
        }
    )
    return 0


def cmd_seal(dry_run: bool) -> int:
    token = resolve_token()
    master, master_source = resolve_master_key()
    if not token:
        _print_json({"ok": False, "error": "Sin NOCODB_API_TOKEN"})
        return 1
    if not master:
        _print_json(
            {
                "ok": False,
                "error": "Sin ACCESOS_MASTER_KEY. Genera /opt/apps/private/accesos.master.key en parvus-vps.",
            }
        )
        return 1
    status, rows = fetch_all(token, "Id,Title,Valor")
    if status != 200:
        _print_json({"ok": False, "http": status})
        return 1
    pending = [r for r in rows if str(r.get("Valor") or "") and not is_encrypted(str(r.get("Valor") or ""))]
    already = len(rows) - len(pending)
    if dry_run:
        _print_json(
            {
                "ok": True,
                "dry_run": True,
                "rows": len(rows),
                "already_encrypted": already,
                "would_encrypt": len(pending),
                "master_key": master_source,
            }
        )
        return 0
    updated = failed = 0
    for rec in pending:
        sealed = encrypt_value(str(rec.get("Valor") or ""), master)
        st, _body = _request(token, "PATCH", f"/api/v2/tables/{TABLE_ID}/records", {"Id": rec["Id"], "Valor": sealed})
        if st >= 400:
            failed += 1
        else:
            updated += 1
    _print_json(
        {
            "ok": failed == 0,
            "dry_run": False,
            "rows": len(rows),
            "already_encrypted": already,
            "encrypted_now": updated,
            "failed": failed,
            "master_key": master_source,
        }
    )
    return 0 if failed == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Catalogo privado de accesos (NocoDB). No imprime secretos.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Comprobar token, cifrado y recuento.")
    list_p = sub.add_parser("list", help="Listar filas sin el campo Valor.")
    list_p.add_argument("--entorno")
    list_p.add_argument("--servicio")
    list_p.add_argument("--clave")
    list_p.add_argument("--query")
    get_p = sub.add_parser("get", help="Descifrar un secreto a un archivo 0600.")
    get_p.add_argument("--clave", required=True)
    get_p.add_argument("--entorno")
    get_p.add_argument("--servicio")
    get_p.add_argument("--out", required=True)
    seal_p = sub.add_parser("seal", help="Cifrar filas Valor en claro con la clave maestra.")
    seal_p.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "status":
        return cmd_status()
    if args.command == "list":
        return cmd_list(args.entorno, args.servicio, args.clave, args.query)
    if args.command == "get":
        return cmd_get(args.clave, args.entorno, args.servicio, args.out)
    if args.command == "seal":
        return cmd_seal(args.dry_run)
    _print_json({"error": "Comando no soportado."})
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
