from __future__ import annotations

from typing import Any

from .catalogue import programmes, strong_match_threshold, weights

PRIORITY_BOOSTS = {
    "Learn new technology": {"ai-applied": 0.08},
    "Specialization": {"biomechanics": 0.08, "ai-applied": 0.03},
    "Brand / communication career": {"marketing": 0.10},
    "Better job opportunities": {"ai-applied": 0.03, "marketing": 0.03, "biomechanics": 0.02},
    "Career change": {"marketing": 0.08, "ai-applied": 0.04},
    "Higher salary": {"ai-applied": 0.02, "marketing": 0.02},
    "Research": {"ai-applied": 0.07, "biomechanics": 0.04},
    "Combine study + work": {"ai-applied": 0.06, "biomechanics": 0.06, "marketing": -0.05},
}


def _tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        out: set[str] = set()
        for item in value:
            out |= _tokens(item)
        return out
    text = str(value).lower().replace("&", " ").replace("/", " ")
    stop = {"and", "the", "of", "a", "to", "in", "for"}
    return {t for t in text.replace("-", " ").split() if t and t not in stop}


def _overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = a & b
    if not inter:
        # light stem: physiotherap* / engineer*
        for left in a:
            for right in b:
                if len(left) >= 5 and (left.startswith(right[:5]) or right.startswith(left[:5])):
                    return 0.55
        return 0.0
    return min(1.0, len(inter) / max(1, min(len(a), 4)))


def _education_score(profile: dict[str, Any], programme: dict[str, Any]) -> tuple[float, list[str]]:
    edu = _tokens(profile.get("education"))
    preferred = _tokens(programme["eligibility"].get("preferred_backgrounds"))
    accepted = _tokens(programme["eligibility"].get("accepted_backgrounds"))
    ideal = _tokens(programme.get("ideal_profiles"))
    reasons: list[str] = []
    score = max(_overlap(edu, preferred) * 1.0, _overlap(edu, accepted) * 0.75, _overlap(edu, ideal) * 0.7)
    if score >= 0.7 and profile.get("education"):
        reasons.append(f"{str(profile['education']).title()} background")
    elif score >= 0.4 and profile.get("education"):
        reasons.append(f"Partial overlap with {programme['name']} entry profiles")
    return score, reasons


def _area_score(profile: dict[str, Any], programme: dict[str, Any]) -> tuple[float, list[str]]:
    hay = _tokens([profile.get("current_role"), profile.get("education"), profile.get("interests")])
    areas = _tokens(programme.get("areas") + programme.get("keywords", []))
    score = _overlap(hay, areas)
    reasons: list[str] = []
    if "sports" in (profile.get("interests") or []) and "sports" in areas:
        reasons.append("Sports experience")
        score = max(score, 0.85)
    if "movement analysis" in (profile.get("interests") or []) and "movement" in areas:
        reasons.append("Interest in movement analysis")
        score = max(score, 0.9)
    if any(k in hay for k in ("ai", "artificial", "intelligence")) and "intelligence" in areas:
        reasons.append("Interest in applying AI")
        score = max(score, 0.9)
    if any(k in hay for k in ("marketing", "brand", "communication")) and "marketing" in areas:
        reasons.append("Marketing and communication experience")
        score = max(score, 0.88)
    if any(k in hay for k in ("software", "developer", "engineering")) and "software" in areas:
        reasons.append("Software / technology profile")
        score = max(score, 0.88)
    return min(1.0, score), reasons


def _goal_score(profile: dict[str, Any], programme: dict[str, Any]) -> tuple[float, list[str]]:
    goal = _tokens(profile.get("goal"))
    goals = _tokens(programme.get("goals"))
    score = _overlap(goal, goals)
    reasons: list[str] = []
    g = (profile.get("goal") or "")
    if g == "specialization" and "specialization" in goals:
        reasons.append("Looking for specialization")
        score = max(score, 0.95)
    if g in ("learn AI", "AI specialization", "apply AI professionally") and "ai" in " ".join(programme.get("goals", [])).lower():
        reasons.append("Wants to apply AI professionally")
        score = max(score, 0.95)
    if g in ("marketing career", "career progression", "communication") and programme["id"] == "marketing":
        reasons.append("Career progression in marketing / communication")
        score = max(score, 0.9)
    if g == "career change" and programme["id"] == "marketing":
        score = max(score, 0.55)
    if g == "career change" and programme["id"] == "ai-applied" and profile.get("education") in (
        "software engineering", "computer science", "informatics", "data science"
    ):
        score = max(score, 0.4)
    return min(1.0, score), reasons


def _interest_score(profile: dict[str, Any], programme: dict[str, Any]) -> tuple[float, list[str]]:
    interests = _tokens(profile.get("interests"))
    areas = _tokens(programme.get("areas") + programme.get("keywords", []))
    score = _overlap(interests, areas)
    return score, []


def _modality_score(profile: dict[str, Any], programme: dict[str, Any]) -> tuple[float, list[str]]:
    constraints = profile.get("constraints") or []
    reasons: list[str] = []
    if "combine work and study" in constraints:
        if programme.get("work_compatible") or str(programme.get("modality", "")).lower() == "hybrid":
            reasons.append("Hybrid format may fit your situation")
            return 1.0, reasons
        reasons.append("On-campus format may be harder to combine with work")
        return 0.25, reasons
    return 0.6, reasons


def _experience_score(profile: dict[str, Any], programme: dict[str, Any]) -> tuple[float, list[str]]:
    years = profile.get("experience_years")
    if years is None:
        return 0.45, []
    if years >= 2:
        return 0.85, []
    return 0.55, []


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def score_programme(profile: dict[str, Any], programme: dict[str, Any], priority: str | None = None) -> dict[str, Any]:
    w = weights()
    edu_s, edu_r = _education_score(profile, programme)
    area_s, area_r = _area_score(profile, programme)
    goal_s, goal_r = _goal_score(profile, programme)
    int_s, int_r = _interest_score(profile, programme)
    mod_s, mod_r = _modality_score(profile, programme)
    exp_s, exp_r = _experience_score(profile, programme)

    breakdown = {
        "education": edu_s,
        "professional_area": area_s,
        "career_goal": goal_s,
        "interests": int_s,
        "modality": mod_s,
        "experience": exp_s,
    }
    total = sum(breakdown[k] * w[k] for k in w)
    boosts = PRIORITY_BOOSTS.get(priority or "", {})
    total += boosts.get(programme["id"], 0.0)
    total = _clamp(total)

    reasons = []
    for group in (edu_r, area_r, goal_r, int_r, mod_r, exp_r):
        for item in group:
            if item not in reasons:
                reasons.append(item)
    return {
        "programme_id": programme["id"],
        "programme": programme["name"],
        "score": total,
        "score_pct": int(round(total * 100)),
        "breakdown": {k: _clamp(v) for k, v in breakdown.items()},
        "reasons": reasons[:6],
        "modality": programme["modality"],
        "ects": programme["ects"],
        "url": programme.get("url"),
        "foundation_modules_possible": bool(programme.get("foundation_modules_possible")),
    }


def rank(profile: dict[str, Any], priority: str | None = None) -> list[dict[str, Any]]:
    scored = [score_programme(profile, p, priority=priority or profile.get("priority")) for p in programmes()]
    scored.sort(key=lambda x: (-x["score"], x["programme"]))
    return scored


def split_matches(scored: list[dict[str, Any]]) -> dict[str, Any]:
    threshold = strong_match_threshold()
    if not scored or scored[0]["score"] < threshold:
        return {
            "has_strong_match": False,
            "best": None,
            "alternatives": scored[:2],
            "all": scored,
        }
    return {
        "has_strong_match": True,
        "best": scored[0],
        "alternatives": scored[1:3],
        "all": scored,
    }
