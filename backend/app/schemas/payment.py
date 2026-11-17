"""Pydantic v2 schemas for payments and bill tracking."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Money = Decimal
PaymentMethod = Literal[
    "upi",
    "neft",
    "imps",
    "net_banking",
    "debit_card",
    "auto_debit",
    "cheque",
    "cash",
    "other",
]
BillStatus = Literal["PAID", "PARTIALLY_PAID", "UNPAID", "NO_BILL"]


class PaymentCreate(BaseModel):
    """Request body to record a credit card bill payment."""

    card_id: uuid.UUID
    statement_id: uuid.UUID | None = None
    payment_date: date
    amount: Money = Field(gt=0, max_digits=18, decimal_places=4)
    payment_method: PaymentMethod = "net_banking"
    reference_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)


class PaymentRead(BaseModel):
    """Response body for payment records."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    card_id: uuid.UUID
    statement_id: uuid.UUID | None
    payment_date: date
    amount: Money
    currency: str
    payment_method: str
    reference_number: str | None
    notes: str | None
    status: str
    created_at: datetime


class CardBillStatus(BaseModel):
    """Consolidated payment status for a credit card's active/latest billing cycle."""

    card_id: uuid.UUID
    card_name: str
    issuer: str
    last_four_digits: str
    statement_id: uuid.UUID | None
    statement_date: date | None
    due_date: date
    statement_amount: Money
    minimum_due: Money
    total_paid: Money
    remaining_balance: Money
    days_until_due: int
    status: BillStatus
    is_overdue: bool
