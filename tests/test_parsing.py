import datetime

import pytest

from src.parsing.categories import categorize
from src.parsing.transactions import norm, parse

BOOKED = datetime.date(2026, 10, 5)
CARD = "Platba kartou"


def card(info: str, amount: float = -250.5, currency: str = "CZK"):
    return parse(CARD, info, amount, currency, BOOKED)


# ---------- card purchases ----------

def test_full_czech_purchase():
    p = card("Nákup: Lidl, Brno, 60200, CZE, dne 3.10.2026, částka 120.00 CZK")
    assert p.kind == "card_purchase"
    assert p.parse_ok is True
    assert p.merchant_raw == "Lidl"
    assert p.merchant_key == "lidl"
    assert p.city == "Brno"
    assert p.country == "CZE"
    assert p.purchase_date == datetime.date(2026, 10, 3)
    assert p.orig_amount == 120.0
    assert p.orig_currency == "CZK"
    assert p.category == "groceries"


def test_foreign_currency_purchase_keeps_both_amounts():
    p = card("Nákup: Starbucks, Wien, AUT, dne 1.9.2026, částka 5.50 EUR", -140.0)
    assert p.amount == -140.0 and p.currency == "CZK"      # what hit the account
    assert p.orig_amount == 5.5 and p.orig_currency == "EUR"  # what the shop charged
    assert p.country == "AUT"
    assert p.city == "Wien"
    assert p.category == "dining"


def test_booked_fields_pass_through():
    p = card("Nákup: Lidl, Brno, CZE, dne 3.10.2026, částka 120.00 CZK", -99.9)
    assert p.amount == -99.9
    assert p.currency == "CZK"
    assert p.booked_date == BOOKED


def test_single_digit_day_and_month_in_date():
    p = card("Nákup: Lidl, Brno, CZE, dne 3.1.2026, částka 10.00 CZK")
    assert p.purchase_date == datetime.date(2026, 1, 3)


def test_prefix_is_optional():
    p = card("Lidl, Brno, CZE, dne 3.10.2026, částka 120.00 CZK")
    assert p.merchant_raw == "Lidl"
    assert p.parse_ok is True


def test_unknown_merchant_is_uncategorized():
    p = card("Nákup: Neznamy Obchod, Praha, CZE, dne 3.10.2026, částka 50.00 CZK")
    assert p.parse_ok is True
    assert p.category == "uncategorized"


def test_unparseable_card_text_is_flagged_not_crashing():
    p = card("Nákup: something totally different")
    assert p.kind == "card_purchase"
    assert p.parse_ok is False
    assert p.merchant_raw is None
    assert p.category is None
    assert p.amount == -250.5  # booked data still kept


def test_tail_only_has_no_merchant():
    p = card("Nákup: dne 3.10.2026, částka 50.00 CZK")
    assert p.parse_ok is False


# ---------- non-card kinds ----------

def test_internal_transfer():
    p = parse("Platba převodem uvnitř banky", "to savings", -5000, "CZK", BOOKED)
    assert p.kind == "transfer_internal"
    assert p.parse_ok is True
    assert p.category == "transfer"


def test_incoming_payment_is_income():
    p = parse("Okamžitá příchozí platba", "salary", 45000, "CZK", BOOKED)
    assert p.kind == "transfer_in"
    assert p.category == "income"


def test_unknown_type_is_other_and_not_ok():
    p = parse("Something new", "whatever", -10, "CZK", BOOKED)
    assert p.kind == "other"
    assert p.parse_ok is False


# ---------- norm ----------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Žabka Praha", "zabka praha"),
        ("  Lidl   Brno ", "lidl brno"),
        ("Albert Vam Dekuje", "albert"),
        ("Alza.cz a.s.", "alza.cz"),
        ("Dopravní podnik", "dopravni podnik"),
    ],
)
def test_norm(raw, expected):
    assert norm(raw) == expected


# ---------- categorize ----------

@pytest.mark.parametrize(
    "key, category",
    [
        ("lidl", "groceries"),
        ("lidl dekuje za nakup", "groceries"),  # substring match
        ("zabka praha", "groceries"),
        ("uber trip", "transport"),
        ("netflix.com", "subscriptions"),
        ("mol praha", "transport"),  # "mol " keyword needs the trailing space
        ("totally unknown shop", "uncategorized"),
    ],
)
def test_categorize_by_merchant(key, category):
    assert categorize("card_purchase", key) == category


def test_categorize_kind_overrides_merchant():
    assert categorize("transfer_internal", "lidl") == "transfer"
    assert categorize("transfer_in", None) == "income"


def test_categorize_without_merchant_is_none():
    assert categorize("card_purchase", None) is None
    assert categorize("card_purchase", "") is None
