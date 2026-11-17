"""Reward program, rules, caps, and reward ledger models."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Final

from sqlalchemy import Boolean, Date, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk

REWARD_TYPES: Final[tuple[str, ...]] = ("cashback", "reward_points", "miles")
RULE_TYPES: Final[tuple[str, ...]] = (
    "base",
    "category_accelerator",
    "merchant_accelerator",
    "channel_specific",
    "promotional",
)
CAP_PERIODS: Final[tuple[str, ...]] = (
    "monthly",
    "quarterly",
    "annual",
    "billing_cycle",
)
RESET_BASES: Final[tuple[str, ...]] = (
    "calendar_month",
    "calendar_quarter",
    "calendar_year",
    "statement_cycle",
)
LEDGER_STATUSES: Final[tuple[str, ...]] = (
    "potential",
    "pending",
    "confirmed",
    "credited",
    "reversed",
    "expired",
)


class RewardProgram(Base, TimestampMixin):
    """The rewards program associated with a credit card (e.g. Amazon Pay, Millennia, Rewards)."""

    __tablename__ = "reward_programs"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="CASCADE"), index=True
    )

    program_name: Mapped[str] = mapped_column(String(150))
    reward_type: Mapped[str] = mapped_column(String(30), default="cashback")
    reward_currency: Mapped[str] = mapped_column(String(20), default="INR")  # "INR" or "Points"
    # Valuation in INR per point (e.g. 1.0 for cashback, 0.25 for reward points)
    point_value_inr: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("1.0"), server_default="1.0"
    )
    expiry_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    rules: Mapped[list[RewardRule]] = relationship(
        "RewardRule", back_populates="program", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RewardProgram {self.program_name} type={self.reward_type}>"


class RewardRule(Base, TimestampMixin):
    """A versioned, effective-dated reward rate condition for a card."""

    __tablename__ = "reward_rules"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reward_programs.id", ondelete="CASCADE"), index=True
    )

    rule_name: Mapped[str] = mapped_column(String(150))
    rule_type: Mapped[str] = mapped_column(String(30), default="base")  # base, category, merchant, etc.

    # 0.05 = 5%, 0.015 = 1.5%
    reward_rate: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    reward_rate_type: Mapped[str] = mapped_column(
        String(20), default="percentage", server_default="percentage"
    )  # "percentage", "points_per_100", "fixed"

    min_transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), server_default="0"
    )
    max_eligible_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )

    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    merchant_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    channel: Mapped[str | None] = mapped_column(String(20), default="any")  # "online", "offline", "any"

    # Exclusions list: ["Fuel", "Wallet Reload", "Rent", "Jewellery"]
    exclusions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    conditions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Effective dates & versioning
    effective_from: Mapped[date] = mapped_column(Date, default=date.today)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    # Audit & source citations
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), default="verified", server_default="verified"
    )  # "verified", "unverified"
    confidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped[RewardProgram] = relationship("RewardProgram", back_populates="rules")
    caps: Mapped[list[RewardCap]] = relationship(
        "RewardCap", back_populates="rule", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RewardRule {self.rule_name} rate={self.reward_rate} v{self.version}>"


class RewardCap(Base, TimestampMixin):
    """Cap limits configured on a reward rule or program."""

    __tablename__ = "reward_caps"

    id: Mapped[uuid.UUID] = uuid_pk()
    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reward_rules.id", ondelete="CASCADE"), index=True
    )

    cap_name: Mapped[str] = mapped_column(String(150))
    cap_period: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly, quarterly, annual, billing_cycle
    reset_basis: Mapped[str] = mapped_column(
        String(30), default="calendar_month"
    )  # calendar_month, calendar_quarter, statement_cycle
    cap_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    cap_currency: Mapped[str] = mapped_column(String(20), default="INR")

    pending_consumes_cap: Mapped[bool] = mapped_column(Boolean, default=True)
    refunds_reverse_cap: Mapped[bool] = mapped_column(Boolean, default=True)

    rule: Mapped[RewardRule] = relationship("RewardRule", back_populates="caps")

    def __repr__(self) -> str:
        return f"<RewardCap {self.cap_name} amount={self.cap_amount} period={self.cap_period}>"


class RewardLedger(Base, TimestampMixin):
    """Audit ledger tracking reward events, cap consumption, and credit states."""

    __tablename__ = "reward_ledger"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reward_rules.id", ondelete="CASCADE"), index=True
    )
    cap_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reward_caps.id", ondelete="SET NULL"), index=True, nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", server_default="confirmed", index=True
    )
    reward_type: Mapped[str] = mapped_column(String(30), default="cashback")
    calculated_rate: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    reward_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    inr_value: Mapped[Decimal] = mapped_column(Numeric(18, 4))

    # Period key for fast cap aggregation (e.g. "2026-10", "2026-Q4", "2026-10-15_cycle")
    period_key: Mapped[str] = mapped_column(String(50), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    rule: Mapped[RewardRule] = relationship("RewardRule")
    cap: Mapped[RewardCap | None] = relationship("RewardCap")
    transaction: Mapped[Any | None] = relationship("Transaction", lazy="joined")
    card: Mapped[Any] = relationship("CreditCard", lazy="joined")

    def __repr__(self) -> str:
        return f"<RewardLedger {self.id} reward={self.reward_amount} ({self.status})>"
