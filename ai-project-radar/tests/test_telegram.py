from app.deps import AppContext


async def test_scan_latest_stats_commands(ctx: AppContext):
    bot = ctx.bot
    chat = ctx.settings.telegram_chat_id

    await bot.handle_update(
        {"message": {"chat": {"id": int(chat)}, "text": "/scan"}}
    )
    texts = [m["text"] for m in ctx.telegram_client.messages]
    assert any("Running radar scan" in t for t in texts)
    assert any("Scan complete" in t for t in texts)
    assert any("🔥" in t for t in texts)

    ctx.telegram_client.messages.clear()
    await bot.handle_command("/latest", chat)
    assert ctx.telegram_client.messages
    assert all("🔥" in m["text"] for m in ctx.telegram_client.messages)

    ctx.telegram_client.messages.clear()
    await bot.handle_command("/stats", chat)
    body = ctx.telegram_client.messages[-1]["text"]
    assert "scanned today:" in body
    assert "qualified:" in body
    assert "sent:" in body
    assert "applied:" in body
    assert "discarded:" in body


async def test_ignores_other_chat(ctx: AppContext):
    await ctx.bot.handle_update({"message": {"chat": {"id": 999}, "text": "/scan"}})
    assert ctx.telegram_client.messages == []


async def test_prepare_rewrite_applied_discard(ctx: AppContext):
    await ctx.pipeline.run()
    sent = ctx.db.unsent_qualified(8)
    assert sent == []
    latest = ctx.db.latest_qualified(8, limit=1)
    assert latest
    opp = latest[0]
    chat = ctx.settings.telegram_chat_id
    ctx.telegram_client.messages.clear()

    await ctx.bot.handle_update(
        {
            "callback_query": {
                "id": "cb1",
                "data": f"p:{opp.id}",
                "message": {"chat": {"id": int(chat)}},
            }
        }
    )
    letter_msg = ctx.telegram_client.messages[-1]
    assert "Cover letter" in letter_msg["text"]
    words = [w for w in letter_msg["text"].split() if w]
    assert 120 <= len(words) <= 220
    labels = {b["text"] for row in letter_msg["reply_markup"]["inline_keyboard"] for b in row}
    assert "🔄 Rewrite" in labels
    assert "✅ Applied" in labels

    await ctx.bot.handle_update(
        {
            "callback_query": {
                "id": "cb2",
                "data": f"r:{opp.id}",
                "message": {"chat": {"id": int(chat)}},
            }
        }
    )
    assert "rewrite" in ctx.telegram_client.messages[-1]["text"].lower() or "Cover letter" in ctx.telegram_client.messages[-1]["text"]

    await ctx.bot.handle_update(
        {
            "callback_query": {
                "id": "cb3",
                "data": f"a:{opp.id}",
                "message": {"chat": {"id": int(chat)}},
            }
        }
    )
    assert ctx.db.get(opp.id).status == "applied"

    other = ctx.db.latest_qualified(8, limit=2)[-1]
    await ctx.bot.handle_update(
        {
            "callback_query": {
                "id": "cb4",
                "data": f"d:{other.id}",
                "message": {"chat": {"id": int(chat)}},
            }
        }
    )
    assert ctx.db.get(other.id).status == "discarded"
    stats = ctx.db.stats()
    assert stats["applied"] >= 1
    assert stats["discarded"] >= 1
