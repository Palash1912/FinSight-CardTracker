"""Root API router — aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.analytics import router as analytics_router
from app.api.cards import router as cards_router
from app.api.email import router as email_router
from app.api.health import router as health_router
from app.api.payments import router as payments_router
from app.api.rewards import router as rewards_router
from app.api.statements import router as statements_router
from app.api.transactions import router as transactions_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(cards_router, tags=["cards"])
api_router.include_router(statements_router, tags=["statements"])
api_router.include_router(transactions_router, tags=["transactions"])
api_router.include_router(payments_router, tags=["payments"])
api_router.include_router(analytics_router, tags=["analytics"])
api_router.include_router(rewards_router, tags=["rewards"])
api_router.include_router(email_router, tags=["email"])
