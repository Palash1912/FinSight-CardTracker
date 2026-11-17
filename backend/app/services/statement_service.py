"""Statement ingestion, parsing, deduplication, and reconciliation service."""

from __future__ import annotations

import hashlib
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.models.card import CreditCard
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.parsers.detector import detect_and_parse
from app.parsers.normalizer import (
    clean_description,
    extract_merchant_and_category,
    generate_fingerprint,
)
from app.schemas.statement import StatementConfirmRequest, StatementReviewDetail
from app.schemas.transaction import TransactionRead
from app.storage.base import StorageProvider


class StatementError(Exception):
    """Base exception for statement operations."""


class DuplicateStatementError(StatementError):
    """Uploaded statement has already been imported."""


class StatementNotFoundError(StatementError):
    """Statement was not found."""


class CardMatchError(StatementError):
    """Could not identify or associate a card for this statement."""


class StatementService:
    """Orchestrates PDF validation, storage, parsing, deduplication, and import."""

    def __init__(
        self,
        db: AsyncSession,
        storage: StorageProvider,
        settings: Settings,
    ) -> None:
        self.db = db
        self.storage = storage
        self.settings = settings

    async def upload_and_process(
        self,
        user_id: uuid.UUID,
        file_bytes: bytes,
        file_name: str,
        card_id: uuid.UUID | None = None,
    ) -> StatementReviewDetail:
        """Process an uploaded statement PDF through the ingestion pipeline."""
        # 1. Size validation
        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise StatementError(
                f"File size exceeds maximum allowed limit of {self.settings.max_upload_size_mb} MB"
            )

        # 2. SHA-256 Duplicate Check
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        existing = await self.db.execute(
            select(Statement).where(
                Statement.user_id == user_id,
                Statement.file_hash_sha256 == file_hash,
                Statement.status != "rejected",
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateStatementError(
                "This exact statement PDF has already been uploaded."
            )

        # 3. Text Extraction & Bank Parser Detection
        try:
            parsed_data, parser_name = detect_and_parse(file_bytes)
        except Exception as exc:
            raise StatementError(f"Failed to read or parse PDF: {exc}") from exc

        # 4. Resolve Target Credit Card
        target_card: CreditCard | None = None
        if card_id:
            res = await self.db.execute(
                select(CreditCard).where(
                    CreditCard.id == card_id,
                    CreditCard.user_id == user_id,
                )
            )
            target_card = res.scalar_one_or_none()
            if not target_card:
                raise CardMatchError("Specified credit card not found or access denied.")
        elif parsed_data.card_last_four:
            # Auto-match by last 4 digits
            res = await self.db.execute(
                select(CreditCard).where(
                    CreditCard.user_id == user_id,
                    CreditCard.last_four_digits == parsed_data.card_last_four,
                    CreditCard.status == "active",
                )
            )
            target_card = res.scalar_one_or_none()

        if not target_card:
            # Match first active card or require user selection
            res = await self.db.execute(
                select(CreditCard).where(
                    CreditCard.user_id == user_id,
                    CreditCard.status == "active",
                )
            )
            active_cards = res.scalars().all()
            if len(active_cards) == 1:
                target_card = active_cards[0]
            elif not active_cards:
                raise CardMatchError("No credit cards registered. Please add a card first.")
            else:
                raise CardMatchError(
                    "Multiple cards detected. Please explicitly select the target credit card."
                )

        # 5. Save Raw PDF to Secure Storage
        dest_path = f"statements/{user_id}/{target_card.id}/{file_hash[:16]}_{file_name}"
        saved_rel_path = await self.storage.save(file_bytes, dest_path)

        # Fallback dates if parser couldn't detect them
        stmt_date = parsed_data.statement_date or date.today()
        due_date = parsed_data.due_date or date.today()

        # 6. Create Statement in pending_review status
        statement = Statement(
            user_id=user_id,
            card_id=target_card.id,
            statement_date=stmt_date,
            due_date=due_date,
            period_start=parsed_data.period_start,
            period_end=parsed_data.period_end,
            total_amount_due=parsed_data.total_amount_due or Decimal("0"),
            minimum_amount_due=parsed_data.minimum_amount_due or Decimal("0"),
            opening_balance=parsed_data.opening_balance or Decimal("0"),
            closing_balance=parsed_data.closing_balance or Decimal("0"),
            total_credits=parsed_data.total_credits or Decimal("0"),
            total_debits=parsed_data.total_debits or Decimal("0"),
            file_hash_sha256=file_hash,
            file_path=saved_rel_path,
            file_name=file_name,
            file_size_bytes=len(file_bytes),
            parser_used=parser_name,
            status="pending_review",
        )
        self.db.add(statement)
        await self.db.flush()

        # 7. Normalize & Deduplicate Transactions
        created_transactions: list[Transaction] = []
        for raw_tx in parsed_data.transactions:
            cleaned = clean_description(raw_tx.description)
            merchant, category = extract_merchant_and_category(cleaned)
            fp = generate_fingerprint(
                card_id=target_card.id,
                txn_date=raw_tx.date,
                amount=raw_tx.amount,
                txn_type=raw_tx.txn_type,
                cleaned_desc=cleaned,
            )

            # Check if this exact transaction was already imported previously
            fp_exists = await self.db.execute(
                select(Transaction.id).where(
                    Transaction.card_id == target_card.id,
                    Transaction.fingerprint == fp,
                    Transaction.status.in_(["posted", "reconciled"]),
                )
            )
            if fp_exists.scalar_one_or_none():
                # Skip duplicate
                continue

            tx = Transaction(
                user_id=user_id,
                card_id=target_card.id,
                statement_id=statement.id,
                transaction_date=raw_tx.date,
                posting_date=raw_tx.posting_date,
                original_description=raw_tx.description,
                cleaned_description=cleaned,
                merchant_name=merchant,
                category=category,
                amount=raw_tx.amount,
                currency="INR",
                txn_type=raw_tx.txn_type,
                fingerprint=fp,
                source="pdf_statement",
                status="pending",
                source_page=raw_tx.source_page,
                source_row=raw_tx.source_row,
                original_values={
                    "raw_text": raw_tx.raw_text,
                    "raw_desc": raw_tx.description,
                    "raw_amount": str(raw_tx.amount),
                },
            )
            self.db.add(tx)
            created_transactions.append(tx)

        await self.db.commit()
        await self.db.refresh(statement)

        # Check reconciliation
        calc_net = (parsed_data.total_debits or Decimal("0")) - (
            parsed_data.total_credits or Decimal("0")
        )
        matched = False
        if parsed_data.total_amount_due:
            matched = abs(calc_net - parsed_data.total_amount_due) < Decimal("1.00")

        return StatementReviewDetail(
            id=statement.id,
            user_id=statement.user_id,
            card_id=statement.card_id,
            statement_date=statement.statement_date,
            due_date=statement.due_date,
            period_start=statement.period_start,
            period_end=statement.period_end,
            total_amount_due=statement.total_amount_due,
            minimum_amount_due=statement.minimum_amount_due,
            opening_balance=statement.opening_balance,
            closing_balance=statement.closing_balance,
            total_credits=statement.total_credits,
            total_debits=statement.total_debits,
            file_name=statement.file_name,
            file_size_bytes=statement.file_size_bytes,
            parser_used=statement.parser_used,
            status="pending_review",
            error_message=None,
            created_at=statement.created_at,
            updated_at=statement.updated_at,
            transactions=[TransactionRead.model_validate(t) for t in created_transactions],
            reconciliation_matched=matched,
            net_calculated=calc_net,
        )

    async def get_statement_review(
        self, user_id: uuid.UUID, statement_id: uuid.UUID
    ) -> StatementReviewDetail:
        """Fetch statement and its staged transactions for review."""
        res = await self.db.execute(
            select(Statement)
            .options(selectinload(Statement.transactions))
            .where(
                Statement.id == statement_id,
                Statement.user_id == user_id,
            )
        )
        statement = res.scalar_one_or_none()
        if not statement:
            raise StatementNotFoundError("Statement not found.")

        calc_net = statement.total_debits - statement.total_credits
        matched = False
        if statement.total_amount_due:
            matched = abs(calc_net - statement.total_amount_due) < Decimal("1.00")

        return StatementReviewDetail(
            id=statement.id,
            user_id=statement.user_id,
            card_id=statement.card_id,
            statement_date=statement.statement_date,
            due_date=statement.due_date,
            period_start=statement.period_start,
            period_end=statement.period_end,
            total_amount_due=statement.total_amount_due,
            minimum_amount_due=statement.minimum_amount_due,
            opening_balance=statement.opening_balance,
            closing_balance=statement.closing_balance,
            total_credits=statement.total_credits,
            total_debits=statement.total_debits,
            file_name=statement.file_name,
            file_size_bytes=statement.file_size_bytes,
            parser_used=statement.parser_used,
            status=statement.status,  # type: ignore[arg-type]
            error_message=statement.error_message,
            created_at=statement.created_at,
            updated_at=statement.updated_at,
            transactions=[TransactionRead.model_validate(t) for t in statement.transactions],
            reconciliation_matched=matched,
            net_calculated=calc_net,
        )

    async def confirm_statement(
        self,
        user_id: uuid.UUID,
        statement_id: uuid.UUID,
        req: StatementConfirmRequest,
    ) -> Statement:
        """Confirm reviewed transactions, update card balance, and finalize import."""
        res = await self.db.execute(
            select(Statement)
            .options(selectinload(Statement.transactions))
            .where(
                Statement.id == statement_id,
                Statement.user_id == user_id,
            )
        )
        statement = res.scalar_one_or_none()
        if not statement:
            raise StatementNotFoundError("Statement not found.")

        # Remove excluded transactions
        if req.excluded_transaction_ids:
            await self.db.execute(
                delete(Transaction).where(
                    Transaction.statement_id == statement.id,
                    Transaction.id.in_(req.excluded_transaction_ids),
                )
            )

        # Transition transactions to posted
        for tx in statement.transactions:
            if tx.id not in req.excluded_transaction_ids:
                tx.status = "posted"

        statement.status = "imported"

        # Update card balance if requested
        if req.update_card_balance and statement.total_amount_due > 0:
            card_res = await self.db.execute(
                select(CreditCard).where(CreditCard.id == statement.card_id)
            )
            card = card_res.scalar_one_or_none()
            if card:
                card.current_balance = statement.total_amount_due

        await self.db.commit()
        await self.db.refresh(statement)
        return statement

    async def list_statements(
        self, user_id: uuid.UUID, card_id: uuid.UUID | None = None
    ) -> list[Statement]:
        """List statements with optional card filter."""
        stmt = select(Statement).where(Statement.user_id == user_id)
        if card_id:
            stmt = stmt.where(Statement.card_id == card_id)
        stmt = stmt.order_by(Statement.statement_date.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete_statement(self, user_id: uuid.UUID, statement_id: uuid.UUID) -> bool:
        """Rollback and delete statement, stored file, and associated transactions."""
        res = await self.db.execute(
            select(Statement).where(
                Statement.id == statement_id,
                Statement.user_id == user_id,
            )
        )
        statement = res.scalar_one_or_none()
        if not statement:
            raise StatementNotFoundError("Statement not found.")

        # Delete from disk
        await self.storage.delete(statement.file_path)

        # Delete statement (cascades transactions in DB)
        await self.db.delete(statement)
        await self.db.commit()
        return True
