"""Credit card model (Phase 2).

Money is stored as Numeric(18, 4) — never float. Only the last four digits of the
card number are kept; full card numbers, CVVs and PINs are never stored.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Final

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk

CARD_NETWORKS: Final[tuple[str, ...]] = ("visa", "mastercard", "amex", "rupay", "diners_club")
CARD_STATUSES: Final[tuple[str, ...]] = ("active", "archived")


class CreditCard(Base, TimestampMixin):
    """A credit card owned by a user."""

    __tablename__ = "credit_cards"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    issuer: Mapped[str] = mapped_column(String(100))
    card_name: Mapped[str] = mapped_column(String(150))
    network: Mapped[str] = mapped_column(String(20))
    last_four_digits: Mapped[str] = mapped_column(String(4))
    # Day of month the statement is generated (1–28 to avoid month-end ambiguity).
    billing_cycle_day: Mapped[int] = mapped_column(Integer)
    # Days after the statement date that the payment is due.
    payment_due_days: Mapped[int] = mapped_column(Integer)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    # Manually entered until statement ingestion (Phase 3) keeps it up to date.
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), server_default="0"
    )
    annual_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), server_default="0"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active", index=True
    )

    def __repr__(self) -> str:
        return f"<CreditCard {self.issuer} ****{self.last_four_digits}>"
