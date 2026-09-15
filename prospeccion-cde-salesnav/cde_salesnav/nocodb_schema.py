"""Clone NocoDB columns from prospecting_es_formacion into cde_salesnav."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import CdeConfig

logger = logging.getLogger(__name__)

_SYSTEM_TITLES = {
    "Id",
    "CreatedAt",
    "UpdatedAt",
    "nc_created_by",
    "nc_updated_by",
    "nc_order",
    "nc_row_meta",
    "Title",
}

_EXTRA_COLUMNS: list[dict[str, Any]] = [
    {"title": "premium", "uidt": "Checkbox"},
    {"title": "open_profile", "uidt": "Checkbox"},
    {"title": "industry", "uidt": "SingleLineText"},
    {"title": "public_identifier", "uidt": "SingleLineText"},
    {"title": "query_geo", "uidt": "SingleLineText"},
    {"title": "country", "uidt": "SingleLineText"},
    {"title": "city", "uidt": "SingleLineText"},
    {"title": "source", "uidt": "SingleLineText"},
    {"title": "icepeas_status", "uidt": "SingleLineText"},
    {"title": "company_size", "uidt": "SingleLineText"},
]


def _headers(cfg: CdeConfig) -> dict[str, str]:
    return {
        "xc-token": cfg.nocodb_api_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def fetch_table_meta(*, cfg: CdeConfig, table_id: str) -> dict[str, Any]:
    resp = httpx.get(
        f"{cfg.nocodb_base_url}/api/v2/meta/tables/{table_id}",
        headers=_headers(cfg),
        timeout=45,
    )
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}


def _create_payload(col: dict[str, Any]) -> dict[str, Any]:
    uidt = col.get("uidt") or "SingleLineText"
    payload: dict[str, Any] = {
        "title": col["title"],
        "column_name": col.get("column_name") or col["title"],
        "uidt": uidt,
    }
    if col.get("cdf") not in (None, ""):
        payload["cdf"] = col["cdf"]
    options = col.get("options")
    if uidt == "SingleSelect":
        if options:
            payload["colOptions"] = {
                "options": [
                    {"title": o["title"], "color": o.get("color") or "#6c757d"}
                    for o in options
                    if o.get("title")
                ]
            }
        elif col.get("dtxp"):
            payload["dtxp"] = col["dtxp"]
    return payload


def _slim_ref_column(col: dict[str, Any]) -> dict[str, Any] | None:
    title = col.get("title")
    if not title or title in _SYSTEM_TITLES or col.get("system"):
        return None
    slim: dict[str, Any] = {
        "title": title,
        "column_name": col.get("column_name") or title,
        "uidt": col.get("uidt") or "SingleLineText",
        "cdf": col.get("cdf"),
        "dtxp": col.get("dtxp"),
    }
    col_options = col.get("colOptions") or {}
    opts = col_options.get("options") if isinstance(col_options, dict) else None
    if isinstance(opts, list):
        slim["options"] = [
            {"title": o.get("title"), "color": o.get("color")}
            for o in opts
            if isinstance(o, dict) and o.get("title")
        ]
    return slim


def ensure_schema(*, cfg: CdeConfig | None = None) -> dict[str, Any]:
    cfg = cfg or CdeConfig.from_env()
    if not cfg.nocodb_api_token:
        return {"ok": False, "error": "missing_nocodb_token"}

    ref = fetch_table_meta(cfg=cfg, table_id=cfg.nocodb_ref_table_id)
    dest = fetch_table_meta(cfg=cfg, table_id=cfg.nocodb_table_id)
    existing = {c.get("title") for c in (dest.get("columns") or []) if isinstance(c, dict)}

    wanted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for col in ref.get("columns") or []:
        if not isinstance(col, dict):
            continue
        slim = _slim_ref_column(col)
        if not slim or slim["title"] in seen:
            continue
        seen.add(slim["title"])
        wanted.append(slim)
    for extra in _EXTRA_COLUMNS:
        if extra["title"] not in seen:
            seen.add(extra["title"])
            wanted.append(extra)

    extra_status = {
        "discovered",
        "scored",
        "matched",
        "not_found",
        "hold",
        "contacted",
        "icypeas_ok",
        "icypeas_miss",
        "smartlead_queued",
        "smartlead_enrolled",
        "unipile_queued",
        "unipile_sent",
        "dropped",
    }
    for col in wanted:
        if col["title"] != "status":
            continue
        have = {o.get("title") for o in (col.get("options") or [])}
        for title in sorted(extra_status - have):
            col.setdefault("options", []).append({"title": title, "color": "#6c757d"})
        break

    created: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []
    for col in wanted:
        title = col["title"]
        if title in existing:
            skipped.append(title)
            continue
        payload = _create_payload(col)
        try:
            resp = httpx.post(
                f"{cfg.nocodb_base_url}/api/v2/meta/tables/{cfg.nocodb_table_id}/columns",
                headers=_headers(cfg),
                json=payload,
                timeout=45,
            )
            if resp.status_code >= 400:
                failed.append({"title": title, "error": (resp.text or "")[:240]})
                continue
            created.append(title)
            existing.add(title)
        except Exception as exc:
            logger.exception("create column failed title=%s", title)
            failed.append({"title": title, "error": str(exc)})

    dest_after = fetch_table_meta(cfg=cfg, table_id=cfg.nocodb_table_id)
    titles = [c.get("title") for c in (dest_after.get("columns") or []) if isinstance(c, dict)]
    return {
        "ok": not failed,
        "table_id": cfg.nocodb_table_id,
        "table_title": dest_after.get("title"),
        "ref_table_id": cfg.nocodb_ref_table_id,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "columns": [t for t in titles if t],
    }
