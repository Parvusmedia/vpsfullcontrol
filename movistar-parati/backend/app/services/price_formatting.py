"""Centralized money formatting and installment display rules."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

MONEY_TOLERANCE = Decimal("0.01")
TWOPLACES = Decimal("0.01")


def _to_decimal(value: float | int | str | Decimal | None) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def round_money(value: float | int | str | None) -> float | None:
    dec = _to_decimal(value)
    if dec is None:
        return None
    return float(dec.quantize(TWOPLACES, rounding=ROUND_HALF_UP))


def round_monthly(value: float | int | str | None) -> float | None:
    return round_money(value)


def format_eur(
    amount: float | int | str | None,
    *,
    per_month: bool = False,
) -> str:
    dec = _to_decimal(amount)
    if dec is None:
        return "—"
    quantized = dec.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    if quantized == quantized.to_integral_value():
        text = f"{int(quantized)}"
    else:
        text = f"{quantized:.2f}".replace(".", ",")
    suffix = " €/mes" if per_month else " €"
    return f"{text}{suffix}"


def installment_product_matches(
    monthly: float | None,
    months: int | None,
    total: float | None,
) -> bool:
    monthly_dec = _to_decimal(monthly)
    total_dec = _to_decimal(total)
    if monthly_dec is None or total_dec is None or not months:
        return False
    computed = monthly_dec * months
    return abs(computed - total_dec) <= MONEY_TOLERANCE


InstallmentStyle = Literal["exact", "approx"]


def installment_display_style(
    monthly: float | None,
    months: int | None,
    total: float | None,
) -> InstallmentStyle:
    if installment_product_matches(monthly, months, total):
        return "exact"
    return "approx"


def format_monthly_phrase(
    monthly: float | None,
    *,
    style: InstallmentStyle = "exact",
) -> str:
    if monthly is None:
        return "cuotas"
    amount = format_eur(monthly, per_month=True)
    if style == "approx":
        return f"desde {amount}"
    return amount


def format_installment_summary(
    monthly: float | None,
    months: int | None,
    total: float | None,
    *,
    include_total: bool = True,
    client_label: str = "cliente Movistar",
) -> str:
    if monthly is None and total is None:
        return ""
    months = months or 48
    style = installment_display_style(monthly, months, total)
    monthly_text = format_monthly_phrase(monthly, style=style)

    if not include_total or total is None:
        return f"En <b>{months} cuotas</b> de <b>{monthly_text}</b> <i>({client_label})</i>"

    total_text = format_eur(total)
    if style == "exact":
        return (
            f"En <b>{months} cuotas</b> de <b>{monthly_text}</b> "
            f"(<b>{total_text}</b> en total, {client_label})"
        )
    return (
        f"En <b>{months} cuotas</b> de <b>{monthly_text}</b> "
        f"(total <b>{total_text}</b>, {client_label})"
    )


def format_installment_compact(
    monthly: float | None,
    months: int | None,
    total: float | None,
) -> str:
    months = months or 48
    style = installment_display_style(monthly, months, total)
    monthly_text = format_monthly_phrase(monthly, style=style)
    if total is None:
        return f"{monthly_text} × {months}"
    total_text = format_eur(total)
    if style == "exact":
        return f"{monthly_text} × {months} — total {total_text}"
    return f"{monthly_text} × {months} (total {total_text})"
