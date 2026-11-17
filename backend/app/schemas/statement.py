"""Pydantic v2 schemas for statements."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.transaction import TransactionRead

StatementStatus = Literal["pending_review", "imported", "rejected", "failed"]
Money = Decimal


class StatementRead(BaseModel):
    """Statement summary response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    card_id: uuid.UUID
    statement_date: date
    due_date: date
    period_start: date | None
    period_end: date | None
    total_amount_due: Money
    minimum_amount_due: Money
    opening_balance: Money
    closing_balance: Money
    total_credits: Money
    total_debits: Money
    file_name: str
    file_size_bytes: int
    parser_used: str
    status: StatementStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None


class StatementReviewDetail(StatementRead):
    """Detailed statement response including transactions for the review screen."""

    transactions: list[TransactionRead] = []
    reconciliation_matched: bool = False
    net_calculated: Money = Decimal("0")


class StatementConfirmRequest(BaseModel):
    """Confirm statement import request."""

    # Optionally exclude any false positive transaction IDs
    excluded_transaction_ids: list[uuid.UUID] = []
    # If user wants to override/update card current_balance with total_amount_due
    update_card_balance: bool = True
