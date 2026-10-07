from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache
from threading import Lock
from typing import Any

_lock = Lock()

DATA_DIR = Path(os.getenv("USJ_DATA_DIR") or Path(__file__).resolve().parent.parent / "storage")
LEADS_PATH = DATA_DIR / "leads.json"
EVENTS_PATH = DATA_DIR / "events.json"
DEMO_LEADS_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_leads.json"
_DEMO_BLOCKLIST = {"emiliano tichauer"}


@lru_cache(maxsize=1)
def _demo_leads() -> list[dict[str, Any]]:
    if not DEMO_LEADS_PATH.exists():
        return []
    try:
        payload = json.loads(DEMO_LEADS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def _blocked_lead(record: dict[str, Any]) -> bool:
    name = str(record.get("name") or "").strip().casefold()
    return name in _DEMO_BLOCKLIST


def _read(path: Path) -> list[Any]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write(path: Path, payload: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_lead(lead: dict[str, Any]) -> dict[str, Any]:
    record = dict(lead)
    record["id"] = record.get("id") or f"lead-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    with _lock:
        items = _read(LEADS_PATH)
        items.insert(0, record)
        _write(LEADS_PATH, items[:200])
    return record


def list_leads(limit: int = 50) -> list[dict[str, Any]]:
    demo_ids = {row.get("id") for row in _demo_leads()}
    with _lock:
        live = [
            row
            for row in _read(LEADS_PATH)
            if not row.get("demo_seed") and row.get("id") not in demo_ids and not _blocked_lead(row)
        ]
    merged = _demo_leads() + live
    return merged[:limit]


def append_event(event: dict[str, Any]) -> None:
    record = dict(event)
    record["at"] = datetime.now(timezone.utc).isoformat()
    with _lock:
        items = _read(EVENTS_PATH)
        items.append(record)
        _write(EVENTS_PATH, items[-500:])


def list_events(limit: int = 200) -> list[dict[str, Any]]:
    with _lock:
        return _read(EVENTS_PATH)[-limit:]
