#!/usr/bin/env python3
"""Backfill Facturas sheet from Holded API (September, Havas contacts).

Does not send email. Rows mimic webhook approve state for issued (non-draft) invoices.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path

HOLDED_ENV = Path("/opt/apps/private/cde/holded.env")
CONTACT_IDS = frozenset(
    {
        "6023ce4a0a356d6caf64b163",
        "653f9fdfa0105e3d910cbbe7",
    }
)
YEAR_MONTH = os.environ.get("HOLDED_BACKFILL_MONTH", "2026-09")


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = HOLDED_ENV
    if not path.is_file():
        raise SystemExit(f"Missing {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def _fetch_invoices(api_key: str) -> list[dict]:
    items: list[dict] = []
    cursor: str | None = None
    while True:
        url = "https://api.holded.com/api/v2/invoices?limit=100"
        if cursor:
            url += f"&cursor={urllib.parse.quote(cursor)}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
        batch = payload.get("items") or []
        items.extend(batch)
        if not payload.get("has_more"):
            break
        cursor = payload.get("cursor")
        if not cursor:
            break
    return items


def _line_summary(lines: list) -> str:
    parts: list[str] = []
    for line in lines or []:
        if not isinstance(line, dict):
            continue
        text = (line.get("name") or line.get("description") or "").strip()
        if text:
            parts.append(text)
    return "; ".join(parts)


def _row_from_invoice(inv: dict) -> dict[str, str]:
    tags = inv.get("tags") or []
    tags_s = ";".join(tags) if isinstance(tags, list) else str(tags)
    approved = inv.get("approved_at") or ""
    draft = bool(inv.get("draft"))
    estado = "borrador" if draft else "aprobada"
    email_estado = ""
    if not draft:
        email_estado = "pendiente"
    return {
        "invoice_id": str(inv.get("id") or ""),
        "numero": str(inv.get("document_number") or ""),
        "fecha": str(inv.get("date") or ""),
        "vencimiento": str(inv.get("due_date") or ""),
        "estado": estado,
        "total": str(inv.get("total") or ""),
        "moneda": str(inv.get("currency") or ""),
        "tags_factura": tags_s,
        "lineas_resumen": _line_summary(inv.get("lines") or []),
        "contact_id": str(inv.get("contact_id") or ""),
        "creada_en": str(inv.get("date") or "") + "T00:00:00Z" if inv.get("date") else "",
        "aprobada_en": approved if approved else ("" if draft else str(inv.get("date") or "") + "T00:00:00Z"),
        "email_estado": email_estado,
        "destinatarios": "",
        "ultimo_error": "",
    }


def main() -> int:
    env = _load_env()
    api_key = env.get("HOLDED_API_KEY") or os.environ.get("HOLDED_API_KEY")
    if not api_key:
        raise SystemExit("HOLDED_API_KEY missing")

    all_inv = _fetch_invoices(api_key)
    selected: list[dict] = []
    for inv in all_inv:
        cid = inv.get("contact_id")
        if cid not in CONTACT_IDS:
            continue
        date = str(inv.get("date") or "")
        if not date.startswith(YEAR_MONTH):
            continue
        if inv.get("draft"):
            continue
        selected.append(inv)

    selected.sort(key=lambda x: (x.get("date") or "", x.get("document_number") or ""))
    rows = [_row_from_invoice(i) for i in selected]

    out_path = Path(os.environ.get("OUT", "/tmp/holded-sept-rows.json"))
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    tsv_path = out_path.with_suffix(".tsv")
    cols = [
        "invoice_id", "numero", "fecha", "vencimiento", "estado", "total", "moneda",
        "tags_factura", "lineas_resumen", "contact_id", "creada_en", "aprobada_en",
        "email_estado", "destinatarios", "ultimo_error",
    ]
    tsv_lines = ["\t".join(cols)]
    for r in rows:
        tsv_lines.append("\t".join(r.get(c, "") for c in cols))
    tsv_path.write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")
    print(json.dumps({"month": YEAR_MONTH, "count": len(rows), "out": str(out_path), "tsv": str(tsv_path)}, indent=2))
    for r in rows:
        print(f"- {r['numero'] or r['invoice_id'][:8]} | {r['tags_factura']} | {r['total']} {r['moneda']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
