"""Merchant -> category mapping.

Keys are matched as substrings of the normalized merchant key (see transactions.norm:
ascii, lowercase), so "lidl" also matches "lidl dekuje za nakup". First match wins,
so put more specific keywords above generic ones. Extend freely.
"""

CATEGORY_MAP: dict[str, str] = {
    # groceries
    "lidl": "groceries", "albert": "groceries", "billa": "groceries", "tesco": "groceries",
    "penny": "groceries", "kaufland": "groceries", "globus": "groceries", "coop": "groceries",
    "rohlik": "groceries", "žabka": "groceries", "zabka": "groceries", "potraviny": "groceries",
    # dining & coffee
    "mcdonald": "dining", "kfc": "dining", "burger": "dining", "pizza": "dining",
    "restaurant": "dining", "restaurace": "dining", "cafe": "dining", "kavarna": "dining",
    "starbucks": "dining", "bistro": "dining", "pub": "dining", "wolt": "dining", "foodora": "dining",
    # transport
    "uber": "transport", "bolt": "transport", "dpp": "transport", "dopravni podnik": "transport",
    "ceske drahy": "transport", "regiojet": "transport", "flixbus": "transport",
    "mol ": "transport", "shell": "transport", "benzina": "transport", "omv": "transport",
    "lime": "transport", "parking": "transport", "parkovani": "transport",
    # telecom & utilities
    "vodafone": "telecom", "o2": "telecom", "t-mobile": "telecom", "tmobile": "telecom",
    "pre ": "utilities", "cez": "utilities", "innogy": "utilities", "pvk": "utilities",
    # subscriptions & digital
    "netflix": "subscriptions", "spotify": "subscriptions", "youtube": "subscriptions",
    "apple.com": "subscriptions", "google": "subscriptions", "steam": "subscriptions",
    "openai": "subscriptions", "hbo": "subscriptions", "disney": "subscriptions",
    # shopping
    "alza": "shopping", "datart": "shopping", "mall.cz": "shopping", "amazon": "shopping",
    "zalando": "shopping", "ikea": "shopping", "hornbach": "shopping", "obi": "shopping",
    "h&m": "shopping", "decathlon": "shopping", "allegro": "shopping",
    # health
    "dr.max": "health", "dr max": "health", "benu": "health", "lekarna": "health",
    "pilulka": "health", "dm drogerie": "health", "rossmann": "health", "teta": "health",
    # entertainment & travel
    "cinema": "entertainment", "kino": "entertainment", "cinestar": "entertainment",
    "booking": "travel", "airbnb": "travel", "ryanair": "travel", "wizz": "travel",
    "hotel": "travel",
}

# Categories for non-card transaction kinds (no merchant to look at).
KIND_CATEGORY: dict[str, str] = {
    "transfer_internal": "transfer",
    "transfer_in": "income",
}

UNCATEGORIZED = "uncategorized"


def categorize(kind: str, merchant_key: str | None) -> str | None:
    if kind in KIND_CATEGORY:
        return KIND_CATEGORY[kind]
    if not merchant_key:
        return None
    for keyword, category in CATEGORY_MAP.items():
        if keyword in merchant_key:
            return category
    return UNCATEGORIZED
