from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from advisor.engine import recommend  # noqa: E402
from advisor.intent import score_intent  # noqa: E402
from advisor.matcher import rank  # noqa: E402
from advisor.parser import parse_profile  # noqa: E402
from advisor.qa import answer_question  # noqa: E402

PHYSIO = (
    "I'm a physiotherapist with three years of experience. "
    "I work with athletes and I'd like to specialize without leaving my current job."
)
DEV = (
    "I studied software engineering and currently work as a developer. "
    "I want to understand how to apply AI to real business problems."
)
MKT = (
    "I studied Business Administration and work in digital marketing. "
    "I want to progress into a marketing management role."
)
EDGE = "I'm a chef and want to become an architect."


def test_physio_maps_to_biomechanics():
    result = recommend(PHYSIO)
    assert result["has_strong_match"]
    assert result["best"]["programme_id"] == "biomechanics"
    assert result["best"]["score"] > 0.7


def test_developer_maps_to_ai():
    result = recommend(DEV)
    assert result["best"]["programme_id"] == "ai-applied"


def test_marketing_profile():
    result = recommend(MKT)
    assert result["best"]["programme_id"] == "marketing"


def test_unrelated_not_forced():
    result = recommend(EDGE)
    assert result["has_strong_match"] is False
    assert result["best"] is None


def test_priority_shifts_ranking():
    base = rank(parse_profile(PHYSIO))
    boosted = rank(parse_profile(PHYSIO, priority="Learn new technology"), priority="Learn new technology")
    ai_base = next(x["score"] for x in base if x["programme_id"] == "ai-applied")
    ai_boost = next(x["score"] for x in boosted if x["programme_id"] == "ai-applied")
    assert ai_boost > ai_base


def test_parser_extracts_years():
    profile = parse_profile(PHYSIO)
    assert profile["education"] == "physiotherapy"
    assert profile["experience_years"] == 3
    assert "combine work and study" in profile["constraints"]


def test_question_uses_catalogue():
    rec = recommend(PHYSIO)["best"]
    out = answer_question("Can I combine it with work?", parse_profile(PHYSIO), rec)
    assert "Hybrid" in out["answer"] or "hybrid" in out["answer"].lower()


def test_intent_high_on_advisor():
    assert score_intent(
        {
            "profile_completed": True,
            "recommendation_generated": True,
            "lead_submitted": True,
        }
    ) == "HIGH"


def test_scores_reproducible():
    a = recommend(PHYSIO, debug=True)
    b = recommend(PHYSIO, debug=True)
    assert a["best"]["score"] == b["best"]["score"]
    assert a["debug"]["all_scores"] == b["debug"]["all_scores"]


def test_no_acceptance_language():
    text = recommend(PHYSIO)["best"]["explanation"].lower()
    assert "you are accepted" not in text
    assert "better salary" not in text
    assert "job guarantee" not in text
