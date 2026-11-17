"""AI Assistant conversational history and message models (Phase 8)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class AIConversation(Base, TimestampMixin):
    """A chat session between a user and the FinSight AI financial advisor."""

    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(
        String(255), default="Financial Advisory Session", server_default="Financial Advisory Session"
    )

    messages: Mapped[list[AIMessage]] = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<AIConversation {self.id} title={self.title!r}>"


class AIMessage(Base):
    """An individual message or tool interaction within an AI conversation."""

    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    role: Mapped[str] = mapped_column(String(20), index=True)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text)

    # Optional structured tool calling metadata
    tool_calls: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), index=True
    )

    conversation: Mapped[AIConversation] = relationship(
        "AIConversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<AIMessage {self.id} role={self.role} content={self.content[:30]!r}>"
