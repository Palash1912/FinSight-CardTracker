"""Pydantic v2 schemas for credit cards.

JSON uses snake_case field names. Money values are serialised as decimal strings
(e.g. "150000.0000") so they never pass through floating point.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.card import CreditCard
from app.services.billing import next_statement_date, payment_due_date

Network = Literal["visa", "mastercard", "amex", "rupay", "diners_club"]
CardStatus = Literal["active", "archived"]

Money = Decimal


class CardCreate(BaseModel):
    """Request body for POST /cards."""

    issuer: str = Field(min_length=1, max_length=100)
    card_name: str = Field(min_length=1, max_length=150)
    network: Network
    last_four_digits: str = Field(pattern=r"^\d{4}$")
    billing_cycle_day: int = Field(ge=1, le=28)
    payment_due_days: int = Field(ge=1, le=60)
    credit_limit: Money = Field(gt=0, max_digits=18, decimal_places=4)
    current_balance: Money = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=4)
    annual_fee: Money = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=4)


class CardUpdate(BaseModel):
    """Request body for PATCH /cards/{id}. Only fields that are sent are changed."""

    model_config = ConfigDict(extra="forbid")

    issuer: str | None = Field(default=None, min_length=1, max_length=100)
    card_name: str | None = Field(default=None, min_length=1, max_length=150)
    network: Network | None = None
    last_four_digits: str | None = Field(default=None, pattern=r"^\d{4}$")
    billing_cycle_day: int | None = Field(default=None, ge=1, le=28)
    payment_due_days: int | None = Field(default=None, ge=1, le=60)
    credit_limit: Money | None = Field(default=None, gt=0, max_digits=18, decimal_places=4)
    current_balance: Money | None = Field(default=None, ge=0, max_digits=18, decimal_places=4)
    annual_fee: Money | None = Field(default=None, ge=0, max_digits=18, decimal_places=4)
    status: CardStatus | None = None

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> Self:
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class CardRead(BaseModel):
    """Response body for card endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issuer: str
    card_name: str
    network: str
    last_four_digits: str
    billing_cycle_day: int
    payment_due_days: int
    credit_limit: Money
    current_balance: Money
    available_credit: Money
    annual_fee: Money
    status: str
    next_statement_date: date
    next_due_date: date
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def from_card(cls, card: CreditCard, as_of: date) -> Self:
        statement = next_statement_date(card.billing_cycle_day, as_of)
        return cls(
            id=card.id,
            issuer=card.issuer,
            card_name=card.card_name,
            network=card.network,
            last_four_digits=card.last_four_digits,
            billing_cycle_day=card.billing_cycle_day,
            payment_due_days=card.payment_due_days,
            credit_limit=card.credit_limit,
            current_balance=card.current_balance,
            available_credit=card.credit_limit - card.current_balance,
            annual_fee=card.annual_fee,
            status=card.status,
            next_statement_date=statement,
            next_due_date=payment_due_date(statement, card.payment_due_days),
            created_at=card.created_at,
            updated_at=card.updated_at,
        )
