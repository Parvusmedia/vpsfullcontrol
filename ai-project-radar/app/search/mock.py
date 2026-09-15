from __future__ import annotations

from datetime import datetime, timezone

from app.models import SearchResult
from app.search.base import SearchProvider

MOCK_RESULTS = [
    SearchResult(
        title="AI Automation Consultant for Revenue Ops — 3 month engagement",
        url="https://www.upwork.com/freelance-jobs/apply/AI-Automation-Consultant_~01radarhighfit/",
        snippet=(
            "US-based B2B SaaS (Series B) needs a senior consultant to map sales and "
            "marketing processes, then automate CRM, enrichment and reporting with AI agents. "
            "Fixed budget $8,000–$12,000. Posted 3 hours ago. Looking for someone who "
            "understands GTM operations, not just a developer."
        ),
        published_at=datetime.now(timezone.utc),
        source="Upwork",
        query='site:upwork.com/freelance-jobs "AI automation"',
    ),
    SearchResult(
        title="n8n / Make expert to rebuild internal ops (London)",
        url="https://www.freelancer.com/projects/n8n-make-internal-ops-uk",
        snippet=(
            "UK scale-up looking for a freelancer/consultant to replace brittle Zapier flows "
            "with n8n and Make. WhatsApp + HubSpot + reporting dashboards. Day rate preferred, "
            "budget around £550/day. Posted today."
        ),
        published_at=datetime.now(timezone.utc),
        source="Freelancer",
        query='site:freelancer.com/projects "n8n"',
    ),
    SearchResult(
        title="Looking for AI consultant — AdTech reporting automation (Dubai)",
        url="https://www.linkedin.com/posts/example-looking-for-ai-consultant-adtech",
        snippet=(
            "Media group in UAE looking for a consultant to automate campaign reporting and "
            "Paid Media workflows. Need someone who understands AdTech, not a junior coder. "
            "Contract, 4–6 weeks."
        ),
        published_at=datetime.now(timezone.utc),
        source="LinkedIn",
        query='site:linkedin.com/posts "looking for" "AI automation"',
    ),
    SearchResult(
        title="Cheap Python scraper + chatbot — India agency",
        url="https://www.upwork.com/freelance-jobs/apply/python-scraper-india_~01cheap/",
        snippet=(
            "Need a developer in India or Pakistan to scrape websites and build a simple "
            "chatbot. Budget $150 fixed. Hourly $8. Posted 1 hour ago."
        ),
        published_at=datetime.now(timezone.utc),
        source="Upwork",
        query='site:upwork.com/freelance-jobs "AI automation"',
    ),
    SearchResult(
        title="WordPress landing page updates",
        url="https://www.freelancer.com/projects/wordpress-landing-page-updates",
        snippet="Need 3 landing pages updated in WordPress. Budget $200. No automation.",
        published_at=datetime.now(timezone.utc),
        source="Freelancer",
        query='site:freelancer.com/projects "AI automation"',
    ),
    SearchResult(
        title="CRM + lead qualification automation — fee not disclosed",
        url="https://www.linkedin.com/jobs/view/crm-lead-qualification-contract-us",
        snippet=(
            "US-based healthcare-adjacent company hiring a contract automation consultant to design "
            "lead qualification and CRM workflows. Seniority required. Compensation is not disclosed."
        ),
        published_at=datetime.now(timezone.utc),
        source="LinkedIn",
        query="site:linkedin.com/jobs CRM automation contract",
    ),
]


class MockSearchProvider(SearchProvider):
    name = "mock"

    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.results = results if results is not None else list(MOCK_RESULTS)
        self.calls: list[tuple[str, int]] = []

    async def search(self, query: str, max_age_hours: int = 24) -> list[SearchResult]:
        self.calls.append((query, max_age_hours))
        return [item.model_copy(update={"query": query}) for item in self.results]
