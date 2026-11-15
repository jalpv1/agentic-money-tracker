import os
from pathlib import Path

DB_PATH = Path(os.environ.get("MONEY_DB", "data/money.db"))


def fio_token() -> str:
    token = os.environ.get("FIO_TOKEN")
    if not token:
        raise RuntimeError("Set the FIO_TOKEN environment variable")
    return token