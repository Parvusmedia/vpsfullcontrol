from __future__ import annotations

from openai import AsyncOpenAI

from app.models import Opportunity
from app.profile import ALLOWED_TOOLS, PROFILE_SUMMARY
from app.proposal.base import ProposalGenerator

SYSTEM_PROMPT = f"""You write short, specific cover letters / Upwork proposals.

PROFILE (only this experience exists — never invent tools, employers, or results):
{PROFILE_SUMMARY}

Allowed tools/topics you may mention, and only if relevant to THIS brief:
{ ", ".join(ALLOWED_TOOLS) }.

Rules:
- 150 to 180 words. Hard max 180.
- Personalized to the project. Reference the actual problem.
- No generic phrases: "I am excited to apply", "leverage synergies", "passionate developer".
- Do not claim tools that are not in the allow-list.
- Emphasize business + process understanding BEFORE automation.
- The differentiator is consulting/architecture, not coding speed.
- Write in first person, professional, direct.
- English unless the brief is clearly in another language.
- No markdown headings. Plain text paragraphs.
"""


class OpenAIProposalGenerator(ProposalGenerator):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, opportunity: Opportunity, *, rewrite: bool = False) -> str:
        scoring = opportunity.scoring
        extra = "Rewrite with a different opening and structure. Same facts. Still 150–180 words." if rewrite else ""
        user = (
            f"PROJECT TITLE: {scoring.title if scoring else opportunity.title}\n"
            f"COMPANY: {scoring.company if scoring else ''}\n"
            f"COUNTRY: {scoring.country if scoring else ''}\n"
            f"PLATFORM: {opportunity.platform}\n"
            f"BUDGET: {scoring.budget if scoring else ''}\n"
            f"ESTIMATED VALUE: {scoring.estimated_value if scoring else ''}\n"
            f"SUMMARY: {scoring.summary if scoring else opportunity.snippet}\n"
            f"WHY FIT: {scoring.why_fit if scoring else ''}\n"
            f"URL: {opportunity.url}\n"
            f"{extra}"
        )
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.5 if not rewrite else 0.8,
        )
        text = (completion.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("OpenAI returned an empty proposal")
        return text
