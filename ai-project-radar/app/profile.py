"""Consultant profile, geography, economics and scoring weights for OpenAI."""

from __future__ import annotations

PROFILE_NAME = "Senior Founder / Business Automation Consultant / Solutions Architect"

PROFILE_SUMMARY = """
Senior Founder / Business Automation Consultant / Solutions Architect.

More than 10 years applying technology to advertising and marketing:
AdTech, MarTech, business automation, AI automation, APIs/integrations, CRM,
lead generation, lead qualification, Sales Navigator, proprietary tools to
identify companies and contacts, data enrichment, cold email automation,
Paid Media automation, campaign reporting, dashboards, WhatsApp, Telegram,
data-driven workflows, and business process optimisation.

The differentiator is NOT being a developer-for-hire.

Approach:
Understand business → understand processes → understand people/data →
identify inefficiencies → design solution → automate/integrate →
measure business value.

Hands-on with n8n, Make, OpenAI integrations, Claude integrations, webhooks,
WhatsApp automation, Telegram automation, CRM automation, and implementation-partner work.
""".strip()

ALLOWED_TOOLS = [
    "n8n",
    "Make",
    "OpenAI",
    "Claude",
    "WhatsApp",
    "Telegram",
    "Sales Navigator",
    "CRM",
    "APIs",
    "webhooks",
    "data enrichment",
    "cold email",
    "Paid Media",
    "dashboards",
    "campaign reporting",
]

EXCLUDED_COUNTRIES = ["India", "Pakistan", "Bangladesh"]

PRIORITY_MARKETS = [
    "United States",
    "United Kingdom",
    "UAE",
    "Saudi Arabia",
    "Switzerland",
    "Germany",
    "Netherlands",
    "Nordics",
    "Australia",
    "Singapore",
    "Spain",
    "France",
    "Belgium",
    "Ireland",
    "Austria",
    "Western Europe",
]

ECONOMY_PREFERENCES = {
    "fixed_min_usd_eur": 2500,
    "hourly_min_eur": 45,
    "day_rate_min_eur": 500,
}

SCORING_WEIGHTS = {
    "profile_fit": 0.25,
    "economic_potential": 0.20,
    "buyer_market": 0.15,
    "ability_to_execute": 0.15,
    "consulting_business_component": 0.10,
    "competition": 0.10,
    "freshness": 0.05,
}

SEARCH_TOPICS = [
    "AI automation",
    "AI agents",
    "n8n",
    "Make.com",
    "CRM automation",
    "API integration",
    "webhooks",
    "WhatsApp automation",
    "Telegram automation",
    "reporting automation",
    "business process automation",
    "internal operations automation",
    "AdTech automation",
    "MarTech automation",
    "OpenAI integrations",
    "Claude integrations",
    "AI consultants",
    "implementation partner",
]
