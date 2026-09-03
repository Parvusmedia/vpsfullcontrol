from __future__ import annotations

import html

from app.models import Opportunity
from app.normalize import relative_time


def format_alert(opp: Opportunity) -> str:
    scoring = opp.scoring
    if scoring is None:
        raise ValueError("opportunity has no scoring payload")
    score = f"{scoring.score:.1f}"
    published = relative_time(scoring.published_at, opp.first_seen.isoformat() if opp.first_seen else None)
    title = _esc(scoring.title or opp.title)
    company = _esc(scoring.company or "Unknown")
    country = _esc(scoring.country or "Unknown")
    platform = _esc(opp.platform or "web")
    estimated = _esc(scoring.estimated_value or scoring.budget or "n/a")
    summary = _esc(_clip(scoring.summary, 400))
    why = _esc(_clip(scoring.why_fit, 350))
    risks = _esc(_clip(scoring.risks, 250))
    return (
        f"🔥 <b>{score}/10 — {title}</b>\n\n"
        f"🏢 {company}\n"
        f"🌍 {country}\n"
        f"📍 {platform}\n"
        f"🕐 {html.escape(published)}\n\n"
        f"💰 Estimated: {estimated}\n\n"
        f"{summary}\n\n"
        f"✅ <b>Why it fits:</b>\n{why}\n\n"
        f"⚠️ <b>Risk:</b>\n{risks}"
    )


def format_proposal(opp: Opportunity, letter: str) -> str:
    title = _esc((opp.scoring.title if opp.scoring else None) or opp.title)
    return (
        f"✍️ <b>Cover letter — {title}</b>\n\n"
        f"{_esc(letter.strip())}"
    )


def alert_keyboard(opp: Opportunity) -> dict:
    if opp.id is None:
        raise ValueError("opportunity id required")
    return {
        "inline_keyboard": [
            [{"text": "🔗 View", "url": opp.url}],
            [
                {"text": "✍️ Prepare proposal", "callback_data": f"p:{opp.id}"},
                {"text": "❌ Discard", "callback_data": f"d:{opp.id}"},
            ],
        ]
    }


def proposal_keyboard(opp: Opportunity) -> dict:
    if opp.id is None:
        raise ValueError("opportunity id required")
    return {
        "inline_keyboard": [
            [{"text": "🔗 View", "url": opp.url}],
            [
                {"text": "🔄 Rewrite", "callback_data": f"r:{opp.id}"},
                {"text": "✅ Applied", "callback_data": f"a:{opp.id}"},
                {"text": "❌ Discard", "callback_data": f"d:{opp.id}"},
            ],
        ]
    }


def format_stats(stats: dict[str, int]) -> str:
    return (
        "📊 <b>Radar stats</b>\n\n"
        f"scanned today: {stats.get('scanned_today', 0)}\n"
        f"qualified: {stats.get('qualified', 0)}\n"
        f"sent: {stats.get('sent', 0)}\n"
        f"applied: {stats.get('applied', 0)}\n"
        f"discarded: {stats.get('discarded', 0)}"
    )


def format_scan_summary(summary) -> str:
    return (
        "🛰 <b>Scan complete</b>\n\n"
        f"found: {summary.results_found}\n"
        f"new: {summary.new_saved}\n"
        f"qualified ≥8: {summary.qualified}\n"
        f"sent: {summary.notified}"
        + (f"\nerror: {_esc(summary.error)}" if summary.error else "")
    )


def _esc(text: str) -> str:
    return html.escape(text or "", quote=False)


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
