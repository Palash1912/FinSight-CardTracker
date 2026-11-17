"""Business logic for credit cards."""

from __future__ import annotations

import uuid

from app.models.card import CreditCard
from app.repositories.card_repository import CardRepository
from app.schemas.card import CardCreate, CardUpdate


class CardNotFoundError(LookupError):
    """Raised when a card does not exist or belongs to another user."""


class CardService:
    def __init__(self, repository: CardRepository) -> None:
        self._repository = repository

    async def create(self, user_id: uuid.UUID, data: CardCreate) -> CreditCard:
        card = CreditCard(user_id=user_id, status="active", **data.model_dump())
        self._repository.add(card)
        await self._repository.persist(card)
        return card

    async def list(self, user_id: uuid.UUID, *, include_archived: bool = False) -> list[CreditCard]:
        return await self._repository.list_for_user(user_id, include_archived=include_archived)

    async def get(self, user_id: uuid.UUID, card_id: uuid.UUID) -> CreditCard:
        card = await self._repository.get_for_user(user_id, card_id)
        if card is None:
            raise CardNotFoundError(str(card_id))
        return card

    async def update(self, user_id: uuid.UUID, card_id: uuid.UUID, data: CardUpdate) -> CreditCard:
        card = await self.get(user_id, card_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(card, field, value)
        await self._repository.persist(card)
        return card

    async def archive(self, user_id: uuid.UUID, card_id: uuid.UUID) -> CreditCard:
        card = await self.get(user_id, card_id)
        card.status = "archived"
        await self._repository.persist(card)
        return card
