"""Pydantic v2 schemas for email connections and statement ingestion (Phase 7)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EmailConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email_address: str
    provider: str
    sync_status: str
    last_synced_at: datetime | None
    error_message: str | None
    created_at: datetime


class EmailImportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connection_id: uuid.UUID
    statement_id: uuid.UUID | None
    card_id: uuid.UUID | None
    sender: str
    subject: str
    received_at: datetime
    attachment_name: str
    status: str
    error_message: str | None
    created_at: datetime


class GmailAuthUrlResponse(BaseModel):
    """Google OAuth consent screen URL."""

    auth_url: str
    state: str


class GmailCallbackRequest(BaseModel):
    """Payload received from Google OAuth redirection."""

    code: str
    state: str | None = None


class GmailSyncRequest(BaseModel):
    """Request to trigger statement discovery over connected email."""

    connection_id: uuid.UUID | None = None
    days_back: int = Field(default=90, ge=1, le=365)


class GmailSyncResponse(BaseModel):
    """Outcome of Gmail statement discovery and ingestion."""

    connection_id: uuid.UUID
    email_address: str
    messages_found: int
    attachments_downloaded: int
    statements_created: int
    duplicates_skipped: int
    errors: list[str] = []
