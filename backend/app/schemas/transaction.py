"""Pydantic v2 schemas for transactions."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TxnType = Literal["debit", "credit"]
TxnStatus = Literal["pending", "posted", "reconciled"]
Money = Decimal


class TransactionRead(BaseModel):
    """Response body for transaction items."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    card_id: uuid.UUID
    statement_id: uuid.UUID | None
    transaction_date: date
    posting_date: date | None
    original_description: str
    cleaned_description: str
    merchant_name: str | None
    category: str
    amount: Money
    currency: str
    txn_type: TxnType
    fingerprint: str
    source: str
    status: TxnStatus
    source_page: int | None
    source_row: int | None
    original_values: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime | None


class TransactionUpdate(BaseModel):
    """Editable fields for a transaction."""

    cleaned_description: str | None = Field(default=None, max_length=500)
    merchant_name: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    status: TxnStatus | None = None


class TransactionFilterParams(BaseModel):
    """Query parameters for listing transactions."""

    card_id: uuid.UUID | None = None
    statement_id: uuid.UUID | None = None
    category: str | None = None
    merchant: str | None = None
    txn_type: TxnType | None = None
    start_date: date | None = None
    end_date: date | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
