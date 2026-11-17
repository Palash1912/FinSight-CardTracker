"""Unit tests for statement parser adapters and transaction normalizer."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.parsers.generic import GenericStatementParser
from app.parsers.hdfc import HDFCStatementParser
from app.parsers.hsbc import HSBCStatementParser
from app.parsers.icici import ICICIStatementParser
from app.parsers.normalizer import (
    clean_description,
    extract_merchant_and_category,
    generate_fingerprint,
)

SYNTHETIC_ICICI_TEXT = """
ICICI Bank Credit Card Statement
Card Number: 4315 XXXX XXXX 4589
Statement Date: 18/10/2026
Payment Due Date: 05/11/2026
Total Amount Due: Rs. 14,500.00
Minimum Amount Due: Rs. 1,500.00

DATE        TRANSACTION DETAILS               AMOUNT (INR)
15/10/2026  AMAZON PAY INDIA                  4,500.00
16/10/2026  SWIGGY BANGALORE                  850.00
17/10/2026  PAYMENT RECEIVED VIA UPI          10,000.00 CR
"""

SYNTHETIC_HDFC_TEXT = """
HDFC BANK Credit Card Statement
Account No: 5422 XXXX XXXX 9912
Statement Date: 20/09/2026
Payment Due Date: 10/10/2026
Total Dues: 18,250.50
Min. Amount Due: 1,825.00

Date        Transaction Description           Amount
12/09/2026  FLIPKART INTERNET PVT LTD         12,499.00
14/09/2026  UBER TRIP HELP.UBER.COM           450.50
18/09/2026  NETBANKING TRANSFER PAYMENT       5,000.00 Cr
"""

SYNTHETIC_HSBC_TEXT = """
HSBC Card Statement
Card Number: 4123 XXXX XXXX 7733
Statement Date: 25/08/2026
Payment Due Date: 15/09/2026
Total Payment Due: Rs. 6,800.00
Minimum Payment Due: Rs. 700.00

Date        Details                           Amount
20/08/2026  NETFLIX.COM                       649.00
22/08/2026  ZOMATO RESTAURANT                 1,250.00
24/08/2026  PAYMENT RECEIVED                  2,000.00 CR
"""


def test_icici_parser_metadata_and_transactions() -> None:
    parser = ICICIStatementParser()
    assert parser.can_parse(SYNTHETIC_ICICI_TEXT) is True

    parsed = parser.parse(SYNTHETIC_ICICI_TEXT)
    assert parsed.issuer == "ICICI Bank"
    assert parsed.statement_date == date(2026, 10, 18)
    assert parsed.due_date == date(2026, 11, 5)
    assert parsed.card_last_four == "4589"
    assert parsed.total_amount_due == Decimal("14500.00")
    assert parsed.minimum_amount_due == Decimal("1500.00")

    assert len(parsed.transactions) == 3
    # Check debits
    t1 = parsed.transactions[0]
    assert t1.date == date(2026, 10, 15)
    assert "AMAZON PAY" in t1.description
    assert t1.amount == Decimal("4500.00")
    assert t1.txn_type == "debit"

    # Check credit
    t3 = parsed.transactions[2]
    assert t3.amount == Decimal("10000.00")
    assert t3.txn_type == "credit"


def test_hdfc_parser() -> None:
    parser = HDFCStatementParser()
    assert parser.can_parse(SYNTHETIC_HDFC_TEXT) is True

    parsed = parser.parse(SYNTHETIC_HDFC_TEXT)
    assert parsed.issuer == "HDFC Bank"
    assert parsed.statement_date == date(2026, 9, 20)
    assert parsed.due_date == date(2026, 10, 10)
    assert parsed.card_last_four == "9912"
    assert parsed.total_amount_due == Decimal("18250.50")

    assert len(parsed.transactions) == 3
    assert parsed.transactions[0].txn_type == "debit"
    assert parsed.transactions[2].txn_type == "credit"


def test_hsbc_parser() -> None:
    parser = HSBCStatementParser()
    assert parser.can_parse(SYNTHETIC_HSBC_TEXT) is True

    parsed = parser.parse(SYNTHETIC_HSBC_TEXT)
    assert parsed.card_last_four == "7733"
    assert parsed.total_amount_due == Decimal("6800.00")
    assert len(parsed.transactions) == 3


def test_generic_parser() -> None:
    sample = """
    Billing Statement
    Date: 01/01/2026
    Due Date: 20/01/2026
    Total Amount Due: 5,000.00
    Card: **** **** **** 1122

    02/01/2026 BLINKIT GROCERIES 1,200.00
    05/01/2026 PAYMENT REFUND 300.00 CR
    """
    parser = GenericStatementParser()
    assert parser.can_parse(sample) is True
    parsed = parser.parse(sample)

    assert parsed.statement_date == date(2026, 1, 1)
    assert parsed.due_date == date(2026, 1, 20)
    assert parsed.card_last_four == "1122"
    assert len(parsed.transactions) == 2
    assert parsed.transactions[0].txn_type == "debit"
    assert parsed.transactions[1].txn_type == "credit"


def test_normalizer_clean_description() -> None:
    raw = "POS / SWIGGY BANGALORE / 872364827364"
    cleaned = clean_description(raw)
    assert "SWIGGY BANGALORE" in cleaned
    assert "POS" not in cleaned


def test_normalizer_merchant_and_category() -> None:
    merchant, cat = extract_merchant_and_category("AMZN Mktp US")
    assert merchant == "Amazon"
    assert cat == "Shopping"

    merchant, cat = extract_merchant_and_category("UBER INDIA TECHNOLOGIES")
    assert merchant == "Uber"
    assert cat == "Travel"

    merchant, cat = extract_merchant_and_category("UNKNOWN LOCAL STORE")
    assert merchant is None
    assert cat == "Uncategorized"


def test_fingerprint_deterministic_and_unique() -> None:
    cid = uuid.uuid4()
    d = date(2026, 10, 15)
    amt = Decimal("4500.00")

    fp1 = generate_fingerprint(cid, d, amt, "debit", "Amazon")
    fp2 = generate_fingerprint(cid, d, amt, "debit", "Amazon")
    fp3 = generate_fingerprint(cid, d, amt, "credit", "Amazon")

    assert fp1 == fp2  # Deterministic
    assert fp1 != fp3  # Different for credit vs debit
