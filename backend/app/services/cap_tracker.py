"""Reward cap tracker and period calculation engine."""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reward import RewardCap, RewardLedger


def get_period_key(
    reset_basis: str, ref_date: date, billing_cycle_day: int = 15
) -> str:
    """Compute period partition key for cap tracking."""
    yr = ref_date.year
    mo = ref_date.month

    if reset_basis == "calendar_month":
        return f"{yr:04d}-{mo:02d}"

    if reset_basis == "calendar_quarter":
        quarter = (mo - 1) // 3 + 1
        return f"{yr:04d}-Q{quarter}"

    if reset_basis == "calendar_year":
        return f"{yr:04d}"

    if reset_basis == "statement_cycle":
        # Cycle begins on billing_cycle_day of current or previous month
        if ref_date.day >= billing_cycle_day:
            return f"{yr:04d}-{mo:02d}-c{billing_cycle_day}"
        else:
            prev_mo = mo - 1 if mo > 1 else 12
            prev_yr = yr if mo > 1 else yr - 1
            return f"{prev_yr:04d}-{prev_mo:02d}-c{billing_cycle_day}"

    # Default fallback
    return f"{yr:04d}-{mo:02d}"


def get_next_reset_date(
    reset_basis: str, ref_date: date, billing_cycle_day: int = 15
) -> date:
    """Calculate the exact date when the cap resets."""
    yr = ref_date.year
    mo = ref_date.month

    if reset_basis == "calendar_month":
        # First day of next month
        if mo == 12:
            return date(yr + 1, 1, 1)
        return date(yr, mo + 1, 1)

    if reset_basis == "calendar_quarter":
        quarter = (mo - 1) // 3 + 1
        next_q_month = quarter * 3 + 1
        if next_q_month > 12:
            return date(yr + 1, 1, 1)
        return date(yr, next_q_month, 1)

    if reset_basis == "calendar_year":
        return date(yr + 1, 1, 1)

    if reset_basis == "statement_cycle":
        if ref_date.day >= billing_cycle_day:
            # Next month on billing_cycle_day
            if mo == 12:
                return date(yr + 1, 1, billing_cycle_day)
            return date(yr, mo + 1, billing_cycle_day)
        else:
            return date(yr, mo, billing_cycle_day)

    return date(yr, mo + 1, 1)


async def get_consumed_cap(
    db: AsyncSession,
    user_id: uuid.UUID,
    card_id: uuid.UUID,
    rule_id: uuid.UUID,
    period_key: str,
) -> Decimal:
    """Calculate total rewards consumed against a specific rule in the period."""
    stmt = select(func.coalesce(func.sum(RewardLedger.reward_amount), Decimal("0"))).where(
        RewardLedger.user_id == user_id,
        RewardLedger.card_id == card_id,
        RewardLedger.rule_id == rule_id,
        RewardLedger.period_key == period_key,
        RewardLedger.status.in_(["pending", "confirmed", "credited"]),
    )
    res = await db.execute(stmt)
    return res.scalar_one()
