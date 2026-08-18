from __future__ import annotations

from typing import Any

from .catalogue import programme_by_id, programmes
from .eligibility import classify


def _facts(programme: dict[str, Any]) -> str:
    return " ".join(programme.get("approved_facts") or [])


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
        return {"answer": "Ask anything about modality, background, or why this programme was suggested.", "source": "catalogue"}

    if "combine" in q or "work" in q or "job" in q and "with work" in q:
        if programme and (programme.get("work_compatible") or str(programme.get("modality")).lower() == "hybrid"):
            return {
                "answer": f"{programme['name']} is listed as {programme['modality']} in the catalogue, which can make it easier to combine with work. An advisor confirms the current timetable.",
                "source": "catalogue",
            }
        if programme:
            return {
                "answer": f"{programme['name']} is listed as {programme['modality']}. Combining it with a full-time job may be harder. An advisor can confirm options.",
                "source": "catalogue",
            }

    if "business" in q and ("ai" in q or "artificial" in q):
        ai = programme_by_id("ai-applied")
        elig = classify({"education": "business administration"}, "ai-applied")
        extra = " Foundation / levelling modules are possible according to the catalogue." if ai and ai.get("foundation_modules_possible") else ""
        return {
            "answer": f"Business Administration is not a preferred STEM background for Applied Artificial Intelligence. Status: {elig['status']}.{extra} An advisor must review eligibility — this ad cannot admit anyone.",
            "source": "catalogue",
        }

    if "technical" in q:
        if programme:
            tech = "It is a technical programme." if programme.get("technical") else "It is not positioned as a highly technical STEM programme."
            return {"answer": f"{tech} {_facts(programme)}", "source": "catalogue"}

    if "why" in q or "recommend" in q:
        reasons = (recommendation or {}).get("reasons") or []
        if reasons:
            return {
                "answer": "We recommended it because: " + "; ".join(reasons) + ". Reasons come from the match engine, not from promises about salary or admission.",
                "source": "match-engine",
            }

    if "difference" in q or "between" in q:
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
                    f"{a['name']} is {a['modality']}, focused on {', '.join(a['areas'][:3])}. "
                    f"{b['name']} is {b['modality']}, focused on {', '.join(b['areas'][:3])}. "
                    "Both are 60 ECTS in this demo catalogue."
                ),
                "source": "catalogue",
            }

    if programme:
        return {
            "answer": f"From the approved catalogue: {_facts(programme)} I can only use these facts — for anything else, talk to an USJ advisor.",
            "source": "catalogue",
        }
    return {
        "answer": "I can only answer from the three demo programmes. An USJ advisor can help if you want to explore the wider catalogue.",
        "source": "catalogue",
    }
