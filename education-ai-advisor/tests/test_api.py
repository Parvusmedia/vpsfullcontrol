from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from main import app  # noqa: E402

client = TestClient(app)

PHYSIO = (
    "I'm a physiotherapist with three years of experience. "
    "I work with athletes and I'd like to specialize without leaving my current job."
)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["ai_mode"] == "mock"


def test_programmes_not_hardcoded_in_response_only():
    res = client.get("/api/programmes")
    ids = {p["id"] for p in res.json()["programmes"]}
    assert ids == {"ai-applied", "marketing", "biomechanics"}


def test_recommend_and_lead_context():
    rec = client.post("/api/recommend", json={"message": PHYSIO, "debug": True}).json()
    assert rec["best"]["programme_id"] == "biomechanics"
    lead = client.post(
        "/api/lead",
        json={
            "name": "Laura Martín",
            "email": "laura@example.com",
            "phone": "+34 600 000 000",
            "profile": rec["profile"],
            "recommendation": rec["best"],
            "alternatives": rec["alternatives"],
            "questions_asked": ["Can I combine it with work?"],
            "priority": "Specialization",
            "signals": {"programme_viewed": True},
        },
    ).json()
    assert lead["ok"]
    assert lead["lead_intent"] == "HIGH"
    listed = client.get("/api/leads").json()["leads"]
    assert listed[0]["recommendation"]["programme_id"] == "biomechanics"


def test_question_endpoint():
    rec = client.post("/api/recommend", json={"message": PHYSIO}).json()["best"]
    res = client.post(
        "/api/question",
        json={"question": "Can I combine it with work?", "message": PHYSIO, "recommendation": rec},
    )
    assert res.status_code == 200
    assert "catalogue" in res.json()["source"] or "Hybrid" in res.json()["answer"]


def test_guide_lawyer_endpoint():
    steps = client.get("/api/guide").json()
    assert len(steps["steps"]) == 3
    rec = client.post(
        "/api/guide",
        json={"answers": {"background": "law", "goal": "tech-law", "format": "work-study"}},
    ).json()
    assert rec["best"]["programme_id"] == "ai-applied"
    assert rec["has_strong_match"] is False
    assert "biomechanics" not in [x["programme_id"] for x in rec["remaining"]]
