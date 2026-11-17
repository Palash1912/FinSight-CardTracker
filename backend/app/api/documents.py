"""Document knowledge, policy search, and RAG API router — /api/v1/documents."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.models.document import Document, DocumentChunk
from app.schemas.document import (
    DiscrepancyReportResponse,
    DocumentChunkRead,
    DocumentRead,
    PolicySearchRequest,
    PolicySearchResponse,
)
from app.services.document_service import DocumentService
from app.services.policy_rag import PolicyRAGService
from app.storage.local import LocalStorageProvider

router = APIRouter(prefix="/documents")


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File(...)],
    title: Annotated[str, Form(...)],
    doc_type: Annotated[str, Form()] = "policy",
    card_id: Annotated[uuid.UUID | None, Form()] = None,
) -> DocumentRead:
    """Upload a bank policy document or cardholder agreement PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported.",
        )

    settings = get_settings()
    storage = LocalStorageProvider(settings.storage_path)
    file_bytes = await file.read()

    doc = await DocumentService.ingest_document(
        db=db,
        storage=storage,
        user_id=user.id,
        file_bytes=file_bytes,
        file_name=file.filename,
        title=title,
        doc_type=doc_type,
        card_id=card_id,
    )
    return DocumentRead(
        id=doc.id,
        card_id=doc.card_id,
        title=doc.title,
        doc_type=doc.doc_type,
        file_name=doc.file_name,
        file_size_bytes=doc.file_size_bytes,
        total_pages=doc.total_pages,
        status=doc.status,
        created_at=doc.created_at,
        chunks_count=len(doc.chunks) if doc.chunks else 0,
    )


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    user: CurrentUser,
    db: DbSession,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[DocumentRead]:
    """List ingested policy documents."""
    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .options(selectinload(Document.chunks))
        .order_by(Document.created_at.desc())
    )
    if card_id:
        stmt = stmt.where(Document.card_id == card_id)

    docs = list((await db.execute(stmt)).scalars().all())
    return [
        DocumentRead(
            id=d.id,
            card_id=d.card_id,
            title=d.title,
            doc_type=d.doc_type,
            file_name=d.file_name,
            file_size_bytes=d.file_size_bytes,
            total_pages=d.total_pages,
            status=d.status,
            created_at=d.created_at,
            chunks_count=len(d.chunks),
        )
        for d in docs
    ]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    user: CurrentUser,
    db: DbSession,
    id: uuid.UUID,
) -> None:
    """Delete a document and its semantic chunks."""
    stmt = select(Document).where(Document.id == id, Document.user_id == user.id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    await db.delete(doc)
    await db.commit()


@router.post("/search", response_model=PolicySearchResponse)
async def search_policies(
    user: CurrentUser,
    db: DbSession,
    body: PolicySearchRequest,
) -> PolicySearchResponse:
    """Query policy knowledge base and retrieve grounded page citations."""
    return await PolicyRAGService.search_policies(db, user.id, body)


@router.get("/discrepancies", response_model=DiscrepancyReportResponse)
async def audit_discrepancies(
    user: CurrentUser,
    db: DbSession,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
) -> DiscrepancyReportResponse:
    """Compare active reward rules against bank policy texts to flag inconsistencies."""
    return await PolicyRAGService.audit_discrepancies(db, user.id, card_id=card_id)


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_policies(
    user: CurrentUser,
    db: DbSession,
) -> dict[str, int | str]:
    """Seed official bank terms and conditions fixtures."""
    count = await DocumentService.seed_default_policies(db, user.id)
    return {
        "status": "success",
        "message": f"Successfully seeded {count} official policy documents.",
        "seeded_count": count,
    }
