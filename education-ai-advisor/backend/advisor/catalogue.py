from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "programmes.json"


def _load_raw() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def catalogue() -> dict[str, Any]:
    return _load_raw()


def reload() -> dict[str, Any]:
    catalogue.cache_clear()
    return catalogue()


def programmes() -> list[dict[str, Any]]:
    return list(catalogue()["programmes"])


def programme_by_id(pid: str) -> dict[str, Any] | None:
    for item in programmes():
        if item["id"] == pid:
            return item
    return None


def weights() -> dict[str, float]:
    return dict(catalogue()["weights"])


def strong_match_threshold() -> float:
    return float(catalogue().get("strong_match_threshold", 0.48))


def public_programme(item: dict[str, Any]) -> dict[str, Any]:
    modality = item.get("modality")
    modality_label = "Hybrid" if str(modality).lower() == "hybrid" else "On campus"
    return {
        "id": item["id"],
        "name": item["name"],
        "official_name": item.get("official_name") or item["name"],
        "ects": item["ects"],
        "modality": modality,
        "modality_label": modality_label,
        "places": item["places"],
        "start_date": item.get("start_date"),
        "url": item.get("url"),
        "areas": item.get("areas", []),
        "ideal_profiles": item.get("ideal_profiles", []),
        "goals": item.get("goals", []),
        "foundation_modules_possible": bool(item.get("foundation_modules_possible")),
        "eligibility": item.get("eligibility", {}),
        "approved_facts": item.get("approved_facts", []),
    }
