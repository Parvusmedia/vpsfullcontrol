"""Gregorian calendar inline keyboard (Asia/Riyadh)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

RIYADH = ZoneInfo("Asia/Riyadh")


def today_riyadh() -> date:
    return datetime.now(RIYADH).date()


def parse_user_date(text: str) -> date | None:
    text = text.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def month_keyboard(prefix: str, lang: str) -> InlineKeyboardMarkup:
    today = today_riyadh()
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i in range(6):
        month_start = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        label = month_start.strftime("%b %Y")
        row.append(
            InlineKeyboardButton(label, callback_data=f"{prefix}:m:{month_start.isoformat()}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def day_keyboard(prefix: str, month_start: date, min_date: date | None = None) -> InlineKeyboardMarkup:
    if min_date is None:
        min_date = today_riyadh()
    year, month = month_start.year, month_start.month
    first = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    days_in_month = (next_month - first).days
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        if d < min_date:
            continue
        row.append(InlineKeyboardButton(str(day), callback_data=f"{prefix}:d:{d.isoformat()}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)
