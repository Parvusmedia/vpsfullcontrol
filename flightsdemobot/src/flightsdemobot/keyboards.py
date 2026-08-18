"""Telegram keyboards."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from flightsdemobot.hubs import SA_HUBS, hub_label
from flightsdemobot.i18n import Lang, t


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t("lang_en", "en"), callback_data="lang:en"),
                InlineKeyboardButton(t("lang_ar", "ar"), callback_data="lang:ar"),
            ]
        ]
    )


def hub_keyboard(lang: Lang, exclude: str | None = None) -> InlineKeyboardMarkup:
    exclude = (exclude or "").upper()
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for hub in SA_HUBS:
        if hub.code == exclude:
            continue
        label = hub_label(hub.code, lang)
        row.append(InlineKeyboardButton(label, callback_data=f"hub:{hub.code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def one_way_keyboard(lang: Lang) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("one_way", lang), callback_data="trip:ow")]]
    )


def menu_keyboard(lang: Lang) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(t("menu_new", lang)),
                KeyboardButton(t("menu_origin", lang)),
            ],
            [
                KeyboardButton(t("menu_destination", lang)),
                KeyboardButton(t("menu_dates", lang)),
            ],
            [
                KeyboardButton(t("menu_price", lang)),
                KeyboardButton(t("menu_language", lang)),
            ],
            [KeyboardButton(t("menu_cancel", lang))],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
