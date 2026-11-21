"""Agent tools over the vector DB. All numbers are computed here, never by the LLM."""

from collections import defaultdict
from typing import Literal

from langchain_core.tools import tool

from src import vector_db

_EXCLUDED_KINDS = {"transfer_internal"}

Direction = Literal["expense", "income", "all"]


def _load(ids: list[str] | None = None) -> list[dict]:
    """Read parsed transactions."""
    _, parsed = vector_db.connect()
    p = parsed.get(ids=ids, include=["metadatas", "documents"])
    return [
        {
            "id": tid,
            "date": m["booked_date"],
            "amount": m["amount"],  # negative = money out
            "currency": m["currency"],
            "kind": m.get("kind", "unparsed"),
            "merchant": m.get("merchant_raw"),
            "city": m.get("city"),
            "country": m.get("country"),
            "category": m.get("category"),
            "description": doc,
        }
        for tid, m, doc in zip(p["ids"], p["metadatas"], p["documents"])
        if "booked_date" in m
    ]


def _filter(
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    city: str | None = None,
    direction: Direction = "all",
) -> list[dict]:
    rows = []
    for t in _load():
        if t["kind"] in _EXCLUDED_KINDS:
            continue
        if date_from and t["date"] < date_from:
            continue
        if date_to and t["date"] > date_to:
            continue
        if category and (t["category"] or "").lower() != category.lower():
            continue
        if merchant and merchant.lower() not in f"{t['merchant'] or ''} {t['description']}".lower():
            continue
        if city and city.lower() not in (t["city"] or "").lower():
            continue
        if direction == "expense" and t["amount"] >= 0:
            continue
        if direction == "income" and t["amount"] <= 0:
            continue
        rows.append(t)
    return rows


@tool
def data_overview() -> dict:
    """Describe the available data: date range, currency, categories, top merchants.

    Call this first when unsure which category or merchant names exist.
    """
    rows = [t for t in _load() if t["kind"] not in _EXCLUDED_KINDS]
    if not rows:
        return {"transaction_count": 0}
    categories: dict[str, int] = defaultdict(int)
    merchants: dict[str, int] = defaultdict(int)
    for t in rows:
        categories[t["category"] or "unknown"] += 1
        if t["merchant"]:
            merchants[t["merchant"]] += 1
    return {
        "transaction_count": len(rows),
        "date_range": [min(t["date"] for t in rows), max(t["date"] for t in rows)],
        "currency": rows[0]["currency"],
        "categories": dict(sorted(categories.items(), key=lambda kv: -kv[1])),
        "top_merchants": dict(sorted(merchants.items(), key=lambda kv: -kv[1])[:20]),
    }


@tool
def spending_summary(
    group_by: Literal["category", "merchant", "month", "city", "none"] = "category",
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    direction: Direction = "expense",
    top_n: int = 15,
) -> dict:
    """Total, count and average of transactions, grouped by category/merchant/month/city.

    Use for any "how much", "how many" or "biggest ..." question.
    Dates are inclusive ISO strings (YYYY-MM-DD). Totals are positive numbers in the
    account currency. `merchant` is a case-insensitive substring match. Internal
    transfers between own accounts are excluded. Groups are sorted by total
    (by date for month).
    """
    rows = _filter(date_from, date_to, category, merchant, None, direction)
    key = {
        "category": lambda t: t["category"] or "unknown",
        "merchant": lambda t: t["merchant"] or "unknown",
        "month": lambda t: t["date"][:7],
        "city": lambda t: t["city"] or "unknown",
        "none": lambda t: "all",
    }[group_by]
    groups: dict[str, list[float]] = defaultdict(list)
    for t in rows:
        groups[key(t)].append(abs(t["amount"]))
    result = [
        {
            "group": g,
            "total": round(sum(v), 2),
            "count": len(v),
            "average": round(sum(v) / len(v), 2),
        }
        for g, v in groups.items()
    ]
    result.sort(key=(lambda r: r["group"]) if group_by == "month" else (lambda r: -r["total"]))
    return {
        "currency": rows[0]["currency"] if rows else None,
        "grand_total": round(sum(abs(t["amount"]) for t in rows), 2),
        "transaction_count": len(rows),
        "groups": result[:top_n],
        "groups_omitted": max(0, len(result) - top_n),
    }


@tool
def list_transactions(
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    merchant: str | None = None,
    city: str | None = None,
    direction: Direction = "all",
    sort_by: Literal["date", "amount"] = "date",
    limit: int = 20,
) -> list[dict]:
    """List individual transactions that match exact filters.

    sort_by="date" gives newest first; sort_by="amount" gives largest (by absolute
    value) first. Use it to show examples, find the biggest purchase, or verify a total.
    Dates are inclusive ISO strings (YYYY-MM-DD). Amount is negative for money out.
    """
    rows = _filter(date_from, date_to, category, merchant, city, direction)
    if sort_by == "amount":
        rows.sort(key=lambda t: abs(t["amount"]), reverse=True)
    else:
        rows.sort(key=lambda t: t["date"], reverse=True)
    return rows[:limit]


@tool
def search_transactions(query: str, n_results: int = 8) -> list[dict]:
    """Semantic (meaning-based) search over transactions, in Czech or English.

    Use for fuzzy questions where the category or merchant is unclear, e.g. "coffee",
    "ride sharing", "streaming". Results are ordered by relevance (smaller distance =
    closer match). To get totals for what you found, follow up with spending_summary.
    """
    hits = vector_db.search(query, n_results=n_results)
    distance = {h["transaction_id"]: round(h["distance"], 3) for h in hits}
    rows = {t["id"]: t for t in _load(list(distance))}
    return [{**rows[i], "distance": d} for i, d in distance.items() if i in rows]


TOOLS = [data_overview, spending_summary, list_transactions, search_transactions]
