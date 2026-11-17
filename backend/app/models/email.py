"""Email connection and statement import audit models for Phase 7."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Final

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk

SYNC_STATUSES: Final[tuple[str, ...]] = ("idle", "syncing", "error", "disconnected")
IMPORT_STATUSES: Final[tuple[str, ...]] = (
    "discovered",
    "downloaded",
    "ingested",
    "skipped_duplicate",
    "failed",
)


class EmailConnection(Base, TimestampMixin):
    """Connected email provider account (e.g. Gmail OAuth) for automated statement retrieval."""

    __tablename__ = "email_connections"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    email_address: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(50), default="gmail", server_default="gmail")

    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scopes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    sync_status: Mapped[str] = mapped_column(
        String(30), default="idle", server_default="idle", index=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    imports: Mapped[list[EmailImport]] = relationship(
        "EmailImport", back_populates="connection", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EmailConnection {self.email_address} ({self.provider}) [{self.sync_status}]>"


class EmailImport(Base, TimestampMixin):
    """Audit log of discovered bank statement emails and ingested attachments."""

    __tablename__ = "email_imports"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("email_connections.id", ondelete="CASCADE"), index=True
    )
    statement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("statements.id", ondelete="SET NULL"), index=True, nullable=True
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="SET NULL"), index=True, nullable=True
    )

    message_id: Mapped[str] = mapped_column(String(100), index=True)
    thread_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sender: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    received_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    attachment_name: Mapped[str] = mapped_column(String(255))
    attachment_sha256: Mapped[str] = mapped_column(String(64), index=True)

    status: Mapped[str] = mapped_column(
        String(30), default="discovered", server_default="discovered", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    connection: Mapped[EmailConnection] = relationship("EmailConnection", back_populates="imports")
    statement: Mapped[Any | None] = relationship("Statement", lazy="joined")
    card: Mapped[Any | None] = relationship("CreditCard", lazy="joined")

    def __repr__(self) -> str:
        return f"<EmailImport {self.attachment_name} ({self.status})>"
