"""Pydantic v2 schemas for the AI Financial Assistant (Phase 8)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    created_at: datetime


class AIConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime | None = None
    messages: list[ChatMessageRead] = []


class ChatRequest(BaseModel):
    """User input message sent to the financial advisor assistant."""

    conversation_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """Advisor assistant response and executed deterministic tools metadata."""

    conversation_id: uuid.UUID
    message: ChatMessageRead
    tool_calls_executed: list[dict[str, Any]] = []
