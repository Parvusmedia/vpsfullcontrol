from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id, programmes
from .eligibility import classify


def _facts(programme: dict[str, Any]) -> str:
    return " ".join(programme.get("approved_facts") or [])


def _modality(programme: dict[str, Any]) -> str:
    raw = str(programme.get("modality") or "")
    if raw.lower() == "hybrid":
        return "hybrid"
    if "campus" in raw.lower() or "on campus" in raw.lower():
        return "on campus"
    return raw or "the catalogue modality"


def answer_question(
    question: str,
    profile: dict[str, Any],
    recommendation: dict[str, Any] | None,
    alternatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    q = (question or "").strip().lower()
    rec_id = (recommendation or {}).get("programme_id") or (recommendation or {}).get("programme")
    programme = programme_by_id(str(rec_id) if rec_id else "") if rec_id else None
    if programme is None and rec_id:
        for item in programmes():
            if item["name"].lower() == str(rec_id).lower() or item["id"] == rec_id:
                programme = item
                break
    if programme is None and recommendation:
        programme = programme_by_id("biomechanics") if "biomech" in str(recommendation).lower() else None

    if not q:
        return {"answer": "Ask about modality, access requirements or why this programme appears.", "source": "catalogue"}

    if "compatibil" in q or "trabajo" in q or "combine" in q or "work" in q:
        if programme and (programme.get("work_compatible") or str(programme.get("modality")).lower() == "hybrid"):
            return {
                "answer": (
                    f"{programme['name']} is listed as {_modality(programme)} in the catalogue, "
                    "which may help combine study with work. An advisor confirms the current schedule."
                ),
                "source": "catalogue",
            }
        if programme:
            return {
                "answer": (
                    f"{programme['name']} is listed as {_modality(programme)}. "
                    "Combining with full-time work may be harder. An advisor can confirm options."
                ),
                "source": "catalogue",
            }

    if ("business" in q or "ade" in q) and ("ai" in q or "artificial" in q or "intelligence" in q):
        ai = programme_by_id("ai-applied")
        elig = classify({"education": "business administration"}, "ai-applied")
        extra = (
            " The catalogue allows foundation modules if technical background is limited."
            if ai and ai.get("foundation_modules_possible")
            else ""
        )
        return {
            "answer": (
                "Business administration is not a preferred STEM profile for Applied AI. "
                f"Status: {elig['status']}.{extra} An advisor must review eligibility — this ad does not admit anyone."
            ),
            "source": "catalogue",
        }

    if "technical" in q or "tecnic" in q:
        if programme:
            tech = (
                "It is a technical programme."
                if programme.get("technical")
                else "It is not positioned as a highly technical STEM programme."
            )
            return {"answer": f"{tech} {_facts(programme)}", "source": "catalogue"}

    if "why" in q or "recommend" in q or "encaja" in q or "por qué" in q:
        reasons = (recommendation or {}).get("reasons") or []
        if reasons:
            return {
                "answer": (
                    "This option appears because: "
                    + "; ".join(reasons)
                    + ". Reasons come from the matching engine, not salary or admission promises."
                ),
                "source": "match-engine",
            }

    if "difference" in q or "between" in q or "diferencia" in q:
        names = []
        if programme:
            names.append(programme)
        for alt in (alternatives or [])[:2]:
            other = programme_by_id(alt.get("programme_id") or "")
            if other:
                names.append(other)
        if len(names) >= 2:
            a, b = names[0], names[1]
            return {
                "answer": (
                    f"{a['name']} is {_modality(a)}, focused on {', '.join(a['areas'][:3])}. "
                    f"{b['name']} is {_modality(b)}, focused on {', '.join(b['areas'][:3])}. "
                    "Both are 60 ECTS in this demo catalogue."
                ),
                "source": "catalogue",
            }

    if programme:
        return {
            "answer": (
                f"From the approved catalogue: {_facts(programme)} "
                "I only use these facts — for anything else, speak with an advisor."
            ),
            "source": "catalogue",
        }
    return {
        "answer": "I can only answer about the three programmes in this demo. An advisor can help with the wider catalogue.",
        "source": "catalogue",
    }
