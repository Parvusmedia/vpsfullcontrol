from __future__ import annotations

from app.models import Opportunity
from app.proposal.base import ProposalGenerator


class MockProposalGenerator(ProposalGenerator):
    async def generate(self, opportunity: Opportunity, *, rewrite: bool = False) -> str:
        scoring = opportunity.scoring
        title = (scoring.title if scoring else opportunity.title) or "the project"
        company = (scoring.company if scoring else "") or "your team"
        angle = (
            "a different cut of the same experience"
            if rewrite
            else "how I typically approach this kind of work"
        )
        greeting = company.split("(")[0].strip() or "there"
        rewrite_line = (
            "This rewrite stays on the same facts and just changes the entry point."
            if rewrite
            else "This first version is written against the actual brief, not a template."
        )
        return (
            f"Hi {greeting},\n\n"
            f"I read the brief for {title} and it matches how I work: understand the "
            f"business, the process, and the people/data before any automation is designed. "
            f"I am not pitching as a developer-for-hire. For more than ten years I have "
            f"applied AdTech and MarTech, CRM, lead generation, lead qualification, Sales "
            f"Navigator, proprietary prospecting tools, data enrichment, cold email, Paid "
            f"Media automation, campaign reporting and dashboards to real go-to-market "
            f"operations.\n\n"
            f"On similar work I map the current workflow, find the inefficiency, then design "
            f"the integration with APIs, webhooks and CRM — WhatsApp or Telegram only when "
            f"the process actually lives there — and only then automate. {angle.capitalize()} "
            f"is to keep the first pass tight: one process, a measurable output, no tool "
            f"theatre. {rewrite_line} If useful I can start with a short diagnostic of the "
            f"current path from lead to report before proposing stack or timeline.\n\n"
            f"— Senior founder / business automation consultant / solutions architect"
        )
