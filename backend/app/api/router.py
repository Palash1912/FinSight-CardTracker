"""Root API router — aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.cards import router as cards_router
from app.api.health import router as health_router
from app.api.statements import router as statements_router
from app.api.transactions import router as transactions_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(cards_router, tags=["cards"])
api_router.include_router(statements_router, tags=["statements"])
api_router.include_router(transactions_router, tags=["transactions"])
