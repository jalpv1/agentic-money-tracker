import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.environ.get("MONEY_DB", "data/money.db"))
VECTOR_DB_PATH = Path(os.environ.get("MONEY_VECTOR_DB", "data/chroma"))


def fio_token() -> str:
    token = os.environ.get("FIO_TOKEN")
    if not token:
        raise RuntimeError("Set the FIO_TOKEN environment variable")
    return token