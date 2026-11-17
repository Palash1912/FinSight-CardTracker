"""AI Financial Assistant API router — /api/v1/assistant."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.models.assistant import AIConversation, AIMessage
from app.schemas.assistant import (
    AIConversationRead,
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
)
from app.services.assistant_service import AssistantService

router = APIRouter(prefix="/assistant")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    user: CurrentUser,
    db: DbSession,
    body: ChatRequest,
) -> ChatResponse:
    """Send message to the AI Financial Assistant and receive deterministic tool-backed advice."""
    return await AssistantService.chat(db, user.id, body)


@router.get("/conversations", response_model=list[AIConversationRead])
async def list_conversations(
    user: CurrentUser,
    db: DbSession,
) -> list[AIConversationRead]:
    """List recent advisory conversations for the current user."""
    stmt = (
        select(AIConversation)
        .where(AIConversation.user_id == user.id)
        .options(selectinload(AIConversation.messages))
        .order_by(AIConversation.created_at.desc())
        .limit(20)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/conversations/{id}", response_model=AIConversationRead)
async def get_conversation(
    user: CurrentUser,
    db: DbSession,
    id: uuid.UUID,
) -> AIConversationRead:
    """Retrieve an advisory conversation and its message history."""
    stmt = (
        select(AIConversation)
        .where(AIConversation.id == id, AIConversation.user_id == user.id)
        .options(selectinload(AIConversation.messages))
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return conv


@router.delete("/conversations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    user: CurrentUser,
    db: DbSession,
    id: uuid.UUID,
) -> None:
    """Delete a conversation history."""
    stmt = select(AIConversation).where(
        AIConversation.id == id, AIConversation.user_id == user.id
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    await db.delete(conv)
    await db.commit()
