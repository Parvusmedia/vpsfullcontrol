from __future__ import annotations

import httpx

from app.models import SearchResult
from app.search.base import SearchProvider


class BingSearchProvider(SearchProvider):
    """Azure Bing Web Search v7. Set SEARCH_PROVIDER=bing and SEARCH_API_KEY."""

    name = "bing"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.bing.microsoft.com/v7.0/search",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str, max_age_hours: int = 24) -> list[SearchResult]:
        if not self.api_key:
            raise RuntimeError("SEARCH_API_KEY is required for Bing")
        freshness = "Day" if max_age_hours <= 24 else "Week"
        params = {"q": query, "count": 10, "freshness": freshness, "textDecorations": "false"}
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        results: list[SearchResult] = []
        for item in (data.get("webPages") or {}).get("value") or []:
            url = item.get("url") or ""
            if not url:
                continue
            results.append(
                SearchResult(
                    title=item.get("name") or "",
                    url=url,
                    snippet=item.get("snippet") or "",
                    source="bing",
                    query=query,
                    raw=item,
                )
            )
        return results
