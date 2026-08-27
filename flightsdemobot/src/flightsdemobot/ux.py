"""Conversational UX helpers and optional hub imagery."""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from pathlib import Path

from telegram import (
    Bot,
    CallbackQuery,
    InlineKeyboardMarkup,
    MenuButtonCommands,
    Message,
    ReplyKeyboardRemove,
)
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from flightsdemobot.hubs import hub_label
from flightsdemobot.i18n import Lang, t
from flightsdemobot.keyboards import hide_keyboard
from flightsdemobot.storage import ChatState, Store

logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parents[2]
MENU_BANNER_PATH = APP_ROOT / "assets" / "saudia-menu-banner.png"


async def clear_flow_messages(bot: Bot, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove transient picker/ack messages so results sit at the bottom."""
    ids = list(context.user_data.get("flow_msg_ids", []))
    context.user_data["flow_msg_ids"] = []
    context.user_data.pop("last_flow_msg", None)
    for mid in ids:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass


def track_flow_message(context: ContextTypes.DEFAULT_TYPE, message: Message) -> None:
    ids = context.user_data.setdefault("flow_msg_ids", [])
    if message.message_id not in ids:
        ids.append(message.message_id)
    context.user_data["last_flow_msg"] = message.message_id


async def setup_bot_menu(bot: Bot, chat_id: int | None = None) -> None:
    """Native Telegram commands menu (no web app). chat_id resets per-user cached buttons."""
    try:
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonCommands(),
        )
    except Exception as exc:
        logger.warning("set_chat_menu_button failed: %s", exc)


# Wikimedia thumbnails — stable HTTPS URLs for major Saudi hubs.
HUB_IMAGES: dict[str, str] = {
    "JED": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/"
        "King_Abdulaziz_International_Airport_%28Jeddah%29_terminal.jpg/"
        "400px-King_Abdulaziz_International_Airport_%28Jeddah%29_terminal.jpg"
    ),
    "RUH": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/"
        "King_Khalid_International_Airport_Terminal_5.jpg/"
        "400px-King_Khalid_International_Airport_Terminal_5.jpg"
    ),
    "DMM": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/"
        "King_Fahd_International_Airport.jpg/400px-King_Fahd_International_Airport.jpg"
    ),
    "MED": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/"
        "Prince_Mohammad_bin_Abdulaziz_Airport.jpg/"
        "400px-Prince_Mohammad_bin_Abdulaziz_Airport.jpg"
    ),
}


async def send_menu_message(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardRemove | None = None,
) -> Message:
    """Send a picker/menu (text + inline buttons). Banner is only on the welcome message."""
    return await bot.send_message(chat_id, text, reply_markup=reply_markup)


async def edit_menu_message(
    query: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Edit an inline menu message. Legacy photo menus are replaced with plain text."""
    message = query.message
    if message and message.photo:
        try:
            await message.delete()
        except Exception:
            pass
        await send_menu_message(
            message.get_bot(),
            message.chat_id,
            text,
            reply_markup=reply_markup,
        )
        return
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception:
        if message:
            await send_menu_message(
                message.get_bot(),
                message.chat_id,
                text,
                reply_markup=reply_markup,
            )


async def edit_message_to_text(message: Message, text: str) -> Message:
    """Edit a status line on either a text message or a photo+caption menu."""
    try:
        return await message.edit_text(text)
    except Exception:
        return await message.edit_caption(text)


async def edit_chat_message_to_text(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
) -> Message | None:
    try:
        return await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    try:
        return await bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id)
    except Exception:
        return None


async def send_welcome_banner(bot: Bot, chat_id: int, lang: Lang, text: str) -> None:
    """Initial hero banner — shown once after unlock / language pick, not on every step."""
    if MENU_BANNER_PATH.is_file() and len(text) <= 1024:
        try:
            with MENU_BANNER_PATH.open("rb") as banner:
                await bot.send_photo(
                    chat_id,
                    banner,
                    caption=text,
                    reply_markup=hide_keyboard(),
                )
                return
        except Exception as exc:
            logger.debug("welcome banner send failed: %s", exc)
    await bot.send_message(chat_id, text, reply_markup=hide_keyboard())


async def maybe_send_hub_photo(bot: Bot, chat_id: int, code: str) -> None:
    url = HUB_IMAGES.get(code.upper())
    if not url:
        return
    try:
        await bot.send_photo(chat_id, url)
    except Exception as exc:
        logger.debug("hub photo skipped %s: %s", code, exc)


def cabin_display(lang: Lang, cabin: str) -> str:
    if (cabin or "").lower() == "business":
        return t("cabin_label_business", lang)
    return t("cabin_label_economy", lang)


def format_status_summary(state: ChatState, lang: Lang) -> str:
    draft = state.draft
    lines = [t("menu_summary_title", lang), ""]
    if draft.origin:
        lines.append(
            t(
                "status_origin",
                lang,
                city=hub_label(draft.origin, lang),
            )
        )
    else:
        lines.append(t("status_origin_missing", lang))
    if draft.destination:
        lines.append(
            t(
                "status_destination",
                lang,
                city=hub_label(draft.destination, lang),
            )
        )
    else:
        lines.append(t("status_destination_missing", lang))
    if draft.departure:
        dep = draft.departure.strftime("%d/%m/%Y")
        if draft.one_way:
            lines.append(t("status_dates_oneway", lang, date=dep))
        elif draft.return_date:
            ret = draft.return_date.strftime("%d/%m/%Y")
            lines.append(t("status_dates_round", lang, dep=dep, ret=ret))
        else:
            lines.append(t("status_dates_dep_only", lang, dep=dep))
    else:
        lines.append(t("status_dates_missing", lang))
    if draft.max_price_sar:
        lines.append(t("status_price", lang, price=f"{draft.max_price_sar:,}"))
    else:
        lines.append(t("status_price_missing", lang))
    if draft.adults:
        lines.append(t("status_passengers", lang, count=str(draft.adults)))
    else:
        lines.append(t("status_passengers_missing", lang))
    if draft.cabin:
        lines.append(t("status_cabin", lang, cabin=cabin_display(lang, draft.cabin)))
    else:
        lines.append(t("status_cabin_missing", lang))
    lines.append("")
    lines.append(t("menu_summary_hint", lang))
    return "\n".join(lines)


async def show_menu_summary(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    store: Store,
    lang: Lang,
) -> None:
    state = store.get(chat_id)
    await context.bot.send_message(
        chat_id,
        format_status_summary(state, lang),
        reply_markup=hide_keyboard(),
    )


async def ack_origin(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    code: str,
) -> None:
    city = hub_label(code, lang)
    await context.bot.send_message(chat_id, t("ack_origin", lang, city=city))
    await maybe_send_hub_photo(context.bot, chat_id, code)


async def ack_destination(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    origin: str,
    destination: str,
) -> None:
    await context.bot.send_message(
        chat_id,
        t(
            "ack_destination",
            lang,
            origin=hub_label(origin, lang),
            destination=hub_label(destination, lang),
        ),
    )
    await maybe_send_hub_photo(context.bot, chat_id, destination)


async def ack_departure(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    departure: date,
) -> None:
    await context.bot.send_message(
        chat_id,
        t("ack_departure", lang, date=departure.strftime("%d/%m/%Y")),
    )


async def ack_return_oneway(context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: Lang) -> None:
    await context.bot.send_message(chat_id, t("ack_oneway", lang))


async def ack_return_round(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    departure: date,
    return_date: date,
) -> None:
    await context.bot.send_message(
        chat_id,
        t(
            "ack_return",
            lang,
            dep=departure.strftime("%d/%m/%Y"),
            ret=return_date.strftime("%d/%m/%Y"),
        ),
    )


async def ack_max_price(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    price: int,
) -> None:
    await context.bot.send_message(
        chat_id,
        t("ack_max_price", lang, price=f"{price:,}"),
    )


async def ack_passengers(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    count: int,
) -> None:
    await context.bot.send_message(
        chat_id,
        t("ack_passengers", lang, count=str(count)),
    )


async def ack_cabin(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lang: Lang,
    cabin: str,
) -> None:
    await context.bot.send_message(
        chat_id,
        t("ack_cabin", lang, cabin=cabin_display(lang, cabin)),
    )


class SearchProgress:
    """Animate the status message and typing indicator while fares load."""

    def __init__(self, bot: Bot, chat_id: int, lang: Lang, status: Message) -> None:
        self._bot = bot
        self._chat_id = chat_id
        self._lang = lang
        self._status = status
        self._stop = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stop = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while not self._stop:
            try:
                await self._bot.send_chat_action(self._chat_id, ChatAction.TYPING)
            except Exception:
                pass
            await asyncio.sleep(4.0)
