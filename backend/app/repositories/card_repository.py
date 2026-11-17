"""Data access for credit cards. Every query is scoped to an owner."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import CreditCard


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, card: CreditCard) -> None:
        self._session.add(card)

    async def persist(self, card: CreditCard) -> None:
        """Flush pending changes and reload server-generated values (timestamps)."""
        await self._session.flush()
        await self._session.refresh(card)

    async def list_for_user(
        self, user_id: uuid.UUID, *, include_archived: bool
    ) -> list[CreditCard]:
        statement = select(CreditCard).where(CreditCard.user_id == user_id)
        if not include_archived:
            statement = statement.where(CreditCard.status == "active")
        statement = statement.order_by(CreditCard.created_at, CreditCard.id)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_for_user(self, user_id: uuid.UUID, card_id: uuid.UUID) -> CreditCard | None:
        statement = select(CreditCard).where(
            CreditCard.id == card_id, CreditCard.user_id == user_id
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
