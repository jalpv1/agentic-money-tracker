"""ChromaDB-backed store exposing the same interface as src/db.py.

Two collections mirror the two SQLite tables:
  raw_transactions    - bank data as received (document = remittance text)
  parsed_transactions - parse results (document = natural-language summary, embedded for search)
"""
import datetime
import json
from functools import lru_cache

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src import config
from src.models import Parsed

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # handles Czech & English
_CHUNK = 500


@lru_cache(maxsize=1)
def _embedding_function() -> SentenceTransformerEmbeddingFunction:
    return SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)


@lru_cache(maxsize=1)
def _client() -> chromadb.ClientAPI:
    config.VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(config.VECTOR_DB_PATH))


def connect() -> tuple[chromadb.Collection, chromadb.Collection]:
    """Return (raw, parsed) collections, creating them on first use."""
    client = _client()
    kwargs = {"embedding_function": _embedding_function(), "metadata": {"hnsw:space": "cosine"}}
    raw = client.get_or_create_collection("raw_transactions", **kwargs)
    parsed = client.get_or_create_collection("parsed_transactions", **kwargs)
    return raw, parsed


def _existing_ids(collection: chromadb.Collection, ids: list[str]) -> set[str]:
    found: set[str] = set()
    for i in range(0, len(ids), _CHUNK):
        found.update(collection.get(ids=ids[i : i + _CHUNK], include=[])["ids"])
    return found


def last_synced_date() -> datetime.date | None:
    raw, _ = connect()
    metadatas = raw.get(include=["metadatas"])["metadatas"]
    dates = [m["date"] for m in metadatas if m and m.get("date")]
    return datetime.date.fromisoformat(max(dates)) if dates else None


def save_raw(txns: list[dict]) -> int:
    """Insert new transactions, ignoring ones already stored. Returns count inserted."""
    raw, _ = connect()
    by_id = {str(t["transaction_id"]): t for t in txns}
    existing = _existing_ids(raw, list(by_id))
    new = {tid: t for tid, t in by_id.items() if tid not in existing}
    if not new:
        return 0
    raw.add(
        ids=list(new),
        documents=[f"{t['type'] or ''} {t['remittance_info'] or ''}".strip() or "empty" for t in new.values()],
        metadatas=[
            {
                "date": t["date"].isoformat(),
                "amount": str(t["amount"]),
                "currency": t["currency"],
                "type": t["type"] or "",
                "remittance_info": t["remittance_info"] or "",
                "payload": json.dumps(t, default=str, ensure_ascii=False),
            }
            for t in new.values()
        ],
    )
    return len(new)


def unparsed() -> list[dict]:
    """Raw transactions without a parsed counterpart (dicts, indexable like sqlite3.Row)."""
    raw, parsed = connect()
    raw_data = raw.get(include=["metadatas"])
    parsed_ids = set(parsed.get(include=[])["ids"])
    return [
        {
            "transaction_id": tid,
            "type": meta.get("type") or None,
            "remittance_info": meta.get("remittance_info") or None,
        }
        for tid, meta in zip(raw_data["ids"], raw_data["metadatas"])
        if tid not in parsed_ids
    ]


def _describe(p: Parsed) -> str:
    merchant = p.merchant_raw or "Unknown Merchant"
    city = f" in {p.city}" if p.city else ""
    country = f", {p.country}" if p.country else ""
    when = f" on {p.purchase_date}" if p.purchase_date else ""
    amount = f" for {p.orig_amount} {p.orig_currency}" if p.orig_amount and p.orig_currency else ""
    cat = f" Category: {p.category}." if p.category else ""
    return f"Transaction at {merchant}{city}{country}{when}{amount}.{cat}"


def save_parsed(transaction_id: str, parsed: Parsed) -> None:
    _, coll = connect()
    data = parsed.model_dump(mode="json")
    # Chroma metadata can't hold None, so drop empty fields.
    metadata = {k: v for k, v in data.items() if v is not None}
    coll.upsert(ids=[transaction_id], documents=[_describe(parsed)], metadatas=[metadata])


def search(query: str, n_results: int = 5) -> list[dict]:
    """Semantic search over parsed transactions (extra on top of the db.py interface)."""
    _, coll = connect()
    res = coll.query(query_texts=[query], n_results=n_results)
    return [
        {"transaction_id": i, "document": d, "metadata": m, "distance": dist}
        for i, d, m, dist in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
        )
    ]
