from app.services.price_formatting import (
    format_eur,
    format_installment_compact,
    format_installment_summary,
    installment_product_matches,
    round_monthly,
)


def test_round_monthly_two_decimals():
    assert round_monthly(8.505) == 8.51
    assert round_monthly(8.5) == 8.5
    assert round_monthly(14) == 14.0


def test_format_eur_integer():
    assert format_eur(14, per_month=True) == "14 €/mes"
    assert format_eur(671) == "671 €"


def test_format_eur_decimal_spanish():
    assert format_eur(8.5, per_month=True) == "8,50 €/mes"
    assert format_eur(0.5, per_month=True) == "0,50 €/mes"
    assert format_eur(4.5, per_month=True) == "4,50 €/mes"


def test_installment_exact_match():
    assert installment_product_matches(14, 48, 672) is True
    assert installment_product_matches(14, 48, 671) is False


def test_installment_summary_exact():
    text = format_installment_summary(14, 48, 672)
    assert "14 €/mes" in text
    assert "672 €" in text
    assert "desde" not in text


def test_installment_summary_approx():
    text = format_installment_summary(14, 48, 671)
    assert "desde 14 €/mes" in text
    assert "671 €" in text


def test_installment_compact_approx():
    text = format_installment_compact(14, 48, 671)
    assert "desde 14 €/mes" in text
    assert "671 €" in text
