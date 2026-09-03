from app.deps import AppContext
from app.search.mock import MOCK_RESULTS


async def test_pipeline_search_score_telegram_end_to_end(ctx: AppContext):
    summary = await ctx.pipeline.run()
    assert summary.error is None
    assert summary.results_found == len(MOCK_RESULTS)
    assert summary.new_saved == len(MOCK_RESULTS)
    assert summary.qualified >= 1
    assert summary.notified == summary.qualified

    messages = ctx.telegram_client.messages
    assert len(messages) == summary.notified
    for msg in messages:
        assert "🔥" in msg["text"]
        score_line = msg["text"].split("—", 1)[0]
        score = float(score_line.split()[1].split("/")[0])
        assert score >= 8.0
        markup = msg["reply_markup"]["inline_keyboard"]
        assert markup[0][0]["text"] == "🔗 View"

    stats = ctx.db.stats()
    assert stats["scanned_today"] == len(MOCK_RESULTS)
    assert stats["qualified"] == summary.qualified
    assert stats["sent"] == summary.notified

    second = await ctx.pipeline.run()
    assert second.new_saved == 0
    assert second.notified == 0
    assert len(ctx.telegram_client.messages) == summary.notified


async def test_pipeline_does_not_notify_low_scores(ctx: AppContext):
    await ctx.pipeline.run()
    titles = " ".join(m["text"] for m in ctx.telegram_client.messages)
    assert "India" not in titles
    assert "WordPress" not in titles
