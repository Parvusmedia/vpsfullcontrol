from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.models import SearchResult
from app.search.base import SearchProvider


def _freshness_tbs(max_age_hours: int) -> str:
    if max_age_hours <= 24:
        return "qdr:d"
    if max_age_hours <= 168:
        return "qdr:w"
    return "qdr:m"


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


class SerperSearchProvider(SearchProvider):
    """Google search via Serper.dev. Swap this class via SEARCH_PROVIDER."""

    name = "serper"

    def __init__(self, api_key: str, base_url: str = "https://google.serper.dev/search") -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str, max_age_hours: int = 24) -> list[SearchResult]:
        if not self.api_key:
            raise RuntimeError("SEARCH_API_KEY is required for Serper")
        payload = {
            "q": query,
            "num": 10,
            "tbs": _freshness_tbs(max_age_hours),
        }
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        results: list[SearchResult] = []
        for item in data.get("organic") or []:
            url = item.get("link") or ""
            if not url:
                continue
            results.append(
                SearchResult(
                    title=item.get("title") or "",
                    url=url,
                    snippet=item.get("snippet") or "",
                    published_at=_parse_date(item.get("date")),
                    source="serper",
                    query=query,
                    raw=item,
                )
            )
        return results
