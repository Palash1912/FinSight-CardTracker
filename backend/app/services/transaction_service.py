"""Transaction management service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionFilterParams, TransactionUpdate


class TransactionNotFoundError(Exception):
    """Transaction not found."""


class TransactionService:
    """Handles querying and editing transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_transactions(
        self, user_id: uuid.UUID, params: TransactionFilterParams
    ) -> tuple[list[Transaction], int]:
        """Query transactions with filtering and pagination."""
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if params.card_id:
            stmt = stmt.where(Transaction.card_id == params.card_id)
        if params.statement_id:
            stmt = stmt.where(Transaction.statement_id == params.statement_id)
        if params.category:
            stmt = stmt.where(Transaction.category == params.category)
        if params.merchant:
            stmt = stmt.where(Transaction.merchant_name == params.merchant)
        if params.txn_type:
            stmt = stmt.where(Transaction.txn_type == params.txn_type)
        if params.start_date:
            stmt = stmt.where(Transaction.transaction_date >= params.start_date)
        if params.end_date:
            stmt = stmt.where(Transaction.transaction_date <= params.end_date)
        if params.search:
            search_pattern = f"%{params.search.strip()}%"
            stmt = stmt.where(
                Transaction.cleaned_description.ilike(search_pattern)
                | Transaction.merchant_name.ilike(search_pattern)
            )

        # Count total
        count_res = await self.db.execute(stmt)
        all_matches = count_res.scalars().all()
        total_count = len(all_matches)

        # Order & paginate
        stmt = stmt.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total_count

    async def get_transaction(self, user_id: uuid.UUID, txn_id: uuid.UUID) -> Transaction:
        res = await self.db.execute(
            select(Transaction).where(Transaction.id == txn_id, Transaction.user_id == user_id)
        )
        tx = res.scalar_one_or_none()
        if not tx:
            raise TransactionNotFoundError("Transaction not found.")
        return tx

    async def update_transaction(
        self, user_id: uuid.UUID, txn_id: uuid.UUID, update_data: TransactionUpdate
    ) -> Transaction:
        tx = await self.get_transaction(user_id, txn_id)

        if update_data.cleaned_description is not None:
            tx.cleaned_description = update_data.cleaned_description
        if update_data.merchant_name is not None:
            tx.merchant_name = update_data.merchant_name
        if update_data.category is not None:
            tx.category = update_data.category
        if update_data.status is not None:
            tx.status = update_data.status

        await self.db.commit()
        await self.db.refresh(tx)
        return tx

    async def delete_transaction(self, user_id: uuid.UUID, txn_id: uuid.UUID) -> bool:
        tx = await self.get_transaction(user_id, txn_id)
        await self.db.delete(tx)
        await self.db.commit()
        return True
