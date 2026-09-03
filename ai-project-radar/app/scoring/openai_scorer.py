from __future__ import annotations

from openai import AsyncOpenAI

from app.models import OpportunityScore, SearchResult
from app.profile import (
    ECONOMY_PREFERENCES,
    EXCLUDED_COUNTRIES,
    PRIORITY_MARKETS,
    PROFILE_SUMMARY,
    SCORING_WEIGHTS,
)
from app.scoring.base import Scorer

SYSTEM_PROMPT = f"""You are scoring freelance/consulting opportunities for this person:

{PROFILE_SUMMARY}

GEOGRAPHY
Exclude (score should normally be <= 5, almost never notify): {", ".join(EXCLUDED_COUNTRIES)}.
Prioritize: {", ".join(PRIORITY_MARKETS)}.

ECONOMICS
Preference: fixed >= {ECONOMY_PREFERENCES["fixed_min_usd_eur"]} USD/EUR,
hourly >= {ECONOMY_PREFERENCES["hourly_min_eur"]} EUR,
day rate >= {ECONOMY_PREFERENCES["day_rate_min_eur"]} EUR.
Do NOT auto-reject if budget is missing. In that case estimate economic potential
from company, country, seniority, scope and complexity.

SCORING WEIGHTS (approximate):
- {int(SCORING_WEIGHTS["profile_fit"]*100)}% profile fit
- {int(SCORING_WEIGHTS["economic_potential"]*100)}% economic potential
- {int(SCORING_WEIGHTS["buyer_market"]*100)}% buyer market
- {int(SCORING_WEIGHTS["ability_to_execute"]*100)}% ability to execute
- {int(SCORING_WEIGHTS["consulting_business_component"]*100)}% consulting/business component (not just coding)
- {int(SCORING_WEIGHTS["competition"]*100)}% competition if known
- {int(SCORING_WEIGHTS["freshness"]*100)}% freshness

Freshness: prefer last 24 hours. 24–72 hours may score >= 8 only if exceptionally strong.
The differentiator is consulting + process + automation, not being a developer-for-hire.

Return structured JSON only. score is 0-10 (decimals allowed).
urgency is HIGH, MEDIUM or LOW.
recommendation should be a short pursue/skip/watch line.
"""


class OpenAIScorer(Scorer):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def score(self, result: SearchResult) -> OpportunityScore:
        published = result.published_at.isoformat() if result.published_at else "unknown"
        user = (
            f"TITLE: {result.title}\n"
            f"URL: {result.url}\n"
            f"PLATFORM/SOURCE: {result.source}\n"
            f"PUBLISHED_AT: {published}\n"
            f"QUERY: {result.query}\n"
            f"SNIPPET:\n{result.snippet}\n"
        )
        completion = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            response_format=OpportunityScore,
            temperature=0.2,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed score")
        return parsed
