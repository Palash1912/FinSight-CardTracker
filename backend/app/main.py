"""FinSight AI — FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler — runs on startup and shutdown."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logger.info("FinSight AI API starting up")
    yield
    logger.info("FinSight AI API shutting down")


def create_app() -> FastAPI:
    """Application factory — builds and configures the FastAPI instance."""
    settings = get_settings()

    application = FastAPI(
        title="FinSight AI API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_app()
