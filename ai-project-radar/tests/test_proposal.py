from app.models import Opportunity, OpportunityScore
from app.proposal.mock import MockProposalGenerator


async def test_mock_proposal_is_personalized_and_sized():
    opp = Opportunity(
        id=1,
        url="https://upwork.com/jobs/n8n",
        normalized_url="https://upwork.com/jobs/n8n",
        content_hash="x",
        platform="Upwork",
        title="n8n internal ops rebuild",
        scoring=OpportunityScore(
            score=8.4,
            title="n8n / Make expert to rebuild internal ops (London)",
            company="UK scale-up",
            country="United Kingdom",
            summary="Replace Zapier with n8n and Make, WhatsApp + HubSpot reporting.",
            why_fit="Ops automation",
            risks="Legacy zaps",
            recommendation="Pursue",
            urgency="HIGH",
        ),
    )
    letter = await MockProposalGenerator().generate(opp)
    words = letter.split()
    assert 140 <= len(words) <= 200
    assert "n8n / Make expert to rebuild internal ops (London)" in letter
    assert "developer-for-hire" in letter.lower() or "not pitching as a developer" in letter.lower()
    assert "process" in letter.lower()
    rewritten = await MockProposalGenerator().generate(opp, rewrite=True)
    assert rewritten != letter
    assert "rewrite" in rewritten.lower()
