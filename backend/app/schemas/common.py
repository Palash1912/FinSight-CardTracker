"""Shared response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response for the basic health check endpoint."""

    status: str
    version: str
    timestamp: datetime


class HealthDbResponse(HealthResponse):
    """Response for the database health check endpoint."""

    db_connected: bool


class MessageResponse(BaseModel):
    """Generic single-message response."""

    message: str
