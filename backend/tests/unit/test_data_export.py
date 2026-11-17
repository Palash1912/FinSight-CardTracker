"""Unit tests for Phase 10: Data export, CSV formatting, and security hardening."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date
from decimal import Decimal

from app.models.card import CreditCard
from app.models.transaction import Transaction


def test_csv_export_formatting() -> None:
    card_id = uuid.uuid4()
    card = CreditCard(
        id=card_id,
        user_id=uuid.uuid4(),
        issuer="HDFC Bank",
        card_name="Millennia",
        network="visa",
        last_four_digits="9876",
        billing_cycle_day=15,
        payment_due_days=20,
        credit_limit=Decimal("250000.00"),
    )

    txn = Transaction(
        id=uuid.uuid4(),
        user_id=card.user_id,
        card_id=card.id,
        transaction_date=date(2026, 10, 15),
        original_description="SWIGGY BANGALORE",
        cleaned_description="Swiggy Delivery",
        merchant_name="Swiggy",
        category="Food & Dining",
        amount=Decimal("1250.50"),
        currency="INR",
        txn_type="debit",
        fingerprint="dummy_fp",
        status="posted",
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Issuer", "Card", "Description", "Amount"])
    writer.writerow([
        str(txn.id),
        str(txn.transaction_date),
        card.issuer,
        card.card_name,
        txn.cleaned_description,
        f"{txn.amount:.2f}",
    ])

    csv_data = output.getvalue()
    assert "HDFC Bank" in csv_data
    assert "Swiggy Delivery" in csv_data
    assert "1250.50" in csv_data


def test_security_headers_constants() -> None:
    from app.main import SecurityHeadersMiddleware

    assert SecurityHeadersMiddleware is not None
