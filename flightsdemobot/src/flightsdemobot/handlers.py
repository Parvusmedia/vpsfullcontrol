"""Telegram bot handlers."""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from flightsdemobot.calendar import (
    day_keyboard,
    month_keyboard,
    parse_user_date,
    today_riyadh,
)
from flightsdemobot.config import Settings
from flightsdemobot.hubs import is_valid_iata
from flightsdemobot.i18n import Lang, t
from flightsdemobot.keyboards import (
    hub_keyboard,
    language_keyboard,
    menu_keyboard,
    one_way_keyboard,
)
from flightsdemobot.saudia.client import FareQuote, QuoteService
from flightsdemobot.storage import Store

logger = logging.getLogger(__name__)

PRIVATE = filters.ChatType.PRIVATE


def _lang_from_telegram(code: str | None) -> Lang:
    if code and code.lower().startswith("ar"):
        return "ar"
    return "en"


def _is_private(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type == "private"


async def _deny_non_private(update: Update, lang: Lang = "en") -> None:
    if update.effective_message:
        await update.effective_message.reply_text(t("private_only", lang))


def _store(context: ContextTypes.DEFAULT_TYPE) -> Store:
    return context.application.bot_data["store"]


def _quotes(context: ContextTypes.DEFAULT_TYPE) -> QuoteService:
    return context.application.bot_data["quotes"]


def _settings(context: ContextTypes.DEFAULT_TYPE) -> Settings:
    return context.application.bot_data["settings"]


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_chat or not update.effective_message:
        await _deny_non_private(update)
        return
    chat_id = update.effective_chat.id
    store = _store(context)
    state = store.get(chat_id)
    if update.effective_user and update.effective_user.language_code:
        state.lang = _lang_from_telegram(update.effective_user.language_code)
    state.step = "await_key" if not state.unlocked else "idle"
    store.save(chat_id, state)
    await update.effective_message.reply_text(
        t("choose_language", state.lang),
        reply_markup=language_keyboard(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_message:
        return
    store = _store(context)
    state = store.get(update.effective_chat.id)
    await update.effective_message.reply_text(t("help", state.lang))


async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_chat or not update.effective_message:
        return
    store = _store(context)
    store.lock(update.effective_chat.id)
    state = store.get(update.effective_chat.id)
    await update.effective_message.reply_text(t("locked", state.lang))


async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_message:
        return
    store = _store(context)
    state = store.get(update.effective_chat.id)
    await update.effective_message.reply_text(
        t("choose_language", state.lang),
        reply_markup=language_keyboard(),
    )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_chat or not update.effective_message:
        return
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    state.step = "idle"
    store.save(chat_id, state)
    await update.effective_message.reply_text(
        t("cancelled", state.lang),
        reply_markup=menu_keyboard(state.lang) if state.unlocked else None,
    )


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _begin_search(update, context)


async def on_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not update.effective_chat:
        return
    await query.answer()
    if not query.data.startswith("lang:"):
        return
    lang = query.data.split(":")[1]
    if lang not in ("en", "ar"):
        return
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    state.lang = lang
    if not state.unlocked:
        state.step = "await_key"
        store.save(chat_id, state)
        await query.edit_message_text(t("enter_access_key", lang))
        return
    state.step = "idle"
    store.save(chat_id, state)
    await query.edit_message_text(t("access_ok", lang))
    await context.bot.send_message(
        chat_id,
        t("pick_origin", lang),
        reply_markup=menu_keyboard(lang),
    )
    await _prompt_origin(context, chat_id, lang)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not update.effective_chat:
        return
    await query.answer()
    data = query.data
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    if not state.unlocked:
        return

    if data.startswith("dep:m:"):
        month = date.fromisoformat(data.split(":")[2])
        await query.edit_message_text(
            t("pick_departure", state.lang),
            reply_markup=day_keyboard("dep", month),
        )
        return

    if data.startswith("dep:d:"):
        state.draft.departure = date.fromisoformat(data.split(":")[2])
        state.step = "pick_return"
        store.save(chat_id, state)
        await query.edit_message_text(t("pick_return", state.lang))
        await context.bot.send_message(
            chat_id,
            t("pick_return", state.lang),
            reply_markup=one_way_keyboard(state.lang),
        )
        await context.bot.send_message(
            chat_id,
            t("pick_return", state.lang),
            reply_markup=month_keyboard("ret", state.lang),
        )
        return

    if data.startswith("ret:m:"):
        month = date.fromisoformat(data.split(":")[2])
        min_d = state.draft.departure or today_riyadh()
        await query.edit_message_text(
            t("pick_return", state.lang),
            reply_markup=day_keyboard("ret", month, min_date=min_d + timedelta(days=1)),
        )
        return

    if data.startswith("ret:d:"):
        ret = date.fromisoformat(data.split(":")[2])
        if state.draft.departure and ret <= state.draft.departure:
            await query.edit_message_text(t("return_before_depart", state.lang))
            return
        state.draft.return_date = ret
        state.draft.one_way = False
        state.step = "pick_max_price"
        store.save(chat_id, state)
        await query.edit_message_text(t("pick_max_price", state.lang))
        return

    if data == "trip:ow":
        state.draft.one_way = True
        state.draft.return_date = None
        state.step = "pick_max_price"
        store.save(chat_id, state)
        await query.edit_message_text(t("pick_max_price", state.lang))
        return

    if data.startswith("hub:"):
        code = data.split(":")[1].upper()
        if state.step == "pick_origin":
            state.draft.origin = code
            state.step = "pick_destination"
            store.save(chat_id, state)
            await query.edit_message_text(t("pick_destination", state.lang))
            await context.bot.send_message(
                chat_id,
                t("pick_destination", state.lang),
                reply_markup=hub_keyboard(state.lang, exclude=code),
            )
        elif state.step == "pick_destination":
            if code == state.draft.origin:
                await query.edit_message_text(t("same_origin_dest", state.lang))
                return
            state.draft.destination = code
            state.step = "pick_departure"
            store.save(chat_id, state)
            await query.edit_message_text(t("pick_departure", state.lang))
            await context.bot.send_message(
                chat_id,
                t("pick_departure", state.lang),
                reply_markup=month_keyboard("dep", state.lang),
            )
        return

    if data.startswith("book:"):
        idx = int(data.split(":")[1])
        quotes: list[FareQuote] = context.user_data.get("last_quotes", [])
        if 0 <= idx < len(quotes):
            await context.bot.send_message(chat_id, quotes[idx].book_url)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_chat or not update.effective_message:
        return
    text = (update.effective_message.text or "").strip()
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    lang = state.lang

    if text in (t("menu_cancel", "en"), t("menu_cancel", "ar")):
        await cancel_cmd(update, context)
        return

    if state.step == "await_key":
        if store.verify_key(chat_id, text):
            state = store.get(chat_id)
            await update.effective_message.reply_text(t("access_ok", lang))
            await update.effective_message.reply_text(
                t("pick_origin", lang),
                reply_markup=menu_keyboard(lang),
            )
            await _prompt_origin(context, chat_id, lang)
        else:
            await update.effective_message.reply_text(t("access_denied", lang))
        return

    if not state.unlocked:
        state.step = "await_key"
        store.save(chat_id, state)
        await update.effective_message.reply_text(t("enter_access_key", lang))
        return

    if text in (t("menu_language", "en"), t("menu_language", "ar")):
        await language_cmd(update, context)
        return

    if text in (t("menu_new", "en"), t("menu_new", "ar")):
        await _begin_search(update, context)
        return

    if text in (t("menu_origin", "en"), t("menu_origin", "ar")):
        state.step = "pick_origin"
        store.save(chat_id, state)
        await _prompt_origin(context, chat_id, lang)
        return

    if text in (t("menu_destination", "en"), t("menu_destination", "ar")):
        state.step = "pick_destination"
        store.save(chat_id, state)
        await update.effective_message.reply_text(
            t("pick_destination", lang),
            reply_markup=hub_keyboard(lang, exclude=state.draft.origin),
        )
        return

    if text in (t("menu_dates", "en"), t("menu_dates", "ar")):
        state.step = "pick_departure"
        store.save(chat_id, state)
        await update.effective_message.reply_text(
            t("pick_departure", lang),
            reply_markup=month_keyboard("dep", lang),
        )
        return

    if text in (t("menu_price", "en"), t("menu_price", "ar")):
        state.step = "pick_max_price"
        store.save(chat_id, state)
        await update.effective_message.reply_text(t("pick_max_price", lang))
        return

    if state.step == "pick_origin":
        code = text.upper()
        if not is_valid_iata(code):
            await update.effective_message.reply_text(t("invalid_iata", lang))
            return
        state.draft.origin = code
        state.step = "pick_destination"
        store.save(chat_id, state)
        await update.effective_message.reply_text(
            t("pick_destination", lang),
            reply_markup=hub_keyboard(lang, exclude=code),
        )
        return

    if state.step == "pick_destination":
        code = text.upper()
        if not is_valid_iata(code):
            await update.effective_message.reply_text(t("invalid_iata", lang))
            return
        if code == state.draft.origin:
            await update.effective_message.reply_text(t("same_origin_dest", lang))
            return
        state.draft.destination = code
        state.step = "pick_departure"
        store.save(chat_id, state)
        await update.effective_message.reply_text(
            t("pick_departure", lang),
            reply_markup=month_keyboard("dep", lang),
        )
        return

    if state.step == "pick_departure":
        dep = parse_user_date(text)
        if not dep or dep < today_riyadh():
            await update.effective_message.reply_text(t("invalid_date", lang))
            return
        state.draft.departure = dep
        state.step = "pick_return"
        store.save(chat_id, state)
        await update.effective_message.reply_text(
            t("pick_return", lang),
            reply_markup=one_way_keyboard(lang),
        )
        await update.effective_message.reply_text(
            t("pick_return", lang),
            reply_markup=month_keyboard("ret", lang),
        )
        return

    if state.step == "pick_return":
        if text in (t("one_way", "en"), t("one_way", "ar")):
            state.draft.one_way = True
            state.draft.return_date = None
            state.step = "pick_max_price"
            store.save(chat_id, state)
            await update.effective_message.reply_text(t("pick_max_price", lang))
            return
        ret = parse_user_date(text)
        if not ret or state.draft.departure and ret <= state.draft.departure:
            await update.effective_message.reply_text(t("invalid_date", lang))
            return
        state.draft.return_date = ret
        state.draft.one_way = False
        state.step = "pick_max_price"
        store.save(chat_id, state)
        await update.effective_message.reply_text(t("pick_max_price", lang))
        return

    if state.step == "pick_max_price":
        if not re.fullmatch(r"\d{2,7}", text):
            await update.effective_message.reply_text(t("invalid_price", lang))
            return
        state.draft.max_price_sar = int(text)
        state.step = "idle"
        store.save(chat_id, state)
        await _run_search(update, context)
        return

    if state.draft.max_price_sar and state.draft.origin and state.draft.destination and state.draft.departure:
        await _run_search(update, context)


async def _begin_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    if not state.unlocked:
        state.step = "await_key"
        store.save(chat_id, state)
        await update.effective_message.reply_text(t("enter_access_key", state.lang))
        return
    state.step = "pick_origin"
    store.save(chat_id, state)
    await update.effective_message.reply_text(
        t("pick_origin", state.lang),
        reply_markup=menu_keyboard(state.lang),
    )
    await _prompt_origin(context, chat_id, state.lang)


async def _prompt_origin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: Lang) -> None:
    await context.bot.send_message(
        chat_id,
        t("pick_origin", lang),
        reply_markup=hub_keyboard(lang),
    )


def _format_quote(lang: Lang, quote: FareQuote, idx: int) -> str:
    route = f"{quote.origin} → {quote.destination}"
    dep = quote.departure.strftime("%d/%m")
    if quote.return_date:
        dates = f"{t('outbound', lang)} {dep} · {t('return', lang)} {quote.return_date.strftime('%d/%m')}"
    else:
        dates = f"{t('outbound', lang)} {dep}"
    price = f"SAR {quote.price_sar:,}"
    over = f" · {t('over_budget', lang)}" if quote.over_budget else ""
    return f"{route}\n{dates}\n{price}{over}"


async def _run_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    lang = state.lang
    draft = state.draft
    if not (
        draft.origin
        and draft.destination
        and draft.departure
        and draft.max_price_sar
    ):
        await update.effective_message.reply_text(t("pick_origin", lang))
        return

    ret = None if draft.one_way else draft.return_date
    if not draft.one_way and ret is None:
        await update.effective_message.reply_text(t("pick_return", lang))
        return

    status = await update.effective_message.reply_text(t("searching", lang))
    quotes_svc = _quotes(context)
    try:
        exact, flex = await quotes_svc.search(
            draft.origin,
            draft.destination,
            draft.departure,
            ret,
            draft.max_price_sar,
        )
    except Exception:
        logger.exception("search failed")
        await status.edit_text(t("quote_failed", lang))
        return

    if not exact and not flex:
        await status.edit_text(t("quote_failed", lang))
        return

    lines: list[str] = []
    all_quotes: list[FareQuote] = []
    if exact:
        lines.append(t("section_exact", lang))
        for q in exact:
            lines.append(_format_quote(lang, q))
            all_quotes.append(q)
    elif flex:
        lines.append(t("no_under_budget", lang))

    if flex:
        lines.append(t("section_flex", lang))
        for q in flex:
            lines.append(_format_quote(lang, q))
            all_quotes.append(q)

    lines.append(t("disclaimer", lang))
    context.user_data["last_quotes"] = all_quotes

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for i, q in enumerate(all_quotes):
        buttons.append(
            InlineKeyboardButton(
                f"{t('book', lang)} {q.origin}→{q.destination} SAR {q.price_sar}",
                url=q.book_url,
            )
        )
    markup = InlineKeyboardMarkup([[b] for b in buttons]) if buttons else None
    await status.edit_text("\n\n".join(lines), reply_markup=markup)


def build_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("help", help_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("lock", lock_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("language", language_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("cancel", cancel_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("search", search_cmd, filters=PRIVATE))
    application.add_handler(
        MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, on_text)
    )
    from telegram.ext import CallbackQueryHandler

    application.add_handler(CallbackQueryHandler(on_language_callback, pattern=r"^lang:"))
    application.add_handler(CallbackQueryHandler(on_callback))
