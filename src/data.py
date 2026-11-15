import datetime

from src import db
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

    new = db.save_raw(fio.fetch(since, today))
    for row in db.unparsed():
        db.save_parsed(row["transaction_id"], transactions.parse(row["type"], row["remittance_info"]))
    return new