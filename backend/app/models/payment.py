"""Payment model for credit card bill tracking and settlements."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Final

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

PAYMENT_METHODS: Final[tuple[str, ...]] = (
    "upi",
    "neft",
    "imps",
    "net_banking",
    "debit_card",
    "auto_debit",
    "cheque",
    "cash",
    "other",
)

PAYMENT_STATUSES: Final[tuple[str, ...]] = (
    "completed",
    "pending",
    "failed",
)


class Payment(Base, TimestampMixin):
    """A credit card payment recorded by the user or statement reconciliation."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="CASCADE"), index=True
    )
    statement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("statements.id", ondelete="SET NULL"), index=True, nullable=True
    )

    payment_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")

    payment_method: Mapped[str] = mapped_column(
        String(50), default="net_banking", server_default="net_banking"
    )
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default="completed", server_default="completed", index=True
    )

    def __repr__(self) -> str:
        return f"<Payment {self.id} card={self.card_id} amount={self.amount} date={self.payment_date}>"
