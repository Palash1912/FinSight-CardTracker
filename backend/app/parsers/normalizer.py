"""Transaction description cleaner, merchant extractor, and categorizer."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import date
from decimal import Decimal
from typing import Final

MERCHANT_PATTERNS: Final[list[tuple[re.Pattern[str], str, str]]] = [
    # (regex, Normalized Merchant, Category)
    (re.compile(r"\b(AMAZON|AMZN)\b", re.IGNORECASE), "Amazon", "Shopping"),
    (re.compile(r"\bFLIPKART\b", re.IGNORECASE), "Flipkart", "Shopping"),
    (re.compile(r"\bMYNTRA\b", re.IGNORECASE), "Myntra", "Shopping"),
    (re.compile(r"\bSWIGGY\b", re.IGNORECASE), "Swiggy", "Dining"),
    (re.compile(r"\bZOMATO\b", re.IGNORECASE), "Zomato", "Dining"),
    (re.compile(r"\bBLINKIT\b", re.IGNORECASE), "Blinkit", "Groceries"),
    (re.compile(r"\bZEPTO\b", re.IGNORECASE), "Zepto", "Groceries"),
    (re.compile(r"\bINSTAMART\b", re.IGNORECASE), "Instamart", "Groceries"),
    (re.compile(r"\bBIGBASKET\b", re.IGNORECASE), "BigBasket", "Groceries"),
    (re.compile(r"\bUBER\b", re.IGNORECASE), "Uber", "Travel"),
    (re.compile(r"\bOLA\b", re.IGNORECASE), "Ola", "Travel"),
    (re.compile(r"\bMAKEMYTRIP\b", re.IGNORECASE), "MakeMyTrip", "Travel"),
    (re.compile(r"\bGOIBIBO\b", re.IGNORECASE), "Goibibo", "Travel"),
    (re.compile(r"\bIRCTC\b", re.IGNORECASE), "IRCTC", "Travel"),
    (re.compile(r"\bNETFLIX\b", re.IGNORECASE), "Netflix", "Entertainment"),
    (re.compile(r"\bSPOTIFY\b", re.IGNORECASE), "Spotify", "Entertainment"),
    (re.compile(r"\bHOTSTAR\b", re.IGNORECASE), "Disney+ Hotstar", "Entertainment"),
    (re.compile(r"\bBOOKMYSHOW\b", re.IGNORECASE), "BookMyShow", "Entertainment"),
    (re.compile(r"\b(AIRTEL|JIO|VODAFONE|VI BILL)\b", re.IGNORECASE), "Telecom", "Utilities"),
    (re.compile(r"\b(BESCOM|TNEB|MSEDCL|ELECTRICITY)\b", re.IGNORECASE), "Electricity", "Utilities"),
    (re.compile(r"\b(HPCL|BPCL|IOCL|PETROL|FUEL)\b", re.IGNORECASE), "Fuel Station", "Fuel"),
    (re.compile(r"\b(ANNUAL FEE|LATE FEE|INTEREST CHARGE|GST)\b", re.IGNORECASE), "Bank Charges", "Fees & Charges"),
    (re.compile(r"\b(AUTOPAY|PAYMENT RECEIVED|NEFT|IMPS|CHEQUE|UPI)\b", re.IGNORECASE), "Payment", "Payment"),
]


def clean_description(raw: str) -> str:
    """Strip card terminal codes, dates, transaction reference IDs and excess whitespace."""
    s = raw.strip()
    # Remove common bank prefixes
    s = re.sub(r"^(POS|ECOM|UPI|IMPS|NEFT|INB|VPS)[\s/:-]+", "", s, flags=re.IGNORECASE)
    # Remove reference code endings like /1234567890/TXN
    s = re.sub(r"[\s/]+[A-Z0-9]{10,}$", "", s)
    # Condense internal spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s or raw.strip()


def extract_merchant_and_category(description: str) -> tuple[str | None, str]:
    """Identify recognizable merchants and assign a category from normalized description."""
    for pattern, merchant, category in MERCHANT_PATTERNS:
        if pattern.search(description):
            return merchant, category
    return None, "Uncategorized"


def generate_fingerprint(
    card_id: uuid.UUID,
    txn_date: date,
    amount: Decimal,
    txn_type: str,
    cleaned_desc: str,
) -> str:
    """Generate deterministic SHA-256 fingerprint for deduplication."""
    # Normalize amount to standard 4 decimal places
    amount_str = f"{amount:.4f}"
    content = f"{card_id}:{txn_date.isoformat()}:{amount_str}:{txn_type.lower()}:{cleaned_desc.lower()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
