from __future__ import annotations

from typing import Any

import httpx

from app.models import SearchResult
from app.search.base import SearchProvider


class TavilySearchProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str, base_url: str = "https://api.tavily.com/search") -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str, max_age_hours: int = 24) -> list[SearchResult]:
        if not self.api_key:
            raise RuntimeError("SEARCH_API_KEY is required for Tavily")
        days = 1 if max_age_hours <= 24 else max(1, round(max_age_hours / 24))
        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 10,
            "days": days,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
        results: list[SearchResult] = []
        for item in data.get("results") or []:
            url = item.get("url") or ""
            if not url:
                continue
            results.append(
                SearchResult(
                    title=item.get("title") or "",
                    url=url,
                    snippet=item.get("content") or item.get("snippet") or "",
                    source="tavily",
                    query=query,
                    raw=item,
                )
            )
        return results
