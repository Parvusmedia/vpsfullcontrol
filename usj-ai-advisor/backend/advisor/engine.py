from __future__ import annotations

from typing import Any

from . import eligibility as eligibility_mod
from . import explainer as explainer_mod
from . import llm
from . import matcher
from . import parser as parser_mod
from . import qa as qa_mod
from .catalogue import programme_by_id, public_programme


def analyse_message(message: str, priority: str | None = None) -> dict[str, Any]:
    profile = parser_mod.parse_profile(message, priority=priority)
    llm_profile = llm.analyse_with_llm(message)
    if llm_profile:
        for key, value in llm_profile.items():
            if value not in (None, "", []):
                profile[key] = value
        profile["parser"] = "llm+rules"
    else:
        profile["parser"] = "mock"
    return profile


def recommend(message: str, priority: str | None = None, debug: bool = False) -> dict[str, Any]:
    profile = analyse_message(message, priority=priority)
    scored = matcher.rank(profile, priority=priority)
    split = matcher.split_matches(scored)
    best = split["best"]
    if best:
        elig = eligibility_mod.classify(profile, best["programme_id"])
        best = dict(best)
        best["eligibility"] = elig["status"]
        best["eligibility_note"] = elig["note"]
        programme = programme_by_id(best["programme_id"])
        context = {
            "reasons": best.get("reasons"),
            "facts": (programme or {}).get("approved_facts", []),
            "eligibility": elig,
            "programme": best["programme"],
        }
        best["explanation"] = llm.explain_with_llm(context) or explainer_mod.explain(profile, best, elig)
        if programme:
            best["programme_card"] = public_programme(programme)
        split["best"] = best
        for alt in split["alternatives"]:
            alt_el = eligibility_mod.classify(profile, alt["programme_id"])
            alt["eligibility"] = alt_el["status"]
    payload: dict[str, Any] = {
        "profile": {k: v for k, v in profile.items() if k != "raw_message" or debug},
        "has_strong_match": split["has_strong_match"],
        "best": split["best"],
        "alternatives": split["alternatives"],
        "ai_mode": llm.ai_mode(),
    }
    if debug:
        from .catalogue import weights

        payload["debug"] = {
            "all_scores": [
                {
                    "programme": row["programme"],
                    "id": row["programme_id"],
                    "score_pct": row["score_pct"],
                    "breakdown": row["breakdown"],
                    "reasons": row["reasons"],
                }
                for row in split["all"]
            ],
            "raw_message": profile.get("raw_message"),
            "weights": weights(),
        }
        payload["profile"]["raw_message"] = profile.get("raw_message")
    return payload


def ask(question: str, message: str, priority: str | None, recommendation: dict[str, Any] | None) -> dict[str, Any]:
    profile = analyse_message(message, priority=priority) if message else {}
    rec = recommendation
    if message and not rec:
        result = recommend(message, priority=priority)
        rec = result.get("best")
        alts = result.get("alternatives")
    else:
        alts = []
        if message:
            alts = recommend(message, priority=priority).get("alternatives") or []
    return qa_mod.answer_question(question, profile, rec, alts)
