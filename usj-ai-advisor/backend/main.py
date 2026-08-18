from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from advisor import engine, guide, intent, store
from advisor.catalogue import programmes, public_programme, reload
from advisor.llm import ai_mode

FRONTEND = os.getenv("USJ_FRONTEND_DIR", "")

app = FastAPI(title="USJ AI Student Advisor", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class AnalyseIn(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    priority: str | None = None


class RecommendIn(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    priority: str | None = None
    debug: bool = False


class GuideIn(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
    debug: bool = False


class QuestionIn(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    message: str = ""
    priority: str | None = None
    recommendation: dict[str, Any] | None = None


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(default="", max_length=40)
    profile: dict[str, Any] = Field(default_factory=dict)
    recommendation: dict[str, Any] | None = None
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    questions_asked: list[str] = Field(default_factory=list)
    priority: str | None = None
    signals: dict[str, Any] = Field(default_factory=dict)


class EventIn(BaseModel):
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


@app.get("/api/health")
@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "product": "AI Student Advisor",
        "ai_mode": ai_mode(),
        "programmes": len(programmes()),
    }


@app.get("/api/programmes")
def list_programmes() -> dict[str, Any]:
    return {"programmes": [public_programme(p) for p in programmes()]}


@app.post("/api/analyse")
def analyse(body: AnalyseIn) -> dict[str, Any]:
    profile = engine.analyse_message(body.message, priority=body.priority)
    profile.pop("raw_message", None)
    return {"profile": profile}


@app.post("/api/recommend")
def recommend(body: RecommendIn) -> dict[str, Any]:
    try:
        return engine.recommend(body.message, priority=body.priority, debug=body.debug)
    except Exception:
        return {
            "has_strong_match": False,
            "fallback": True,
            "message": "Vamos a ayudarte a encontrar el programa adecuado.",
            "explore_url": "https://www.usj.es/estudios/posgrados/masteres",
            "best": None,
            "alternatives": [],
        }


@app.get("/api/guide")
def get_guide() -> dict[str, Any]:
    return guide.public_steps()


@app.post("/api/guide")
def post_guide(body: GuideIn) -> dict[str, Any]:
    try:
        return guide.run_guide(body.answers, debug=body.debug)
    except Exception:
        return {
            "has_strong_match": False,
            "fallback": True,
            "message": "Vamos a ayudarte a encontrar el programa adecuado.",
            "best": None,
            "alternatives": [],
            "remaining": [],
        }


@app.post("/api/question")
def question(body: QuestionIn) -> dict[str, Any]:
    try:
        return engine.ask(body.question, body.message, body.priority, body.recommendation)
    except Exception:
        return {
            "answer": "Un asesor de USJ puede ayudarte. Solo uso el catálogo aprobado.",
            "source": "fallback",
        }


@app.post("/api/lead")
def create_lead(body: LeadIn) -> dict[str, Any]:
    signals = dict(body.signals)
    signals.update(
        {
            "profile_completed": bool(body.profile),
            "recommendation_generated": bool(body.recommendation),
            "question_asked": bool(body.questions_asked),
            "priority_selected": bool(body.priority),
            "lead_submitted": True,
        }
    )
    lead_intent = intent.score_intent(signals)
    record = store.append_lead(
        {
            "name": body.name,
            "email": str(body.email),
            "phone": body.phone,
            "profile": body.profile,
            "recommendation": body.recommendation,
            "alternatives": body.alternatives,
            "questions_asked": body.questions_asked,
            "priority": body.priority,
            "lead_intent": lead_intent,
        }
    )
    return {"ok": True, "id": record["id"], "lead_intent": lead_intent}


@app.get("/api/leads")
def leads() -> dict[str, Any]:
    return {"leads": store.list_leads()}


@app.post("/api/events")
def events(body: EventIn) -> dict[str, Any]:
    store.append_event({"name": body.name, "payload": body.payload})
    return {"ok": True}


@app.get("/api/events")
def get_events() -> dict[str, Any]:
    return {"events": store.list_events()}


@app.post("/api/admin/reload")
def admin_reload() -> dict[str, Any]:
    data = reload()
    return {"ok": True, "programmes": len(data.get("programmes", []))}


if FRONTEND and os.path.isdir(FRONTEND):
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
