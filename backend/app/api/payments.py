"""Payments and bill tracking API endpoints — /api/v1/payments."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.payment import CardBillStatus, PaymentCreate, PaymentRead
from app.services.payment_service import (
    CardAccessError,
    PaymentNotFoundError,
    PaymentService,
)

router = APIRouter(prefix="/payments")


def get_payment_service(db: DbSession) -> PaymentService:
    return PaymentService(db)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    user: CurrentUser,
    service: PaymentServiceDep,
    body: PaymentCreate,
) -> PaymentRead:
    """Record a bill settlement or card payment."""
    try:
        payment = await service.create_payment(user.id, body)
        return PaymentRead.model_validate(payment)
    except CardAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[PaymentRead])
async def list_payments(
    user: CurrentUser,
    service: PaymentServiceDep,
    card_id: Annotated[uuid.UUID | None, Query()] = None,
    statement_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[PaymentRead]:
    """List historical payments made."""
    payments = await service.list_payments(user.id, card_id=card_id, statement_id=statement_id)
    return [PaymentRead.model_validate(p) for p in payments]


@router.get("/bills", response_model=list[CardBillStatus])
async def get_bills_status(
    user: CurrentUser,
    service: PaymentServiceDep,
) -> list[CardBillStatus]:
    """Retrieve billing and due date payment status across all active cards."""
    return await service.get_cards_bill_status(user.id)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    user: CurrentUser,
    service: PaymentServiceDep,
    payment_id: uuid.UUID,
) -> None:
    """Delete a recorded payment and restore card outstanding balance."""
    try:
        await service.delete_payment(user.id, payment_id)
    except PaymentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
