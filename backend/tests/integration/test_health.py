"""Integration tests for the health-check endpoints."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client: httpx.AsyncClient) -> None:
    """GET /api/v1/health should return 200 with status 'healthy'."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_contains_version_and_timestamp(client: httpx.AsyncClient) -> None:
    """GET /api/v1/health response must include version and timestamp fields."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


# NOTE: The /api/v1/health/db endpoint requires a running PostgreSQL instance.
# It is intentionally not tested here; run it with docker compose up.
# To generate the initial Alembic migration, start the database and run:
#   cd backend && alembic revision --autogenerate -m "initial schema"
