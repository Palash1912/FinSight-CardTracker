"""Transaction management API endpoints — /api/v1/transactions."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.transaction import (
    TransactionFilterParams,
    TransactionRead,
    TransactionUpdate,
    TxnType,
)
from app.services.transaction_service import TransactionNotFoundError, TransactionService

router = APIRouter(prefix="/transactions")


def get_transaction_service(db: DbSession) -> TransactionService:
    return TransactionService(db)


TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]


@router.get("", response_model=dict[str, Any])
async def list_transactions(
    user: CurrentUser,
    service: TransactionServiceDep,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
    statement_id: Annotated[uuid.UUID | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    merchant: Annotated[str | None, Query()] = None,
    txn_type: Annotated[TxnType | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    """Query transactions with optional filtering and pagination."""
    params = TransactionFilterParams(
        card_id=card_id,
        statement_id=statement_id,
        category=category,
        merchant=merchant,
        txn_type=txn_type,
        search=search,
        page=page,
        page_size=page_size,
    )
    items, total = await service.list_transactions(user.id, params)
    return {
        "items": [TransactionRead.model_validate(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    user: CurrentUser,
    service: TransactionServiceDep,
    transaction_id: uuid.UUID,
) -> TransactionRead:
    """Get single transaction by ID."""
    try:
        tx = await service.get_transaction(user.id, transaction_id)
        return TransactionRead.model_validate(tx)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    user: CurrentUser,
    service: TransactionServiceDep,
    transaction_id: uuid.UUID,
    body: TransactionUpdate,
) -> TransactionRead:
    """Update transaction category, merchant name, or description."""
    try:
        tx = await service.update_transaction(user.id, transaction_id, body)
        return TransactionRead.model_validate(tx)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    user: CurrentUser,
    service: TransactionServiceDep,
    transaction_id: uuid.UUID,
) -> None:
    """Delete a transaction."""
    try:
        await service.delete_transaction(user.id, transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
