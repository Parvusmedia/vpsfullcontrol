from __future__ import annotations

from datetime import datetime, timezone

from app.profile import SEARCH_TOPICS

SITE_TEMPLATES = [
    'site:upwork.com/freelance-jobs "{topic}"',
    'site:freelancer.com/projects "{topic}"',
    'site:linkedin.com/posts "looking for" "{topic}"',
    'site:linkedin.com/posts "looking for freelancer" {topic}',
    "site:linkedin.com/jobs {topic} contract",
]

EXTRA_QUERIES = [
    'site:upwork.com/freelance-jobs "implementation partner" AI',
    'site:upwork.com/freelance-jobs "AI consultant" automation',
    'site:linkedin.com/posts "looking for consultant" n8n',
    'site:linkedin.com/posts "looking for" "Make.com" automation',
    'site:freelancer.com/projects "WhatsApp automation"',
]


def generate_queries(topics: list[str] | None = None) -> list[str]:
    topics = topics or SEARCH_TOPICS
    queries: list[str] = []
    for topic in topics:
        for template in SITE_TEMPLATES:
            queries.append(template.format(topic=topic))
    queries.extend(EXTRA_QUERIES)
    # Preserve order, drop duplicates.
    seen: set[str] = set()
    unique: list[str] = []
    for query in queries:
        if query not in seen:
            seen.add(query)
            unique.append(query)
    return unique


def select_queries(queries: list[str], limit: int, now: datetime | None = None) -> list[str]:
    """Rotate a subset each hour so all queries are covered over time."""
    if limit <= 0 or limit >= len(queries):
        return list(queries)
    now = now or datetime.now(timezone.utc)
    offset = (now.timetuple().tm_yday * 24 + now.hour) % len(queries)
    rotated = queries[offset:] + queries[:offset]
    return rotated[:limit]
