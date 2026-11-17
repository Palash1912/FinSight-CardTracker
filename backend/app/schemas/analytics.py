"""Pydantic v2 schemas for deterministic dashboard analytics."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel

Money = Decimal


class MonthlySpendPoint(BaseModel):
    """Spend point in monthly time-series."""

    month: str  # YYYY-MM
    total_spend: Money
    transaction_count: int


class CategorySpendPoint(BaseModel):
    """Spend breakdown by category."""

    category: str
    total_spend: Money
    percentage: float


class MerchantSpendPoint(BaseModel):
    """Top merchant spend item."""

    merchant: str
    total_spend: Money
    transaction_count: int


class CardSpendPoint(BaseModel):
    """Spend breakdown by card."""

    card_id: uuid.UUID
    card_name: str
    issuer: str
    total_spend: Money


class DashboardSummary(BaseModel):
    """High-level summary metrics for the home dashboard."""

    total_outstanding: Money
    total_credit_limit: Money
    total_available_credit: Money
    overall_utilization: float
    active_cards_count: int
    current_month_spend: Money
    previous_month_spend: Money
    spend_change_percentage: float | None
    upcoming_dues_count: int
    upcoming_dues_total: Money
