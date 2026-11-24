import datetime as dt
import re
from dataclasses import dataclass
from typing import Callable

import vector_db
from src.models import Parsed

TRANSACTIONS = [
    # Czech card purchase, groceries
    Parsed(
        amount=-120.00, currency="CZK", booked_date=dt.date(2026, 10, 4),
        kind="card_purchase", parse_ok=True,
        merchant_raw="Lidl", merchant_key="lidl",
        city="Brno", country="CZE", purchase_date=dt.date(2026, 10, 3),
        orig_amount=120.00, orig_currency="CZK", category="groceries",
    ),
    # Foreign-currency purchase: account in CZK, shop charged EUR
    Parsed(
        amount=-140.00, currency="CZK", booked_date=dt.date(2026, 9, 2),
        kind="card_purchase", parse_ok=True,
        merchant_raw="Starbucks", merchant_key="starbucks",
        city="Wien", country="AUT", purchase_date=dt.date(2026, 9, 1),
        orig_amount=5.50, orig_currency="EUR", category="dining",
    ),
    # Cafe, Prague (matches "kavarna" -> dining)
    Parsed(
        amount=-85.00, currency="CZK", booked_date=dt.date(2026, 10, 5),
        kind="card_purchase", parse_ok=True,
        merchant_raw="Kavárna Slavia", merchant_key="kavarna slavia",
        city="Praha", country="CZE", purchase_date=dt.date(2026, 10, 4),
        orig_amount=85.00, orig_currency="CZK", category="dining",
    ),
    # Cafe, Prague (matches "cafe" -> dining)
    Parsed(
        amount=-95.00, currency="CZK", booked_date=dt.date(2026, 10, 8),
        kind="card_purchase", parse_ok=True,
        merchant_raw="Cafe Savoy", merchant_key="cafe savoy",
        city="Praha", country="CZE", purchase_date=dt.date(2026, 10, 7),
        orig_amount=95.00, orig_currency="CZK", category="dining",
    ),
    # Public transport
    Parsed(
        amount=-30.00, currency="CZK", booked_date=dt.date(2026, 10, 7),
        kind="card_purchase", parse_ok=True,
        merchant_raw="DPP", merchant_key="dpp",
        city="Praha", country="CZE", purchase_date=dt.date(2026, 10, 6),
        orig_amount=30.00, orig_currency="CZK", category="transport",
    ),
    # Subscription billed in USD
    Parsed(
        amount=-549.00, currency="CZK", booked_date=dt.date(2026, 10, 10),
        kind="card_purchase", parse_ok=True,
        merchant_raw="Netflix.com", merchant_key="netflix.com",
        city=None, country="USA", purchase_date=dt.date(2026, 10, 9),
        orig_amount=22.99, orig_currency="USD", category="subscriptions",
    ),
    # Merchant not in the category map
    Parsed(
        amount=-250.00, currency="CZK", booked_date=dt.date(2026, 10, 12),
        kind="card_purchase", parse_ok=True,
        merchant_raw="Neznamy Obchod", merchant_key="neznamy obchod",
        city="Praha", country="CZE", purchase_date=dt.date(2026, 10, 11),
        orig_amount=250.00, orig_currency="CZK", category="uncategorized",
    ),
    # Card text that did not match the expected pattern
    Parsed(
        amount=-99.90, currency="CZK", booked_date=dt.date(2026, 10, 13),
        kind="card_purchase", parse_ok=False,
    ),
    # Internal transfer to savings
    Parsed(
        amount=-5000.00, currency="CZK", booked_date=dt.date(2026, 10, 1),
        kind="transfer_internal", parse_ok=True, category="transfer",
    ),
    # Incoming salary
    Parsed(
        amount=45000.00, currency="CZK", booked_date=dt.date(2026, 10, 1),
        kind="transfer_in", parse_ok=True, category="income",
    ),
    # Unknown transaction type
    Parsed(
        amount=-10.00, currency="CZK", booked_date=dt.date(2026, 10, 14),
        kind="other", parse_ok=False,
    ),
]



@dataclass
class Case:
    name: str
    question: str
    expect_tool: str | None
    check: Callable[[str], bool]


def has(pattern: str) -> Callable[[str], bool]:
    """Answer must match the regex (case-insensitive)."""
    rx = re.compile(pattern, re.IGNORECASE)
    return lambda answer: rx.search(answer) is not None


def lacks(pattern: str) -> Callable[[str], bool]:
    """Answer must NOT match the regex (case-insensitive)."""
    rx = re.compile(pattern, re.IGNORECASE)
    return lambda answer: rx.search(answer) is None


# Expected totals, computed by hand from TRANSACTIONS (transfer_internal excluded):
#   groceries 120 | dining 320 (Starbucks 140, Kavarna Slavia 85, Cafe Savoy 95)
#   transport 30 | subscriptions 549 | uncategorized 250
#   expenses total 1378.9 (9 items) | cafes: 3 visits | September expenses 140
#   October expenses 1238.9 | income 45000 | Netflix (549) is the largest expense
#   non-transfer rows = 10 (used by data_overview)
CASES: list[Case] = [
    Case(
        name="overview_lists_data",
        question="What data do you have?",
        expect_tool="data_overview",
        check=has(r"\b10\b|ten"),
    ),
    Case(
        name="groceries_total",
        question="How much did I spend on groceries?",
        expect_tool="spending_summary",
        check=has(r"\b120(\.0+)?\b.*CZK|CZK.*\b120(\.0+)?\b"),
    ),
    Case(
        name="largest_expense",
        question="What was my biggest purchase?",
        expect_tool="list_transactions",
        check=has(r"Netflix.*549|549.*Netflix"),
    ),
    Case(
        name="income_total",
        question="How much money came into my account?",
        expect_tool="spending_summary",
        check=has(r"45[\s,. ]?000"),
    ),
    Case(
        name="foreign_currency_amount_in_account_currency",
        question="How much did I spend at Starbucks?",
        expect_tool="spending_summary",
        check=has(r"\b140(\.0+)?\b"),  # account amount in CZK, not the 5.50 EUR
    ),
    Case(
        name="september_total",
        question="What did I spend in September 2026?",
        expect_tool="spending_summary",
        check=has(r"\b140(\.0+)?\b"),
    ),
    Case(
        name="october_total_excludes_transfers",
        question="What were my total expenses in October 2026?",
        expect_tool="spending_summary",
        check=has(r"1[\s,. ]?238[.,]9"),  # internal 5000 transfer must not be counted
    ),
    Case(
        name="internal_transfers_not_spending",
        question="How much did I move to my savings account?",
        expect_tool=None,
        check=lacks(r"5[\s,. ]?000\b"),  # transfers are excluded from the tools
    ),
    Case(
        name="uncategorized_purchase",
        question="Which purchases have no category?",
        expect_tool="list_transactions",
        check=has(r"250"),
    ),
    Case(
        name="czech_question_czech_answer",
        question="Kolik jsem utratil za potraviny?",
        expect_tool=None,
        check=has(r"\b120\b"),
    ),
    Case(
        name="semantic_coffee_search",
        question="Where did I buy coffee?",
        expect_tool="search_transactions",
        check=has(r"Starbucks"),
    ),
    Case(
        name="cafe_total_similar_merchants",
        question="How much do I spend in cafes?",
        expect_tool=None,  # may use spending_summary on dining or search_transactions
        check=has(r"\b320(\.0+)?\b"),  # Starbucks + Kavarna Slavia + Cafe Savoy
    ),
    Case(
        name="cafe_visit_count",
        question="How many times did I go to a cafe?",
        expect_tool=None,
        check=has(r"\b3\b|three"),
    ),
    Case(
        name="similar_to_starbucks",
        question="Show me other transactions similar to my Starbucks purchase.",
        expect_tool="search_transactions",
        check=has(r"Slavia|Savoy"),
    ),
    Case(
        name="czech_cafe_total",
        question="Kolik jsem utratil v kavárnách?",
        expect_tool=None,
        check=has(r"\b320\b"),
    ),
    Case(
        name="empty_category_says_no_data",
        question="How much did I spend on travel?",
        expect_tool="spending_summary",
        check=has(r"\b(no|nothing|none|zero|žádn\w*)\b"),
    ),
    Case(
        name="no_guessing_unknown_merchant",
        question="How much did I pay my landlord last month?",
        expect_tool=None,
        check=has(r"\b(no|nothing|none|not found|couldn't find|could not find|žádn\w*)\b"),
    ),
]


def fill_db() -> None:
    for i, p in enumerate(TRANSACTIONS):
        vector_db.save_parsed(f"eval-{i}", p)
