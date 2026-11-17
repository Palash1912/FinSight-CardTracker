"""Document knowledge, policy chunking, and RAG models (Phase 9)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Final

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk

DOC_TYPES: Final[tuple[str, ...]] = (
    "policy",
    "terms_and_conditions",
    "fee_schedule",
    "exclusion_circular",
    "other",
)
DOC_STATUSES: Final[tuple[str, ...]] = ("pending", "processing", "processed", "failed")


class Document(Base, TimestampMixin):
    """An ingested bank policy, terms sheet, or cardmember agreement PDF."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("credit_cards.id", ondelete="SET NULL"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(
        String(50), default="policy", server_default="policy", index=True
    )
    file_path: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    total_pages: Mapped[int] = mapped_column(Integer, default=1)

    status: Mapped[str] = mapped_column(
        String(30), default="processed", server_default="processed", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    card: Mapped[Any | None] = relationship("CreditCard", lazy="joined")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index.asc()",
    )

    def __repr__(self) -> str:
        return f"<Document {self.title} ({self.doc_type}) [{self.status}]>"


class DocumentChunk(Base):
    """A semantic text slice of a policy document with page attribution and vector embeddings."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # Embedding vector stored as JSON array of floats for cross-database portability
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    document: Mapped[Document] = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk doc={self.document_id} p.{self.page_number} idx={self.chunk_index}>"
