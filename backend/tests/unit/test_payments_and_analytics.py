"""Unit tests for payments, bill tracking, and analytics schemas."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.schemas.analytics import (
    CategorySpendPoint,
    DashboardSummary,
    MonthlySpendPoint,
)
from app.schemas.payment import CardBillStatus, PaymentCreate


def test_payment_create_schema() -> None:
    card_id = uuid.uuid4()
    req = PaymentCreate(
        card_id=card_id,
        payment_date=date(2026, 10, 20),
        amount=Decimal("12500.50"),
        payment_method="upi",
        reference_number="UPI/1234567890",
    )
    assert req.amount == Decimal("12500.50")
    assert req.payment_method == "upi"


def test_card_bill_status_schema() -> None:
    card_id = uuid.uuid4()
    bill = CardBillStatus(
        card_id=card_id,
        card_name="Millennia",
        issuer="HDFC Bank",
        last_four_digits="1234",
        statement_id=uuid.uuid4(),
        statement_date=date(2026, 10, 15),
        due_date=date(2026, 11, 4),
        statement_amount=Decimal("25000.00"),
        minimum_due=Decimal("2500.00"),
        total_paid=Decimal("10000.00"),
        remaining_balance=Decimal("15000.00"),
        days_until_due=5,
        status="PARTIALLY_PAID",
        is_overdue=False,
    )
    assert bill.status == "PARTIALLY_PAID"
    assert bill.remaining_balance == Decimal("15000.00")
    assert bill.is_overdue is False


def test_dashboard_summary_schema() -> None:
    summary = DashboardSummary(
        total_outstanding=Decimal("45000.00"),
        total_credit_limit=Decimal("300000.00"),
        total_available_credit=Decimal("255000.00"),
        overall_utilization=15.0,
        active_cards_count=2,
        current_month_spend=Decimal("22000.00"),
        previous_month_spend=Decimal("18000.00"),
        spend_change_percentage=22.2,
        upcoming_dues_count=1,
        upcoming_dues_total=Decimal("15000.00"),
    )
    assert summary.active_cards_count == 2
    assert summary.overall_utilization == 15.0
    assert summary.spend_change_percentage == 22.2


def test_category_spend_point() -> None:
    cat = CategorySpendPoint(
        category="Shopping",
        total_spend=Decimal("14500.00"),
        percentage=45.5,
    )
    assert cat.percentage == 45.5
    assert cat.category == "Shopping"


def test_monthly_spend_point() -> None:
    month_pt = MonthlySpendPoint(
        month="2026-10",
        total_spend=Decimal("34500.00"),
        transaction_count=18,
    )
    assert month_pt.month == "2026-10"
    assert month_pt.transaction_count == 18
