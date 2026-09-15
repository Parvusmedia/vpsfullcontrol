from app.scoring.mock import MockScorer
from app.search.mock import MOCK_RESULTS


async def test_mock_scorer_high_fit_priority_market():
    scorer = MockScorer()
    high = next(r for r in MOCK_RESULTS if "Revenue Ops" in r.title)
    scored = await scorer.score(high)
    assert scored.score >= 8
    assert scored.country == "United States"
    assert scored.urgency in {"HIGH", "MEDIUM", "LOW"}
    assert scored.estimated_value


async def test_mock_scorer_excludes_india_low_budget():
    scorer = MockScorer()
    cheap = next(r for r in MOCK_RESULTS if "India" in r.title)
    scored = await scorer.score(cheap)
    assert scored.score < 8
    assert scored.score <= 5


async def test_mock_scorer_missing_budget_still_evaluates():
    scorer = MockScorer()
    no_budget = next(r for r in MOCK_RESULTS if "fee not disclosed" in r.title.lower())
    scored = await scorer.score(no_budget)
    assert scored.budget == "not listed"
    assert scored.score >= 8
    assert "Likely" in scored.estimated_value or "potential" in scored.why_fit.lower()


async def test_mock_scorer_uae_adtech_without_budget():
    scorer = MockScorer()
    uae = next(r for r in MOCK_RESULTS if "Dubai" in r.title)
    scored = await scorer.score(uae)
    assert scored.score >= 8
    assert scored.country == "UAE"
    assert "UAE" in scored.why_fit or "AdTech" in scored.why_fit
    assert "US contract" not in scored.why_fit


async def test_wordpress_is_not_qualified():
    scorer = MockScorer()
    wp = next(r for r in MOCK_RESULTS if "WordPress" in r.title)
    scored = await scorer.score(wp)
    assert scored.score < 8
