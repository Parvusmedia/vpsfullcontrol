from app.db import Database
from app.models import OpportunityScore
from app.normalize import content_hash, normalize_url


def test_duplicate_by_normalized_url_and_hash(tmp_db: Database):
    url = "https://www.upwork.com/jobs/a?utm_source=x"
    normalized = normalize_url(url)
    hashed = content_hash(url, "Title", "Snippet")
    first = tmp_db.insert_new(
        url=url,
        normalized_url=normalized,
        content_hash=hashed,
        platform="Upwork",
        title="Title",
        snippet="Snippet",
        query_used="q",
    )
    assert first.id is not None
    dup = tmp_db.find_duplicate(normalized, hashed)
    assert dup is not None
    assert dup.id == first.id
    other_hash = content_hash(url, "Other", "Thing")
    still = tmp_db.find_duplicate(normalized, other_hash)
    assert still is not None


def test_never_inserts_same_normalized_url_twice(tmp_db: Database):
    tmp_db.insert_new(
        url="https://x.com/a",
        normalized_url="https://x.com/a",
        content_hash="h1",
        platform="web",
        title="A",
        snippet="",
        query_used="",
    )
    try:
        tmp_db.insert_new(
            url="https://x.com/a",
            normalized_url="https://x.com/a",
            content_hash="h2",
            platform="web",
            title="B",
            snippet="",
            query_used="",
        )
        raised = False
    except Exception:
        raised = True
    assert raised


def test_mark_sent_and_status(tmp_db: Database):
    opp = tmp_db.insert_new(
        url="https://x.com/b",
        normalized_url="https://x.com/b",
        content_hash="hb",
        platform="Upwork",
        title="B",
        snippet="",
        query_used="",
    )
    score = OpportunityScore(
        score=9.1,
        title="AI Automation Consultant",
        company="Acme",
        country="UK",
        published_at="",
        budget="",
        estimated_value="€5k–10k",
        summary="Need automation",
        why_fit="Fit",
        risks="Scope",
        recommendation="Pursue",
        urgency="HIGH",
    )
    tmp_db.save_score(opp.id, score)
    tmp_db.mark_sent(opp.id, 77)
    loaded = tmp_db.get(opp.id)
    assert loaded is not None
    assert loaded.telegram_sent is True
    assert loaded.status == "sent"
    assert loaded.score == 9.1
    tmp_db.set_status(opp.id, "applied")
    assert tmp_db.get(opp.id).status == "applied"
    stats = tmp_db.stats()
    assert stats["applied"] == 1
    assert stats["qualified"] == 1
    assert stats["sent"] == 1
