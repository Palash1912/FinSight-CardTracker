"""Shared test fixtures.

Database tests use an in-memory SQLite database (via aiosqlite) so they run
without Docker. Production uses PostgreSQL; only portable column types are used.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app as _app
from app.models import Base


@pytest.fixture
def app() -> FastAPI:
    """Return the FastAPI application instance."""
    return _app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Provide an async HTTP test client bound to the FastAPI app."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """In-memory SQLite engine with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def api_client(
    app: FastAPI, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client whose requests use the in-memory test database."""

    async def _test_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _test_get_db
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
