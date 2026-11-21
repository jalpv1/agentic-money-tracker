import datetime
import json
import sqlite3
from contextlib import closing

from src import config
from src.models import Parsed

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_transactions (
    transaction_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    type TEXT,
    remittance_info TEXT,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS parsed_transactions (
    transaction_id TEXT PRIMARY KEY REFERENCES raw_transactions(transaction_id),
    kind TEXT NOT NULL,
    parse_ok INTEGER NOT NULL,
    merchant_raw TEXT,
    merchant_key TEXT,
    city TEXT,
    country TEXT,
    purchase_date TEXT,
    orig_amount REAL,
    orig_currency TEXT,
    category TEXT,
    amount REAL,
    currency TEXT,
    booked_date TEXT
);
"""


def connect() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """CREATE TABLE IF NOT EXISTS won't add columns to an existing DB, so add them here."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(parsed_transactions)")}
    for name, sql_type in (
        ("category", "TEXT"),
        ("amount", "REAL"),
        ("currency", "TEXT"),
        ("booked_date", "TEXT"),
    ):
        if name not in cols:
            conn.execute(f"ALTER TABLE parsed_transactions ADD COLUMN {name} {sql_type}")
    conn.commit()


def last_synced_date() -> datetime.date | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT MAX(date) AS d FROM raw_transactions").fetchone()
    return datetime.date.fromisoformat(row["d"]) if row["d"] else None


def save_raw(txns: list[dict]) -> int:
    """Insert new transactions, ignoring ones already stored. Returns count inserted."""
    rows = [
        (
            str(t["transaction_id"]),
            t["date"].isoformat(),
            str(t["amount"]),
            t["currency"],
            t["type"],
            t["remittance_info"],
            json.dumps(t, default=str, ensure_ascii=False),
        )
        for t in txns
    ]
    with closing(connect()) as conn, conn:
        before = conn.total_changes
        conn.executemany(
            "INSERT OR IGNORE INTO raw_transactions VALUES (?, ?, ?, ?, ?, ?, ?)", rows
        )
        return conn.total_changes - before


def unparsed() -> list[sqlite3.Row]:
    with closing(connect()) as conn:
        return conn.execute(
            """SELECT r.transaction_id, r.type, r.remittance_info, r.amount, r.currency, r.date
               FROM raw_transactions r
               LEFT JOIN parsed_transactions p USING (transaction_id)
               WHERE p.transaction_id IS NULL"""
        ).fetchall()


def save_parsed(transaction_id: str, parsed: Parsed) -> None:
    data = parsed.model_dump(mode="json")
    data["parse_ok"] = int(data["parse_ok"])
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT OR REPLACE INTO parsed_transactions
               (transaction_id, kind, parse_ok, merchant_raw, merchant_key, city,
                country, purchase_date, orig_amount, orig_currency, category,
                amount, currency, booked_date)
               VALUES
               (:transaction_id, :kind, :parse_ok, :merchant_raw, :merchant_key, :city,
                :country, :purchase_date, :orig_amount, :orig_currency, :category,
                :amount, :currency, :booked_date)""",
            {"transaction_id": transaction_id, **data},
        )
