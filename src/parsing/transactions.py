import re, unicodedata, datetime
from pydantic import BaseModel

from src.models import Parsed
from src.parsing.categories import categorize

TAIL = re.compile(
    r"dne\s+(?P<d>\d{1,2})\.(?P<m>\d{1,2})\.(?P<y>\d{4}),\s*částka\s+(?P<amt>[\d.]+)\s+(?P<cur>[A-Z]{3})\s*$"
)
COUNTRY = re.compile(r"^[A-Z]{3}$")
ZIP = re.compile(r"^[\d\s-]{5,10}$")
NOISE = ("vam dekuje", "s.r.o.", "a.s.")

KIND = {
    "Platba kartou": "card_purchase",
    "Platba převodem uvnitř banky": "transfer_internal",
    "Okamžitá příchozí platba": "transfer_in",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    for n in NOISE:
        s = s.replace(n, "")
    return re.sub(r"\s+", " ", s).strip()

def parse(
    type_: str, info: str | None, amount: float, currency: str, booked_date: datetime.date
) -> Parsed:
    booked = dict(amount=amount, currency=currency, booked_date=booked_date)
    kind = KIND.get(type_, "other")
    if kind != "card_purchase" or not info:
        return Parsed(**booked, kind=kind, parse_ok=kind != "other", category=categorize(kind, None))
    body = info.removeprefix("Nákup:").strip()
    m = TAIL.search(body)
    if not m:
        return Parsed(**booked, kind=kind, parse_ok=False)
    parts = [p.strip() for p in body[:m.start()].split(",") if p.strip()]
    country = parts.pop() if parts and COUNTRY.match(parts[-1]) else None
    if parts and ZIP.match(parts[-1]):
        parts.pop()
    city = parts.pop() if len(parts) > 1 else None
    merchant = parts[0] if parts else None
    merchant_key = norm(merchant) if merchant else None
    return Parsed(
        **booked, kind=kind, parse_ok=merchant is not None,
        merchant_raw=merchant, merchant_key=merchant_key,
        city=city, country=country,
        purchase_date=datetime.date(int(m["y"]), int(m["m"]), int(m["d"])),
        orig_amount=float(m["amt"]), orig_currency=m["cur"],
        category=categorize(kind, merchant_key),
    )