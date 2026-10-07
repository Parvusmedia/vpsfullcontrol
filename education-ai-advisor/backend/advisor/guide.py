from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import eligibility as eligibility_mod
from . import explainer as explainer_mod
from .catalogue import programme_by_id, public_programme
from .matcher import rank

GUIDE_PATH = Path(__file__).resolve().parent.parent / "data" / "guide.json"


@lru_cache(maxsize=1)
def guide_spec() -> dict[str, Any]:
    return json.loads(GUIDE_PATH.read_text(encoding="utf-8"))


def public_steps() -> dict[str, Any]:
    spec = guide_spec()
    steps = []
    for step in spec.get("steps") or []:
        steps.append(
            {
                "id": step["id"],
                "title": step["title"],
                "subtitle": step.get("subtitle", ""),
                "options": [
                    {
                        "id": o["id"],
                        "label": o["label"],
                        "short_label": o.get("short_label") or o["label"],
                    }
                    for o in step.get("options") or []
                ],
            }
        )
    intro = spec.get("intro_screen") or {}
    return {
        "intro": spec.get("intro", ""),
        "intro_screen": {
            "headline": intro.get("headline", "Find your programme in 3 steps"),
            "lede": intro.get("lede", spec.get("intro", "")),
            "outcome": intro.get("outcome", ""),
            "cta": intro.get("cta", "Empezar"),
            "compact_headline": intro.get("compact_headline", "Your programme in 3 taps"),
            "compact_lede": intro.get("compact_lede", ""),
        },
        "steps": steps,
    }


def _option(step_id: str, option_id: str) -> dict[str, Any] | None:
    for step in guide_spec().get("steps") or []:
        if step["id"] != step_id:
            continue
        for option in step.get("options") or []:
            if option["id"] == option_id:
                return option
    return None


def merge_answers(answers: dict[str, str]) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "education": None,
        "experience_years": None,
        "current_role": None,
        "interests": [],
        "goal": None,
        "constraints": [],
        "priority": None,
        "parser": "guide",
        "answers": dict(answers or {}),
    }
    boosts: dict[str, float] = {}
    eliminate: set[str] = set()
    labels: list[str] = []
    for step_id, option_id in (answers or {}).items():
        option = _option(step_id, option_id)
        if not option:
            continue
        labels.append(option["label"])
        blob = option.get("profile") or {}
        for key, value in blob.items():
            if key == "interests":
                for item in value:
                    if item not in profile["interests"]:
                        profile["interests"].append(item)
            elif key == "constraints":
                for item in value:
                    if item not in profile["constraints"]:
                        profile["constraints"].append(item)
            elif value not in (None, ""):
                profile[key] = value
        for pid, amount in (option.get("boosts") or {}).items():
            boosts[pid] = boosts.get(pid, 0.0) + float(amount)
        eliminate.update(option.get("eliminate") or [])
    profile["raw_message"] = " · ".join(labels)
    return {"profile": profile, "boosts": boosts, "eliminate": sorted(eliminate), "labels": labels}


def run_guide(answers: dict[str, str], debug: bool = False) -> dict[str, Any]:
    merged = merge_answers(answers)
    profile = merged["profile"]
    scored = rank(profile, extra_boosts=merged["boosts"])
    eliminated = set(merged["eliminate"])
    remaining = [row for row in scored if row["programme_id"] not in eliminated]
    dropped = [row for row in scored if row["programme_id"] in eliminated]
    for row in dropped:
        row["eliminated"] = True
    catalogue_limited = False
    if not remaining:
        remaining = scored[:2]
        dropped = []
        catalogue_limited = True
        eliminated = set()

    for row in remaining:
        elig = eligibility_mod.classify(profile, row["programme_id"])
        row["eligibility"] = elig["status"]
        row["eligibility_note"] = elig["note"]
        eligibility_mod.cap_score_for_status(row, elig["status"])
        programme = programme_by_id(row["programme_id"])
        if programme:
            row["programme_card"] = public_programme(programme)
            row["modality_es"] = public_programme(programme).get("modality_es")
        row["explanation"] = explainer_mod.explain(profile, row, elig)

    best = remaining[0] if remaining else None
    strong = bool(
        best
        and best["score"] >= 0.48
        and not catalogue_limited
        and best.get("eligibility") != eligibility_mod.REVIEW
    )
    payload: dict[str, Any] = {
        "profile": {k: v for k, v in profile.items() if k != "raw_message" or debug},
        "has_strong_match": strong,
        "catalogue_limited": catalogue_limited,
        "complete": len(answers or {}) >= len(guide_spec().get("steps") or []),
        "remaining": [
            {
                "programme_id": row["programme_id"],
                "programme": row["programme"],
                "score": row["score"],
                "score_pct": row["score_pct"],
                "eliminated": False,
            }
            for row in remaining
        ],
        "dropped": [
            {"programme_id": row["programme_id"], "programme": row["programme"]}
            for row in dropped
        ],
        "best": best,
        "alternatives": remaining[1:3],
        "guide_labels": merged["labels"],
    }
    if debug:
        payload["debug"] = {
            "boosts": merged["boosts"],
            "eliminate": merged["eliminate"],
            "all_scores": scored,
        }
        payload["profile"]["raw_message"] = profile.get("raw_message")
    return payload
