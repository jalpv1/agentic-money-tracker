import datetime

import fio_banka

from src import config


def fetch(date_from: datetime.date, date_to: datetime.date) -> list[dict]:
    """Fetch transactions from Fio as plain dicts.

    Fio limits: max 90 days per request, one request per 30 seconds per token.
    """
    account = fio_banka.Account(config.fio_token())
    report = account.fetch_transaction_report_for_period(
        date_from, date_to, fio_banka.TransactionReportFmt.JSON
    )
    try:
        txns = list(fio_banka.Account.parse_transactions(report))
    except KeyError:  # Fio omits the "transaction" key when the period is empty
        return []
    return [t._asdict() for t in txns]
