"""Telegram bot handlers."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, timedelta

from telegram import BotCommand, Message, Update
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
from flightsdemobot.hubs import hub_label, is_valid_iata
from flightsdemobot.i18n import Lang, t
from flightsdemobot.keyboards import (
    cabin_keyboard,
    hub_keyboard,
    language_keyboard,
    hide_keyboard,
    one_way_keyboard,
    passengers_keyboard,
)
from flightsdemobot.results import send_search_results
from flightsdemobot.saudia.client import FareQuote, QuoteService
from flightsdemobot.storage import SearchDraft, Store
from flightsdemobot.ux import (
    edit_chat_message_to_text,
    edit_menu_message,
    edit_message_to_text,
    ack_departure,
    ack_destination,
    ack_origin,
    ack_passengers,
    ack_return_oneway,
    clear_flow_messages,
    maybe_send_hub_photo,
    send_initial_menu,
    send_menu_message,
    send_welcome_banner,
    SearchProgress,
    setup_bot_menu,
    show_menu_summary,
    track_flow_message,
)

logger = logging.getLogger(__name__)

PRIVATE = filters.ChatType.PRIVATE


def _lang_from_telegram(code: str | None) -> Lang:
    if code and code.lower().startswith("ar"):
        return "ar"
    return "en"


def _needs_language_picker(code: str | None) -> bool:
    if not code:
        return False
    lowered = code.lower()
    return not lowered.startswith("ar") and not lowered.startswith("en")


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
    await setup_bot_menu(context.bot, chat_id=chat_id)
    if state.unlocked:
        await context.bot.send_message(chat_id, "\u2060", reply_markup=hide_keyboard())
        await _begin_search(update, context)
        return
    lang_code = update.effective_user.language_code if update.effective_user else None
    if lang_code:
        state.lang = _lang_from_telegram(lang_code)
    store.save(chat_id, state)
    if _needs_language_picker(lang_code):
        await send_menu_message(
            context.bot,
            chat_id,
            t("choose_language", state.lang),
            reply_markup=language_keyboard(),
        )
        return
    state.step = "await_key"
    store.save(chat_id, state)
    await update.effective_message.reply_text(t("enter_access_key", state.lang))


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
    await send_menu_message(
        context.bot,
        update.effective_chat.id,
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
        reply_markup=hide_keyboard() if state.unlocked else None,
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_private(update) or not update.effective_chat or not update.effective_message:
        return
    store = _store(context)
    chat_id = update.effective_chat.id
    state = store.get(chat_id)
    if not state.unlocked:
        await update.effective_message.reply_text(t("enter_access_key", state.lang))
        return
    await show_menu_summary(context, chat_id, store, state.lang)


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
        await setup_bot_menu(context.bot, chat_id=chat_id)
        await edit_menu_message(query, t("enter_access_key", lang))
        return
    state.step = "idle"
    store.save(chat_id, state)
    await setup_bot_menu(context.bot, chat_id=chat_id)
    await send_welcome_banner(context.bot, chat_id, lang, t("access_ok", lang))
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
        await edit_menu_message(query, 
            t("pick_departure", state.lang),
            reply_markup=day_keyboard("dep", month),
        )
        return

    if data.startswith("dep:d:"):
        state.draft.departure = date.fromisoformat(data.split(":")[2])
        state.step = "pick_return"
        store.save(chat_id, state)
        await edit_menu_message(query, 
            t("ack_departure", state.lang, date=state.draft.departure.strftime("%d/%m/%Y")),
        )
        await send_menu_message(context.bot, chat_id, t("pick_return", state.lang), reply_markup=one_way_keyboard(state.lang),
        )
        await send_menu_message(context.bot, chat_id, t("pick_return", state.lang), reply_markup=month_keyboard("ret", state.lang),
        )
        return

    if data.startswith("ret:m:"):
        month = date.fromisoformat(data.split(":")[2])
        min_d = state.draft.departure or today_riyadh()
        await edit_menu_message(query, 
            t("pick_return", state.lang),
            reply_markup=day_keyboard("ret", month, min_date=min_d + timedelta(days=1)),
        )
        return

    if data.startswith("ret:d:"):
        ret = date.fromisoformat(data.split(":")[2])
        if state.draft.departure and ret <= state.draft.departure:
            await edit_menu_message(query, t("return_before_depart", state.lang))
            return
        state.draft.return_date = ret
        state.draft.one_way = False
        state.step = "pick_max_price"
        store.save(chat_id, state)
        dep = state.draft.departure
        if dep:
            await edit_menu_message(query, 
                t(
                    "ack_return",
                    state.lang,
                    dep=dep.strftime("%d/%m/%Y"),
                    ret=ret.strftime("%d/%m/%Y"),
                ),
            )
        else:
            await edit_menu_message(query, t("ack_oneway", state.lang))
        await context.bot.send_message(chat_id, t("pick_max_price", state.lang))
        return

    if data == "trip:ow":
        state.draft.one_way = True
        state.draft.return_date = None
        state.step = "pick_max_price"
        store.save(chat_id, state)
        await edit_menu_message(query, t("ack_oneway", state.lang))
        await context.bot.send_message(chat_id, t("pick_max_price", state.lang))
        return

    if data.startswith("hub:"):
        code = data.split(":")[1].upper()
        step = state.step
        if step == "idle":
            step = "pick_origin"
            state.step = step
        if step == "pick_origin":
            state.draft.origin = code
            state.step = "pick_destination"
            store.save(chat_id, state)
            city = hub_label(code, state.lang)
            await edit_menu_message(query, t("ack_origin", state.lang, city=city))
            await maybe_send_hub_photo(context.bot, chat_id, code)
            await send_menu_message(context.bot, chat_id, t("pick_destination", state.lang), reply_markup=hub_keyboard(state.lang, exclude=code),
            )
        elif step == "pick_destination":
            if code == state.draft.origin:
                await edit_menu_message(query, t("same_origin_dest", state.lang))
                return
            origin = state.draft.origin or code
            state.draft.destination = code
            state.step = "pick_departure"
            store.save(chat_id, state)
            await edit_menu_message(query, 
                t(
                    "ack_destination",
                    state.lang,
                    origin=hub_label(origin, state.lang),
                    destination=hub_label(code, state.lang),
                ),
            )
            await maybe_send_hub_photo(context.bot, chat_id, code)
            await send_menu_message(context.bot, chat_id, t("pick_departure", state.lang), reply_markup=month_keyboard("dep", state.lang),
            )
        return

    if data == "action:search":
        await clear_flow_messages(context.bot, chat_id, context)
        state.draft = SearchDraft()
        state.step = "pick_origin"
        store.save(chat_id, state)
        await query.edit_message_reply_markup(reply_markup=None)
        await _prompt_origin(
            context,
            chat_id,
            state.lang,
            with_banner=True,
        )
        return

    if data.startswith("passengers:"):
        count = int(data.split(":")[1])
        state.draft.adults = max(1, min(count, 9))
        state.step = "pick_cabin"
        store.save(chat_id, state)
        await edit_menu_message(query, 
            t("pick_cabin", state.lang),
            reply_markup=cabin_keyboard(state.lang),
        )
        if query.message:
            track_flow_message(context, query.message)
        return

    if data.startswith("cabin:"):
        cabin = data.split(":")[1]
        if cabin not in ("economy", "business"):
            return
        state.draft.cabin = cabin
        state.step = "idle"
        store.save(chat_id, state)
        await edit_menu_message(query, t("searching", state.lang))
        await _run_search(
            context,
            chat_id,
            state.lang,
            status=query.message,
        )
        return


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

    if text in (t("menu_open", "en"), t("menu_open", "ar")):
        await setup_bot_menu(context.bot, chat_id=chat_id)
        if state.unlocked:
            await show_menu_summary(context, chat_id, store, lang)
        else:
            await update.effective_message.reply_text(t("enter_access_key", lang))
        return

    if state.step == "await_key":
        if store.verify_key(chat_id, text):
            state = store.get(chat_id)
            await setup_bot_menu(context.bot, chat_id=chat_id)
            await send_welcome_banner(
                context.bot,
                chat_id,
                lang,
                t("access_ok", lang),
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
        await send_menu_message(context.bot, chat_id, t("pick_destination", lang), reply_markup=hub_keyboard(lang, exclude=state.draft.origin))
        return

    if text in (t("menu_dates", "en"), t("menu_dates", "ar")):
        state.step = "pick_departure"
        store.save(chat_id, state)
        await send_menu_message(context.bot, chat_id, t("pick_departure", lang), reply_markup=month_keyboard("dep", lang))
        return

    if text in (t("menu_price", "en"), t("menu_price", "ar")):
        state.step = "pick_max_price"
        store.save(chat_id, state)
        await update.effective_message.reply_text(t("pick_max_price", lang))
        return

    if text in (t("menu_passengers", "en"), t("menu_passengers", "ar")):
        state.step = "pick_passengers"
        store.save(chat_id, state)
        await _prompt_passengers(context, chat_id, lang)
        return

    if text in (t("menu_cabin", "en"), t("menu_cabin", "ar")):
        state.step = "pick_cabin"
        store.save(chat_id, state)
        await send_menu_message(context.bot, chat_id, t("pick_cabin", lang), reply_markup=cabin_keyboard(lang))
        return

    if state.step == "pick_origin":
        code = text.upper()
        if not is_valid_iata(code):
            await update.effective_message.reply_text(t("invalid_iata", lang))
            return
        state.draft.origin = code
        state.step = "pick_destination"
        store.save(chat_id, state)
        await ack_origin(context, chat_id, lang, code)
        await send_menu_message(context.bot, chat_id, t("pick_destination", lang), reply_markup=hub_keyboard(lang, exclude=code))
        return

    if state.step == "pick_destination":
        code = text.upper()
        if not is_valid_iata(code):
            await update.effective_message.reply_text(t("invalid_iata", lang))
            return
        if code == state.draft.origin:
            await update.effective_message.reply_text(t("same_origin_dest", lang))
            return
        origin = state.draft.origin or code
        state.draft.destination = code
        state.step = "pick_departure"
        store.save(chat_id, state)
        await ack_destination(context, chat_id, lang, origin, code)
        await send_menu_message(context.bot, chat_id, t("pick_departure", lang), reply_markup=month_keyboard("dep", lang))
        return

    if state.step == "pick_departure":
        dep = parse_user_date(text)
        if not dep or dep < today_riyadh():
            await update.effective_message.reply_text(t("invalid_date", lang))
            return
        state.draft.departure = dep
        state.step = "pick_return"
        store.save(chat_id, state)
        await ack_departure(context, chat_id, lang, dep)
        await send_menu_message(context.bot, chat_id, t("pick_return", lang), reply_markup=one_way_keyboard(lang))
        await send_menu_message(context.bot, chat_id, t("pick_return", lang), reply_markup=month_keyboard("ret", lang))
        return

    if state.step == "pick_return":
        if text in (t("one_way", "en"), t("one_way", "ar")):
            state.draft.one_way = True
            state.draft.return_date = None
            state.step = "pick_max_price"
            store.save(chat_id, state)
            await ack_return_oneway(context, chat_id, lang)
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
        if state.draft.departure:
            await update.effective_message.reply_text(
                t(
                    "ack_return",
                    lang,
                    dep=state.draft.departure.strftime("%d/%m/%Y"),
                    ret=ret.strftime("%d/%m/%Y"),
                ),
            )
        await update.effective_message.reply_text(t("pick_max_price", lang))
        return

    if state.step == "pick_max_price":
        if not re.fullmatch(r"\d{2,7}", text):
            await update.effective_message.reply_text(t("invalid_price", lang))
            return
        state.draft.max_price_sar = int(text)
        state.step = "pick_passengers"
        store.save(chat_id, state)
        msg = await send_menu_message(context.bot, chat_id, t("pick_passengers_after_budget", lang, price=f"{state.draft.max_price_sar:,}"), reply_markup=passengers_keyboard(lang))
        track_flow_message(context, msg)
        return

    if state.step == "pick_passengers":
        if text in (t("passengers_1", "en"), t("passengers_1", "ar")):
            state.draft.adults = 1
        elif text in (t("passengers_2", "en"), t("passengers_2", "ar")):
            state.draft.adults = 2
        elif text in (t("passengers_3", "en"), t("passengers_3", "ar")):
            state.draft.adults = 3
        else:
            msg = await send_menu_message(context.bot, chat_id, t("pick_passengers", lang), reply_markup=passengers_keyboard(lang))
            track_flow_message(context, msg)
            return
        state.step = "pick_cabin"
        store.save(chat_id, state)
        msg = await send_menu_message(context.bot, chat_id, t("pick_cabin", lang), reply_markup=cabin_keyboard(lang))
        track_flow_message(context, msg)
        return

    if state.step == "pick_cabin":
        if text in (t("cabin_economy", "en"), t("cabin_economy", "ar")):
            state.draft.cabin = "economy"
        elif text in (t("cabin_business", "en"), t("cabin_business", "ar")):
            state.draft.cabin = "business"
        else:
            msg = await send_menu_message(context.bot, chat_id, t("pick_cabin", lang), reply_markup=cabin_keyboard(lang))
            track_flow_message(context, msg)
            return
        state.step = "idle"
        store.save(chat_id, state)
        last_id = context.user_data.get("last_flow_msg")
        status: Message | None = None
        if last_id:
            try:
                status = await edit_chat_message_to_text(
                    context.bot,
                    chat_id,
                    last_id,
                    t("searching", lang),
                )
            except Exception:
                status = None
        await _run_search(
            context,
            chat_id,
            lang,
            status=status,
            reply_message=update.effective_message if status is None else None,
        )
        return

    if state.draft.max_price_sar and state.draft.origin and state.draft.destination and state.draft.departure:
        await _run_search(context, chat_id, lang, reply_message=update.effective_message)


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
    state.draft = SearchDraft()
    state.step = "pick_origin"
    store.save(chat_id, state)
    await clear_flow_messages(context.bot, chat_id, context)
    try:
        await context.bot.send_message(chat_id, "\u2060", reply_markup=hide_keyboard())
    except Exception:
        pass
    await _prompt_origin(
        context,
        chat_id,
        state.lang,
        with_banner=True,
    )


async def _prompt_passengers(context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: Lang) -> None:
    store = _store(context)
    state = store.get(chat_id)
    state.step = "pick_passengers"
    store.save(chat_id, state)
    price = state.draft.max_price_sar
    text = (
        t("pick_passengers_after_budget", lang, price=f"{price:,}")
        if price
        else t("pick_passengers", lang)
    )
    msg = await send_menu_message(context.bot, chat_id, text, reply_markup=passengers_keyboard(lang))
    track_flow_message(context, msg)


async def _prompt_origin(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    *,
    with_banner: bool = False,
) -> None:
    store = _store(context)
    state = store.get(chat_id)
    state.step = "pick_origin"
    store.save(chat_id, state)
    text = t("pick_origin_start", lang) if with_banner else t("pick_origin", lang)
    markup = hub_keyboard(lang)
    if with_banner:
        await send_initial_menu(context.bot, chat_id, text, markup)
    else:
        await send_menu_message(context.bot, chat_id, text, reply_markup=markup)


async def _run_search(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    *,
    status: Message | None = None,
    reply_message: Message | None = None,
) -> None:
    store = _store(context)
    state = store.get(chat_id)
    draft = state.draft
    if not (
        draft.origin
        and draft.destination
        and draft.departure
        and draft.max_price_sar
    ):
        await send_menu_message(
            context.bot, chat_id, t("pick_origin", lang), reply_markup=hub_keyboard(lang)
        )
        return

    ret = None if draft.one_way else draft.return_date
    if not draft.one_way and ret is None:
        if reply_message:
            await reply_message.reply_text(t("pick_return", lang))
        else:
            await context.bot.send_message(chat_id, t("pick_return", lang))
        return

    if status is not None:
        try:
            await edit_message_to_text(status, t("searching", lang))
        except Exception:
            status = await context.bot.send_message(chat_id, t("searching", lang))
    elif reply_message:
        status = await reply_message.reply_text(t("searching", lang))
    else:
        status = await context.bot.send_message(chat_id, t("searching", lang))

    progress = SearchProgress(context.bot, chat_id, lang, status)
    await progress.start()
    quotes_svc = _quotes(context)

    async def _do_search(demo_only: bool = False) -> tuple[list[FareQuote], list[FareQuote]]:
        return await quotes_svc.search(
            draft.origin,
            draft.destination,
            draft.departure,
            ret,
            draft.max_price_sar,
            adults=draft.adults,
            cabin=draft.cabin,
            demo_only=demo_only,
        )

    exact: list[FareQuote] = []
    flex: list[FareQuote] = []
    try:
        exact, flex = await asyncio.wait_for(_do_search(), timeout=45.0)
    except asyncio.TimeoutError:
        logger.warning("search timed out for %s-%s", draft.origin, draft.destination)
        try:
            exact, flex = await _do_search(demo_only=True)
        except Exception:
            await progress.stop()
            await edit_message_to_text(status, t("search_timeout", lang))
            return
    except Exception:
        logger.exception("search failed")
        try:
            exact, flex = await _do_search(demo_only=True)
        except Exception:
            await progress.stop()
            await edit_message_to_text(status, t("quote_failed", lang))
            return

    if not exact and not flex:
        try:
            exact, flex = await _do_search(demo_only=True)
        except Exception:
            await progress.stop()
            await edit_message_to_text(status, t("quote_failed", lang))
            return

    await progress.stop()
    await asyncio.sleep(0.05)

    await clear_flow_messages(context.bot, chat_id, context)
    try:
        await status.delete()
    except Exception:
        pass

    all_quotes = await send_search_results(
        context.bot,
        chat_id,
        lang,
        exact,
        flex,
        disclaimer_seen=state.disclaimer_seen,
    )
    context.user_data["last_quotes"] = all_quotes
    if not state.disclaimer_seen:
        state.disclaimer_seen = True
        store.save(chat_id, state)
    logger.info(
        "search ok %s-%s exact=%d flex=%d",
        draft.origin,
        draft.destination,
        len(exact),
        len(flex),
    )


def build_handlers(application: Application) -> None:
    async def post_init(app: Application) -> None:
        await setup_bot_menu(app.bot)
        await app.bot.set_my_commands(
            [
                BotCommand("start", "Welcome & language"),
                BotCommand("search", "New fare search"),
                BotCommand("menu", "Trip summary"),
                BotCommand("language", "English / العربية"),
                BotCommand("help", "How this demo works"),
                BotCommand("cancel", "Cancel current step"),
                BotCommand("lock", "Lock session"),
            ]
        )

    application.post_init = post_init

    application.add_handler(CommandHandler("start", start_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("help", help_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("lock", lock_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("language", language_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("cancel", cancel_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("menu", menu_cmd, filters=PRIVATE))
    application.add_handler(CommandHandler("search", search_cmd, filters=PRIVATE))
    application.add_handler(
        MessageHandler(PRIVATE & filters.TEXT & ~filters.COMMAND, on_text)
    )
    from telegram.ext import CallbackQueryHandler

    application.add_handler(CallbackQueryHandler(on_language_callback, pattern=r"^lang:"))
    application.add_handler(CallbackQueryHandler(on_callback))
