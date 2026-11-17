"""Rewards intelligence API router — /api/v1/rewards."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.models.reward import RewardProgram, RewardRule
from app.schemas.reward import (
    CapUtilizationItem,
    CardRecommendationRequest,
    CardRecommendationResponse,
    RewardProgramRead,
    RewardSummaryOverview,
)
from app.services.purchase_advisor import PurchaseAdvisor
from app.services.seed_rewards import seed_user_reward_programs

router = APIRouter(prefix="/rewards")


@router.post("/recommend", response_model=CardRecommendationResponse)
async def recommend_card(
    user: CurrentUser,
    db: DbSession,
    body: CardRecommendationRequest,
) -> CardRecommendationResponse:
    """Evaluate all active cards and rank them for a planned purchase."""
    return await PurchaseAdvisor.recommend_card(db, user.id, body)


@router.get("/caps", response_model=list[CapUtilizationItem])
async def list_cap_utilization(
    user: CurrentUser,
    db: DbSession,
) -> list[CapUtilizationItem]:
    """Retrieve active period cap consumption across all user cards."""
    return await PurchaseAdvisor.get_cap_utilization(db, user.id)


@router.get("/summary", response_model=RewardSummaryOverview)
async def get_rewards_summary(
    user: CurrentUser,
    db: DbSession,
) -> RewardSummaryOverview:
    """Retrieve overall rewards analytics and balances."""
    return await PurchaseAdvisor.get_reward_summary(db, user.id)


@router.get("/programs", response_model=list[RewardProgramRead])
async def list_reward_programs(
    user: CurrentUser,
    db: DbSession,
) -> list[RewardProgramRead]:
    """List configured reward programs, rules, and caps for the current user."""
    stmt = (
        select(RewardProgram)
        .where(RewardProgram.user_id == user.id)
        .options(selectinload(RewardProgram.rules).selectinload(RewardRule.caps))
        .order_by(RewardProgram.created_at.asc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_rewards(
    user: CurrentUser,
    db: DbSession,
) -> dict[str, int | str]:
    """Seed or update realistic synthetic reward rules for user's existing cards."""
    count = await seed_user_reward_programs(db, user.id, override_existing=True)
    return {
        "status": "success",
        "message": f"Successfully configured reward programs for {count} cards.",
        "seeded_count": count,
    }
