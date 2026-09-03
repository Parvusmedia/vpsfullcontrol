from __future__ import annotations

from app.models import OpportunityScore, SearchResult
from app.profile import (
    ECONOMY_PREFERENCES,
    EXCLUDED_COUNTRIES,
    PRIORITY_MARKETS,
    PROFILE_SUMMARY,
    SCORING_WEIGHTS,
)
from app.scoring.base import Scorer

EXCLUDED_HINTS = ("india", "pakistan", "bangladesh", "hindi", "$8/hr", "$8 hourly", "budget $150")
LOW_FIT_HINTS = ("wordpress", "landing page", "cheap python scraper")
HIGH_FIT_HINTS = (
    "ai automation",
    "n8n",
    "make",
    "adtech",
    "crm",
    "lead qualification",
    "whatsapp",
    "consultant",
    "revenue ops",
)
PRIORITY_HINTS = (
    "united states",
    "us-based",
    " uk",
    "london",
    "uae",
    "dubai",
    "germany",
    "netherlands",
    "switzerland",
    "australia",
    "singapore",
    "spain",
    "france",
)


class MockScorer(Scorer):
    """Deterministic scorer for tests and USE_MOCKS=true."""

    async def score(self, result: SearchResult) -> OpportunityScore:
        text = f"{result.title} {result.snippet} {result.url}".lower()
        excluded = any(h in text for h in EXCLUDED_HINTS)
        low = any(h in text for h in LOW_FIT_HINTS)
        high = any(h in text for h in HIGH_FIT_HINTS)
        priority = any(h in text for h in PRIORITY_HINTS)
        has_budget = any(tok in text for tok in ("$", "£", "€", "budget", "day rate"))

        if excluded:
            score = 2.8
            country = "India"
            recommendation = "Skip — excluded geography / low-value coding task."
            urgency = "LOW"
            estimated = "$150"
            why = "Geography and price point do not match the consulting profile."
            risks = "Race-to-bottom marketplace work."
        elif low:
            score = 3.4
            country = "Unknown"
            recommendation = "Skip — not automation/consulting work."
            urgency = "LOW"
            estimated = "$200"
            why = "Tactical production work with no process or AI component."
            risks = "Commodity task, high competition."
        elif high and priority:
            score = 8.9 if "revenue ops" in text or "adtech" in text else 8.4
            if "dubai" in text or "uae" in text:
                country = "UAE"
            elif "london" in text or " uk" in text or "£" in text:
                country = "United Kingdom"
            else:
                country = "United States"
            recommendation = "Pursue — strong profile fit and buyer market."
            urgency = "HIGH"
            estimated = "€5k–10k" if "£" in text or "$8,000" in text else "€4k–8k"
            why = (
                "Senior consulting + automation brief in a priority market. "
                "Needs process understanding before building workflows."
            )
            risks = "Scope may expand; confirm decision-maker and timeline."
            if not has_budget:
                score = 8.1
                estimated = "Likely €4k–9k based on US contract seniority"
                why = (
                    "No posted budget, but US contract + CRM/lead qualification "
                    "suggests mid-five-figure potential if scoped as consulting."
                )
        else:
            score = 6.2
            country = "Unknown"
            recommendation = "Watch — mid fit, not a clear 8+."
            urgency = "MEDIUM"
            estimated = "Unclear"
            why = "Related to automation but weak consulting/economic signal."
            risks = "Could be a small implementation ticket."

        company = "Unknown"
        if "saas" in text:
            company = "B2B SaaS (Series B)"
        elif "scale-up" in text:
            company = "UK scale-up"
        elif "media group" in text:
            company = "UAE media group"
        elif "healthcare" in text:
            company = "US healthcare-adjacent company"

        return OpportunityScore(
            score=round(score, 1),
            title=result.title,
            company=company,
            country=country,
            published_at=result.published_at.isoformat() if result.published_at else "",
            budget="not listed" if not has_budget else "see listing",
            estimated_value=estimated,
            summary=result.snippet[:400],
            why_fit=why,
            risks=risks,
            recommendation=recommendation,
            urgency=urgency,  # type: ignore[arg-type]
        )


# Keep profile constants imported so mock scoring stays aligned with production prompts.
_ = (
    PROFILE_SUMMARY,
    EXCLUDED_COUNTRIES,
    PRIORITY_MARKETS,
    ECONOMY_PREFERENCES,
    SCORING_WEIGHTS,
)
