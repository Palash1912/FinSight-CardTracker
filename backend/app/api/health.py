"""Health-check endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.dependencies import DbSession
from app.schemas.common import HealthDbResponse, HealthResponse

router = APIRouter(prefix="/health")


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic liveness probe — always returns healthy if the process is running."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(UTC),
    )


@router.get("/db", response_model=HealthDbResponse)
async def health_db(db: DbSession) -> HealthDbResponse:
    """Readiness probe — verifies that the database is reachable."""
    try:
        await db.execute(text("SELECT 1"))
        return HealthDbResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.now(UTC),
            db_connected=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {exc}",
        ) from exc
