"""Optional LLM layer. Never decides eligibility, prices, places or dates."""
from __future__ import annotations

import json
import os
from typing import Any

ALLOWED_PROFILE_KEYS = {
    "education",
    "experience_years",
    "current_role",
    "interests",
    "goal",
    "constraints",
}


def ai_mode() -> str:
    return (os.getenv("AI_MODE") or "mock").strip().lower()


def openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _strip_pii(payload: dict[str, Any]) -> dict[str, Any]:
    blocked = {"name", "email", "phone", "raw_lead"}
    return {k: v for k, v in payload.items() if k not in blocked}


def analyse_with_llm(message: str) -> dict[str, Any] | None:
    if ai_mode() in ("mock", "off") or not openai_configured():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        prompt = (
            "Extract a career profile as JSON with keys: education, experience_years, "
            "current_role, interests (array), goal, constraints (array). "
            "No name, email, phone. No programme recommendation. No eligibility decision.\n\n"
            f"TEXT:\n{message}"
        )
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=12,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        return {k: data.get(k) for k in ALLOWED_PROFILE_KEYS}
    except Exception:
        return None


def explain_with_llm(context: dict[str, Any]) -> str | None:
    if ai_mode() in ("mock", "off") or not openai_configured():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        safe = _strip_pii(context)
        prompt = (
            "Write 2-3 sentences explaining why this programme may fit. "
            "Use ONLY the provided reasons, facts and eligibility status. "
            "Never promise salary, jobs or admission. Never invent requirements, price, places or dates.\n"
            f"{json.dumps(safe, ensure_ascii=False)}"
        )
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
            timeout=12,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or None
    except Exception:
        return None
