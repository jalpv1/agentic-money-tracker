import datetime

from src import db, vector_db
from src.bank import fio
from src.parsing import transactions

MAX_DAYS = 90
OVERLAP_DAYS = 3


def sync() -> int:
    """Fetch new transactions, store raw, parse them. Returns number of new rows."""
    today = datetime.date.today()
    earliest = today - datetime.timedelta(days=MAX_DAYS)
    last = db.last_synced_date()
    since = max(earliest, last - datetime.timedelta(days=OVERLAP_DAYS)) if last else earliest

    txns = fio.fetch(since, today)
    new = db.save_raw(txns)
    vector_db.save_raw(txns)

    for row in db.unparsed():
        tid = row["transaction_id"]
        parsed = transactions.parse(
            row["type"],
            row["remittance_info"],
            float(row["amount"]),
            row["currency"],
            datetime.date.fromisoformat(row["date"]),
        )
        db.save_parsed(tid, parsed)
        vector_db.save_parsed(tid, parsed)
    return new
