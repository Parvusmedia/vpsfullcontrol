from __future__ import annotations

from app.config import Settings
from app.search.base import SearchProvider
from app.search.bing import BingSearchProvider
from app.search.mock import MockSearchProvider
from app.search.serper import SerperSearchProvider
from app.search.tavily import TavilySearchProvider


def get_search_provider(settings: Settings) -> SearchProvider:
    name = (settings.search_provider or "serper").strip().lower()
    if settings.use_mocks or name == "mock":
        return MockSearchProvider()
    if name == "serper":
        return SerperSearchProvider(settings.search_api_key, settings.serper_url)
    if name == "tavily":
        return TavilySearchProvider(settings.search_api_key, settings.tavily_url)
    if name == "bing":
        return BingSearchProvider(settings.search_api_key, settings.bing_url)
    raise ValueError(f"Unknown SEARCH_PROVIDER: {settings.search_provider}")
