"""Credit card endpoints — /api/v1/cards."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession
from app.repositories.card_repository import CardRepository
from app.schemas.card import CardCreate, CardRead, CardUpdate
from app.services.card_service import CardNotFoundError, CardService

router = APIRouter(prefix="/cards")


def get_card_service(db: DbSession) -> CardService:
    return CardService(CardRepository(db))


CardServiceDep = Annotated[CardService, Depends(get_card_service)]

NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")


@router.get("", response_model=list[CardRead])
async def list_cards(
    user: CurrentUser,
    service: CardServiceDep,
    include_archived: Annotated[bool, Query()] = False,
) -> list[CardRead]:
    cards = await service.list(user.id, include_archived=include_archived)
    today = date.today()
    return [CardRead.from_card(card, today) for card in cards]


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_card(user: CurrentUser, service: CardServiceDep, body: CardCreate) -> CardRead:
    card = await service.create(user.id, body)
    return CardRead.from_card(card, date.today())


@router.get("/{card_id}", response_model=CardRead)
async def get_card(user: CurrentUser, service: CardServiceDep, card_id: uuid.UUID) -> CardRead:
    try:
        card = await service.get(user.id, card_id)
    except CardNotFoundError as exc:
        raise NOT_FOUND from exc
    return CardRead.from_card(card, date.today())


@router.patch("/{card_id}", response_model=CardRead)
async def update_card(
    user: CurrentUser, service: CardServiceDep, card_id: uuid.UUID, body: CardUpdate
) -> CardRead:
    try:
        card = await service.update(user.id, card_id, body)
    except CardNotFoundError as exc:
        raise NOT_FOUND from exc
    return CardRead.from_card(card, date.today())


@router.post("/{card_id}/archive", response_model=CardRead)
async def archive_card(user: CurrentUser, service: CardServiceDep, card_id: uuid.UUID) -> CardRead:
    try:
        card = await service.archive(user.id, card_id)
    except CardNotFoundError as exc:
        raise NOT_FOUND from exc
    return CardRead.from_card(card, date.today())
