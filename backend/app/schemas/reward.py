"""Pydantic v2 schemas for rewards intelligence and card recommendations."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Money = Decimal
Channel = Literal["online", "offline", "any"]
RewardType = Literal["cashback", "reward_points", "miles"]
CapPeriod = Literal["monthly", "quarterly", "annual", "billing_cycle"]


class RewardCapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_id: uuid.UUID
    cap_name: str
    cap_period: str
    reset_basis: str
    cap_amount: Money
    cap_currency: str
    pending_consumes_cap: bool
    refunds_reverse_cap: bool


class RewardRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_id: uuid.UUID
    rule_name: str
    rule_type: str
    reward_rate: Money
    reward_rate_type: str
    min_transaction_amount: Money
    max_eligible_amount: Money | None
    category: str | None
    merchant_pattern: str | None
    channel: str | None
    exclusions: list[str] | None
    effective_from: date
    effective_to: date | None
    version: int
    source_url: str | None
    verification_status: str
    confidence_notes: str | None
    caps: list[RewardCapRead] = []


class RewardProgramRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID
    program_name: str
    reward_type: str
    reward_currency: str
    point_value_inr: Money
    expiry_months: int | None
    rules: list[RewardRuleRead] = []


class CardRecommendationRequest(BaseModel):
    """User input for pre-purchase card evaluation."""

    amount: Money = Field(gt=0, max_digits=18, decimal_places=4)
    merchant: str = Field(default="", max_length=255)
    category: str = Field(default="Shopping", max_length=100)
    channel: Channel = "online"
    purchase_date: date | None = None


class CardRecommendationItem(BaseModel):
    """Evaluation result for a specific credit card."""

    card_id: uuid.UUID
    card_name: str
    issuer: str
    network: str
    last_four_digits: str
    is_recommended: bool
    rank: int
    effective_rate_percent: float
    estimated_reward: Money
    inr_value: Money
    reward_type: str
    rule_applied: str
    remaining_cap_before: Money | None
    remaining_cap_after: Money | None
    cap_period: str | None
    explanation: str
    verification_status: str
    confidence_notes: str | None


class CardRecommendationResponse(BaseModel):
    """Ranked comparison across all cards for a planned purchase."""

    best_card: CardRecommendationItem | None
    cards: list[CardRecommendationItem]
    purchase_amount: Money
    disclaimer: str = (
        "Reward estimates depend on configured and verified issuer terms and may differ "
        "from actual bank postings. Caps, exclusions, and merchant category codes apply."
    )


class CapUtilizationItem(BaseModel):
    """Active period cap tracking for a card."""

    card_id: uuid.UUID
    card_name: str
    issuer: str
    cap_name: str
    cap_period: str
    reset_basis: str
    cap_amount: Money
    consumed_amount: Money
    remaining_amount: Money
    utilization_percentage: float
    next_reset_date: date


class RewardSummaryOverview(BaseModel):
    """High level rewards dashboard stats."""

    total_cashback_earned: Money
    total_points_balance: int
    total_inr_value: Money
    active_programs_count: int


class RewardReconcileRequest(BaseModel):
    """Request to trigger transaction reward calculation and reconciliation."""

    card_id: uuid.UUID | None = None
    statement_id: uuid.UUID | None = None
    force_recalculate: bool = False


class RewardReconciliationItem(BaseModel):
    """Single transaction reward reconciliation status."""

    transaction_id: uuid.UUID
    card_id: uuid.UUID
    card_name: str
    transaction_date: date
    description: str
    merchant_name: str | None
    category: str
    amount: Money
    txn_type: str
    rule_name: str | None
    rate_percent: float
    reward_amount: Money
    inr_value: Money
    status: str
    is_discrepancy: bool
    discrepancy_reason: str | None
    period_key: str | None
    notes: str | None


class RewardReconciliationSummary(BaseModel):
    """Aggregated reconciliation report for a card, statement, or overall."""

    total_transactions: int
    total_spend: Money
    total_rewards_inr: Money
    total_excluded_spend: Money
    total_capped_lost_inr: Money
    discrepancy_count: int
    items: list[RewardReconciliationItem]

