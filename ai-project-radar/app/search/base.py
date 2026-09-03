from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import SearchResult


class SearchProvider(ABC):
    """Pluggable web search backend (Serper, Tavily, Bing, mock)."""

    name: str = "base"

    @abstractmethod
    async def search(self, query: str, max_age_hours: int = 24) -> list[SearchResult]:
        """Return recent search hits for a query."""
