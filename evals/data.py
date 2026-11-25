import datetime as dt

from src import vector_db
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




def fill_db() -> None:
    for i, p in enumerate(TRANSACTIONS):
        vector_db.save_parsed(f"eval-{i}", p)
