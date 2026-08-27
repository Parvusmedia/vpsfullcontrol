"""Conversational search result formatting."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from flightsdemobot.hubs import hub_label
from flightsdemobot.i18n import Lang, t
from flightsdemobot.keyboards import hide_keyboard
from flightsdemobot.saudia.client import FareQuote

APP_ROOT = Path(__file__).resolve().parents[2]
SAUDIA_LOGO_PATH = APP_ROOT / "assets" / "saudia-logo.png"
SAR_PER_USD = 3.75


def _usd_estimate(sar: int) -> int:
    return max(1, int(round(sar / SAR_PER_USD)))


def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _city(code: str, lang: Lang) -> str:
    return hub_label(code, lang)


def _is_demo_quote(quote: FareQuote) -> bool:
    return quote.source in ("demo", "mock")


def _fare_badge(lang: Lang, quote: FareQuote) -> str:
    if _is_demo_quote(quote):
        return t("result_demo_badge", lang)
    if quote.is_exact and quote.source in ("amadeus", "saudia_scrape"):
        return t("result_exact_badge", lang)
    return t("result_indicative_badge", lang)


def format_quote_fare(lang: Lang, quote: FareQuote) -> str:
    origin = _city(quote.origin, lang)
    dest = _city(quote.destination, lang)
    sar = f"{quote.price_sar:,}"
    usd = f"{_usd_estimate(quote.price_sar):,}"
    badge = _fare_badge(lang, quote)
    if quote.return_date:
        return t(
            "result_fare_round",
            lang,
            badge=badge,
            origin=origin,
            destination=dest,
            dep=_fmt_date(quote.departure),
            ret=_fmt_date(quote.return_date),
            sar=sar,
            usd=usd,
        )
    return t(
        "result_fare_oneway",
        lang,
        badge=badge,
        origin=origin,
        destination=dest,
        dep=_fmt_date(quote.departure),
        sar=sar,
        usd=usd,
    )


def _flex_offset_label(lang: Lang, days: int) -> str:
    if days < 0:
        return t("flex_offset_before", lang, n=str(abs(days)))
    return t("flex_offset_after", lang, n=str(days))


def format_flex_line(
    lang: Lang,
    quote: FareQuote,
    ref_departure: date,
    ref_price: int,
) -> str:
    dep = quote.departure.strftime("%d/%m")
    if quote.return_date:
        dates = f"{dep} → {quote.return_date.strftime('%d/%m')}"
    else:
        dates = dep
    sar = f"{quote.price_sar:,}"
    days = (quote.departure - ref_departure).days
    offset = _flex_offset_label(lang, days)
    savings = ref_price - quote.price_sar
    save = t("flex_save", lang, amount=f"{savings:,}") if savings > 0 else ""
    over = f" {t('over_budget', lang)}" if quote.over_budget else ""
    return t(
        "result_flex_line",
        lang,
        offset=offset,
        origin=_city(quote.origin, lang),
        dest=_city(quote.destination, lang),
        dates=dates,
        sar=sar,
        save=save,
        over=over,
    )


def build_results_caption(
    lang: Lang,
    exact: list[FareQuote],
    flex: list[FareQuote],
    *,
    disclaimer_seen: bool,
) -> str:
    parts: list[str] = []
    all_quotes = list(exact) + list(flex)
    if any(_is_demo_quote(q) for q in all_quotes):
        parts.append(t("result_demo_header", lang))
        parts.append("")

    ref_quote: FareQuote | None = None
    if exact:
        ref_quote = exact[0]
        parts.append(format_quote_fare(lang, exact[0]))
        if _is_demo_quote(exact[0]):
            parts.append("")
            parts.append(t("result_demo_notice", lang))
        elif not exact[0].is_exact or exact[0].source == "network_month_floor":
            parts.append("")
            parts.append(t("result_indicative", lang))
    elif flex:
        ref_quote = flex[0]
        parts.append(t("no_under_budget", lang))
        parts.append("")
        parts.append(format_quote_fare(lang, flex[0]))
        if _is_demo_quote(flex[0]):
            parts.append("")
            parts.append(t("result_demo_notice", lang))
        elif not flex[0].is_exact or flex[0].source == "network_month_floor":
            parts.append("")
            parts.append(t("result_indicative", lang))

    flex_lines = flex if exact else flex[1:]
    if flex_lines and ref_quote:
        parts.append("")
        parts.append(t("result_flex_header", lang))
        ref_dep = ref_quote.departure
        ref_price = ref_quote.price_sar
        for q in flex_lines:
            parts.append(format_flex_line(lang, q, ref_dep, ref_price))

    parts.append("")
    parts.append(t("book_tip", lang))
    parts.append("")
    parts.append(t("disclaimer_short", lang))
    return "\n".join(parts)


def _trim_caption_for_photo(caption: str, max_len: int = 1024) -> str:
    if len(caption) <= max_len:
        return caption
    note = "\n\n…"
    return caption[: max_len - len(note)].rstrip() + note


def build_results_markup(lang: Lang, quotes: list[FareQuote]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, q in enumerate(quotes):
        label_key = "book_button_demo" if _is_demo_quote(q) else "book_button"
        rows.append(
            [
                InlineKeyboardButton(
                    t(label_key, lang, sar=f"{q.price_sar:,}"),
                    url=q.book_url,
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(t("search_again", lang), callback_data="action:search")]
    )
    return InlineKeyboardMarkup(rows)


async def send_search_results(
    bot: Bot,
    chat_id: int,
    lang: Lang,
    exact: list[FareQuote],
    flex: list[FareQuote],
    *,
    disclaimer_seen: bool,
) -> list[FareQuote]:
    all_quotes: list[FareQuote] = []
    if exact:
        all_quotes.extend(exact)
    all_quotes.extend(flex)
    caption = build_results_caption(lang, exact, flex, disclaimer_seen=disclaimer_seen)
    markup = build_results_markup(lang, all_quotes)
    photo_caption = _trim_caption_for_photo(caption)

    if SAUDIA_LOGO_PATH.is_file():
        try:
            with SAUDIA_LOGO_PATH.open("rb") as logo:
                await bot.send_photo(
                    chat_id,
                    logo,
                    caption=photo_caption,
                    reply_markup=markup,
                )
        except Exception:
            await bot.send_message(chat_id, caption, reply_markup=markup)
    else:
        await bot.send_message(chat_id, caption, reply_markup=markup)
    try:
        rm = await bot.send_message(chat_id, "\u2060", reply_markup=hide_keyboard())
        await bot.delete_message(chat_id, rm.message_id)
    except Exception:
        pass
    return all_quotes
