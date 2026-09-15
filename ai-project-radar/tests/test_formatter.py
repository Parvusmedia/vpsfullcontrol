from datetime import datetime, timezone

from app.models import Opportunity, OpportunityScore
from app.telegram.formatter import alert_keyboard, format_alert, format_stats, proposal_keyboard


def _opp() -> Opportunity:
    return Opportunity(
        id=42,
        url="https://www.upwork.com/freelance-jobs/apply/AI-Automation-Consultant",
        normalized_url="https://upwork.com/freelance-jobs/apply/AI-Automation-Consultant",
        content_hash="abc",
        platform="Upwork",
        title="AI Automation Consultant",
        first_seen=datetime.now(timezone.utc),
        scoring=OpportunityScore(
            score=9.1,
            title="AI Automation Consultant",
            company="Acme",
            country="UK",
            published_at="2h ago",
            budget="",
            estimated_value="€5k–10k",
            summary="Need a senior consultant to automate CRM and reporting.",
            why_fit="Process-first automation, AdTech-adjacent GTM.",
            risks="Scope creep on integrations.",
            recommendation="Pursue",
            urgency="HIGH",
        ),
    )


def test_alert_format_matches_spec():
    text = format_alert(_opp())
    assert "🔥" in text
    assert "9.1/10" in text
    assert "AI Automation Consultant" in text
    assert "🏢" in text and "Acme" in text
    assert "🌍" in text and "UK" in text
    assert "📍" in text and "Upwork" in text
    assert "🕐" in text
    assert "💰 Estimated: €5k–10k" in text
    assert "✅" in text and "Why it fits" in text
    assert "⚠️" in text and "Risk" in text


def test_alert_keyboard_actions():
    kb = alert_keyboard(_opp())
    rows = kb["inline_keyboard"]
    assert rows[0][0]["text"] == "🔗 View"
    assert rows[0][0]["url"].startswith("https://")
    labels = {btn["text"] for btn in rows[1]}
    assert "✍️ Prepare proposal" in labels
    assert "❌ Discard" in labels
    assert rows[1][0]["callback_data"] == "p:42"


def test_proposal_keyboard_actions():
    kb = proposal_keyboard(_opp())
    labels = {btn["text"] for row in kb["inline_keyboard"] for btn in row}
    assert "🔄 Rewrite" in labels
    assert "✅ Applied" in labels
    assert "❌ Discard" in labels


def test_stats_format():
    text = format_stats(
        {"scanned_today": 4, "qualified": 2, "sent": 2, "applied": 1, "discarded": 0}
    )
    assert "scanned today: 4" in text
    assert "qualified: 2" in text
