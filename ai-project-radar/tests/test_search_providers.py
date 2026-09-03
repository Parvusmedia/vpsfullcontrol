from app.search.factory import get_search_provider
from app.search.mock import MockSearchProvider
from app.search.serper import SerperSearchProvider
from app.config import Settings


def test_factory_returns_mock_when_use_mocks(mock_settings: Settings):
    provider = get_search_provider(mock_settings)
    assert isinstance(provider, MockSearchProvider)


def test_factory_serper():
    settings = Settings(search_provider="serper", search_api_key="k", use_mocks=False)
    provider = get_search_provider(settings)
    assert isinstance(provider, SerperSearchProvider)


async def test_serper_maps_organic_results(monkeypatch):
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "organic": [
                    {
                        "title": "AI automation job",
                        "link": "https://www.upwork.com/freelance-jobs/ai",
                        "snippet": "Need AI automation consultant",
                        "date": "2026-09-03T10:00:00Z",
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json, headers):
            assert "q" in json
            assert json["tbs"] in {"qdr:d", "qdr:w", "qdr:m"}
            assert headers["X-API-KEY"] == "test-key"
            return FakeResponse()

    monkeypatch.setattr("app.search.serper.httpx.AsyncClient", FakeClient)
    provider = SerperSearchProvider("test-key")
    results = await provider.search('site:upwork.com/freelance-jobs "AI automation"', 24)
    assert len(results) == 1
    assert results[0].url.endswith("/ai")
    assert results[0].title == "AI automation job"
