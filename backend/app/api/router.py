"""Root API router — aggregates all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.cards import router as cards_router
from app.api.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(cards_router, tags=["cards"])

# Future routers will be included here, e.g.:
# api_router.include_router(statements_router, prefix="/statements", tags=["statements"])
