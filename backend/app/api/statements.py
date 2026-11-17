"""Statement ingestion and review API endpoints — /api/v1/statements."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.config import Settings
from app.dependencies import CurrentSettings, CurrentUser, DbSession
from app.schemas.statement import StatementConfirmRequest, StatementRead, StatementReviewDetail
from app.services.statement_service import (
    CardMatchError,
    DuplicateStatementError,
    StatementError,
    StatementNotFoundError,
    StatementService,
)
from app.storage.local import LocalStorageProvider

router = APIRouter(prefix="/statements")


def get_statement_service(db: DbSession, settings: CurrentSettings) -> StatementService:
    storage = LocalStorageProvider(settings.storage_path)
    return StatementService(db, storage, settings)


StatementServiceDep = Annotated[StatementService, Depends(get_statement_service)]


@router.post(
    "/upload",
    response_model=StatementReviewDetail,
    status_code=status.HTTP_201_CREATED,
)
async def upload_statement(
    user: CurrentUser,
    service: StatementServiceDep,
    file: Annotated[UploadFile, File(...)],
    card_id: Annotated[uuid.UUID | None, Form()] = None,
) -> StatementReviewDetail:
    """Upload a credit card statement PDF, extract transactions, and stage for review."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF bank statements are supported.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    try:
        review_data = await service.upload_and_process(
            user_id=user.id,
            file_bytes=content,
            file_name=file.filename,
            card_id=card_id,
        )
        return review_data
    except DuplicateStatementError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except CardMatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except StatementError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[StatementRead])
async def list_statements(
    user: CurrentUser,
    service: StatementServiceDep,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[StatementRead]:
    """List uploaded statements."""
    statements = await service.list_statements(user.id, card_id=card_id)
    return [StatementRead.model_validate(s) for s in statements]


@router.get("/{statement_id}", response_model=StatementReviewDetail)
async def get_statement_review(
    user: CurrentUser,
    service: StatementServiceDep,
    statement_id: uuid.UUID,
) -> StatementReviewDetail:
    """Get statement details and staged transactions for the review screen."""
    try:
        return await service.get_statement_review(user.id, statement_id)
    except StatementNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{statement_id}/confirm", response_model=StatementRead)
async def confirm_statement_import(
    user: CurrentUser,
    service: StatementServiceDep,
    statement_id: uuid.UUID,
    body: StatementConfirmRequest,
) -> StatementRead:
    """Confirm reviewed transactions and finalize import."""
    try:
        stmt = await service.confirm_statement(user.id, statement_id, body)
        return StatementRead.model_validate(stmt)
    except StatementNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_statement(
    user: CurrentUser,
    service: StatementServiceDep,
    statement_id: uuid.UUID,
) -> None:
    """Roll back and delete statement along with its transactions and stored file."""
    try:
        await service.delete_statement(user.id, statement_id)
    except StatementNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
