"""Deterministic financial analytics API endpoints — /api/v1/analytics."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import CurrentUser, DbSession
from app.schemas.analytics import (
    CardSpendPoint,
    CategorySpendPoint,
    DashboardSummary,
    MerchantSpendPoint,
    MonthlySpendPoint,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics")


def get_analytics_service(db: DbSession) -> AnalyticsService:
    return AnalyticsService(db)


AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    user: CurrentUser,
    service: AnalyticsServiceDep,
) -> DashboardSummary:
    """Consolidated KPI metrics for the user overview."""
    return await service.get_dashboard_summary(user.id)


@router.get("/monthly", response_model=list[MonthlySpendPoint])
async def get_monthly_spend(
    user: CurrentUser,
    service: AnalyticsServiceDep,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[MonthlySpendPoint]:
    """Monthly spend time-series points."""
    return await service.get_monthly_spend(user.id, card_id=card_id)


@router.get("/categories", response_model=list[CategorySpendPoint])
async def get_category_spend(
    user: CurrentUser,
    service: AnalyticsServiceDep,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[CategorySpendPoint]:
    """Category breakdown percentages."""
    return await service.get_category_spend(
        user.id,
        start_date=start_date,
        end_date=end_date,
        card_id=card_id,
    )


@router.get("/merchants", response_model=list[MerchantSpendPoint])
async def get_top_merchants(
    user: CurrentUser,
    service: AnalyticsServiceDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[MerchantSpendPoint]:
    """Top merchant rankings by spend."""
    return await service.get_merchant_spend(user.id, limit=limit, card_id=card_id)


@router.get("/cards", response_model=list[CardSpendPoint])
async def get_card_spend(
    user: CurrentUser,
    service: AnalyticsServiceDep,
) -> list[CardSpendPoint]:
    """Spend distribution across cards."""
    return await service.get_card_spend(user.id)
