#!/usr/bin/env python3
"""Hogar Finanzas API (stdlib). Misma semántica que public/api/*.php."""
from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DEFAULT_CATEGORIES = [
    "Alimentación",
    "Hogar y suministros",
    "Transporte",
    "Salud",
    "Ocio",
    "Suscripciones",
    "Educación",
    "Ropa",
    "Finanzas",
    "Otros",
]

DEFAULT_RULES = [
    {"pattern": "mercadona|carrefour|consum|lidl|aldi|eroski", "category": "Alimentación", "tags": []},
    {"pattern": "netflix|spotify|hbo|disney|amazon prime", "category": "Suscripciones", "tags": []},
    {"pattern": "repsol|cepsa|petroprix|uber|cabify|renfe|emt|metro", "category": "Transporte", "tags": []},
]


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def env_path() -> Path:
    p = os.environ.get("HOME_FINANCE_ENV")
    if p:
        return Path(p)
    return Path("/opt/apps/private/home-finance/app.env")


def data_dir() -> Path:
    d = os.environ.get("HOME_FINANCE_DATA_DIR")
    if d:
        return Path(d)
    return Path("/opt/apps/private/home-finance/data")


def api_token() -> str:
    return os.environ.get("HOME_FINANCE_API_TOKEN", "")


def default_store() -> dict[str, Any]:
    return {
        "transactions": [],
        "rules": list(DEFAULT_RULES),
        "categories": list(DEFAULT_CATEGORIES),
        "budgets": {},
    }


def read_store() -> dict[str, Any]:
    path = data_dir() / "store.json"
    if not path.is_file():
        return default_store()
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return default_store()
        base = default_store()
        base.update(data)
        return base
    except json.JSONDecodeError:
        return default_store()


def write_store(store: dict[str, Any]) -> None:
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / "store.json"
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(store, ensure_ascii=False, indent=2))
    tmp.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def tx_id(row: dict[str, Any]) -> str:
    parts = [str(row.get("date", "")), str(row.get("concept", "")), str(row.get("amount", "")), str(row.get("account", ""))]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def month_key(date: str) -> str:
    m = re.match(r"^(\d{4}-\d{2})", date)
    return f"{m.group(1)}-{m.group(2)}" if m else ""


def normalize_concept(s: str) -> str:
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s


def apply_rules(tx: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
    cat = tx.get("category") or ""
    if cat and cat != "Otros":
        return tx
    concept = normalize_concept(str(tx.get("concept", "")))
    for rule in rules:
        pattern = str(rule.get("pattern", ""))
        category = str(rule.get("category", ""))
        if not pattern or not category:
            continue
        if re.search(pattern, concept, re.I):
            tx["category"] = category
            tags = tx.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            extra = rule.get("tags") or []
            if isinstance(extra, list):
                tx["tags"] = list(dict.fromkeys([*tags, *[str(t) for t in extra]]))
            break
    if not tx.get("category"):
        tx["category"] = "Otros"
    return tx


class Handler(BaseHTTPRequestHandler):
    server_version = "HomeFinanceAPI/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _auth(self) -> bool:
        expected = api_token()
        if not expected:
            self._json(503, {"error": "server_not_configured"})
            return False
        given = self.headers.get("X-Home-Token", "")
        if given != expected:
            self._json(401, {"error": "unauthorized"})
            return False
        return True

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/health.php" or path == "/api/health":
            configured = bool(api_token())
            d = data_dir()
            self._json(200, {"ok": True, "configured": configured, "data_dir_writable": d.exists() or os.access(d.parent, os.W_OK)})
            return
        if not self._auth():
            return
        if path in ("/api/store.php", "/api/store"):
            store = read_store()
            self._json(
                200,
                {
                    "categories": store["categories"],
                    "rules": store["rules"],
                    "budgets": store["budgets"],
                    "transaction_count": len(store["transactions"]),
                },
            )
            return
        if path.startswith("/api/transactions"):
            store = read_store()
            month = ""
            if "?" in self.path:
                qs = self.path.split("?", 1)[1]
                for part in qs.split("&"):
                    if part.startswith("month="):
                        month = part[6:]
            txs = store["transactions"]
            if month and re.match(r"^\d{4}-\d{2}$", month):
                txs = [t for t in txs if isinstance(t, dict) and t.get("month") == month]
            self._json(200, {"transactions": txs})
            return
        self._json(404, {"error": "not_found"})

    def do_PUT(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in ("/api/store.php", "/api/store") or not self._auth():
            if path in ("/api/store.php", "/api/store") and api_token():
                return
            if not api_token():
                return
            self._json(405, {"error": "method_not_allowed"})
            return
        body = self._read_json()
        store = read_store()
        if "categories" in body and isinstance(body["categories"], list):
            store["categories"] = [str(c) for c in body["categories"]]
        if "rules" in body and isinstance(body["rules"], list):
            store["rules"] = body["rules"]
        if "budgets" in body and isinstance(body["budgets"], dict):
            store["budgets"] = body["budgets"]
        write_store(store)
        self._json(200, {"ok": True})

    def do_PATCH(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in ("/api/transactions.php", "/api/transactions") or not self._auth():
            return
        body = self._read_json()
        tid = str(body.get("id", ""))
        if not tid:
            self._json(400, {"error": "missing_id"})
            return
        store = read_store()
        found = False
        for i, tx in enumerate(store["transactions"]):
            if not isinstance(tx, dict) or tx.get("id") != tid:
                continue
            if "category" in body:
                store["transactions"][i]["category"] = str(body["category"])
            if "tags" in body and isinstance(body["tags"], list):
                store["transactions"][i]["tags"] = [str(t) for t in body["tags"]]
            if "type" in body:
                store["transactions"][i]["type"] = str(body["type"])
            found = True
            break
        if not found:
            self._json(404, {"error": "not_found"})
            return
        write_store(store)
        self._json(200, {"ok": True})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if not self._auth():
            return
        if path in ("/api/import.php", "/api/import"):
            body = self._read_json()
            rows = body.get("rows")
            if not isinstance(rows, list):
                self._json(400, {"error": "missing_rows"})
                return
            store = read_store()
            existing = {str(t.get("id")) for t in store["transactions"] if isinstance(t, dict) and t.get("id")}
            added = skipped = 0
            for row in rows:
                if not isinstance(row, dict):
                    continue
                date = str(row.get("date", ""))
                concept = str(row.get("concept", "")).strip()
                amount = float(row.get("amount", 0) or 0)
                if not date or not concept:
                    continue
                tx: dict[str, Any] = {
                    "date": date,
                    "concept": concept,
                    "amount": amount,
                    "account": str(row.get("account", "")).strip(),
                    "type": str(row.get("type") or ("ingreso" if amount >= 0 else "gasto")),
                    "category": str(row.get("category", "")).strip(),
                    "tags": row.get("tags") if isinstance(row.get("tags"), list) else [],
                    "month": month_key(date),
                }
                tx = apply_rules(tx, store["rules"])
                i = tx_id(tx)
                if i in existing:
                    skipped += 1
                    continue
                tx["id"] = i
                store["transactions"].append(tx)
                existing.add(i)
                added += 1
            write_store(store)
            self._json(200, {"ok": True, "added": added, "skipped": skipped, "total": len(store["transactions"])})
            return
        if path in ("/api/sheet.php", "/api/sheet"):
            body = self._read_json()
            url = str(body.get("url", "")).strip()
            if not url:
                self._json(400, {"error": "missing_url"})
                return
            if not re.match(r"^https://(docs\.google\.com|drive\.google\.com)", url, re.I):
                self._json(400, {"error": "invalid_url"})
                return
            fetch_url = url
            if "/edit" in fetch_url:
                fetch_url = re.sub(r"/edit.*", "/export?format=csv", fetch_url)
            ctx = ssl.create_default_context()
            try:
                with urllib.request.urlopen(fetch_url, context=ctx, timeout=20) as resp:
                    csv = resp.read().decode("utf-8", errors="replace")
            except Exception:
                self._json(502, {"error": "fetch_failed"})
                return
            lines = [ln for ln in csv.strip().splitlines() if ln.strip()]
            if len(lines) < 2:
                self._json(400, {"error": "empty_sheet"})
                return
            delim = ";" if ";" in lines[0] else ","
            header = [h.strip() for h in lines[0].split(delim)]
            rows_out = []
            for line in lines[1:]:
                cols = [c.strip().strip('"') for c in line.split(delim)]
                rows_out.append({header[i]: (cols[i] if i < len(cols) else "") for i in range(len(header))})
            self._json(200, {"ok": True, "rows": rows_out, "headers": header})
            return
        self._json(404, {"error": "not_found"})


def main() -> None:
    load_env(env_path())
    host = os.environ.get("HOME_FINANCE_BIND", "127.0.0.1")
    port = int(os.environ.get("HOME_FINANCE_PORT", "8791"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Home Finance API on http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
