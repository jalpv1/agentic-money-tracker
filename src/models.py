import datetime

from pydantic import BaseModel


class Parsed(BaseModel):
    kind: str
    parse_ok: bool
    merchant_raw: str | None = None
    merchant_key: str | None = None
    city: str | None = None
    country: str | None = None
    purchase_date: datetime.date | None = None
    orig_amount: float | None = None
    orig_currency: str | None = None
    category: str | None = None
