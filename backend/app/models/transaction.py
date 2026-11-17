"""Transaction model for credit card transactions."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Final

from sqlalchemy import Date, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.statement import Statement

TXN_TYPES: Final[tuple[str, ...]] = ("debit", "credit")
TXN_STATUSES: Final[tuple[str, ...]] = ("pending", "posted", "reconciled")


class Transaction(Base, TimestampMixin):
    """Normalized credit card transaction."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="CASCADE"), index=True
    )
    statement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("statements.id", ondelete="CASCADE"), index=True, nullable=True
    )

    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    posting_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    original_description: Mapped[str] = mapped_column(String(500))
    cleaned_description: Mapped[str] = mapped_column(String(500))
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[str] = mapped_column(
        String(100), default="Uncategorized", server_default="Uncategorized", index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    txn_type: Mapped[str] = mapped_column(String(10))  # "debit" | "credit"

    # Fingerprint to prevent duplicate imports: SHA256(card_id + date + amount + txn_type + cleaned_description)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)

    source: Mapped[str] = mapped_column(
        String(20), default="pdf_statement", server_default="pdf_statement"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="posted", server_default="posted", index=True
    )

    # Audit & auditability references
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_values: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    statement: Mapped[Statement | None] = relationship(
        "Statement", back_populates="transactions"
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.id} {self.transaction_date} {self.amount} {self.txn_type}>"
