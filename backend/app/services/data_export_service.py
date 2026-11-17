"""Data export, CSV serialization, and privacy purge service (Phase 10)."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assistant import AIConversation
from app.models.card import CreditCard
from app.models.document import Document
from app.models.email import EmailConnection, EmailImport
from app.models.payment import Payment
from app.models.reward import RewardLedger, RewardProgram
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.user import User
from app.storage.base import StorageProvider


class DataExportService:
    """Manages full JSON data dumps, CSV transaction exports, and GDPR data purging."""

    @classmethod
    async def export_all(cls, db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        """Compile complete user financial data into an auditable JSON export."""
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        cards = list((await db.execute(select(CreditCard).where(CreditCard.user_id == user_id))).scalars().all())
        statements = list((await db.execute(select(Statement).where(Statement.user_id == user_id))).scalars().all())
        transactions = list((await db.execute(select(Transaction).where(Transaction.user_id == user_id))).scalars().all())
        payments = list((await db.execute(select(Payment).where(Payment.user_id == user_id))).scalars().all())

        programs = list(
            (
                await db.execute(
                    select(RewardProgram)
                    .where(RewardProgram.user_id == user_id)
                    .options(selectinload(RewardProgram.rules))
                )
            ).scalars().all()
        )
        ledgers = list((await db.execute(select(RewardLedger).where(RewardLedger.user_id == user_id))).scalars().all())
        connections = list((await db.execute(select(EmailConnection).where(EmailConnection.user_id == user_id))).scalars().all())
        imports = list((await db.execute(select(EmailImport).where(EmailImport.user_id == user_id))).scalars().all())

        conversations = list(
            (
                await db.execute(
                    select(AIConversation)
                    .where(AIConversation.user_id == user_id)
                    .options(selectinload(AIConversation.messages))
                )
            ).scalars().all()
        )
        documents = list((await db.execute(select(Document).where(Document.user_id == user_id))).scalars().all())

        return {
            "metadata": {
                "version": "1.0",
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": str(user_id),
                "email": user.email if user else "",
            },
            "cards": [
                {
                    "id": str(c.id),
                    "issuer": c.issuer,
                    "card_name": c.card_name,
                    "network": c.network,
                    "last_four": c.last_four_digits,
                    "credit_limit": str(c.credit_limit),
                    "current_balance": str(c.current_balance),
                    "billing_cycle_day": c.billing_cycle_day,
                    "payment_due_days": c.payment_due_days,
                }
                for c in cards
            ],
            "statements": [
                {
                    "id": str(s.id),
                    "card_id": str(s.card_id),
                    "statement_date": str(s.statement_date),
                    "due_date": str(s.due_date),
                    "total_amount_due": str(s.total_amount_due),
                    "minimum_amount_due": str(s.minimum_amount_due),
                    "status": s.status,
                    "file_name": s.file_name,
                }
                for s in statements
            ],
            "transactions": [
                {
                    "id": str(t.id),
                    "card_id": str(t.card_id),
                    "statement_id": str(t.statement_id) if t.statement_id else None,
                    "date": str(t.transaction_date),
                    "description": t.cleaned_description,
                    "merchant": t.merchant_name,
                    "category": t.category,
                    "amount": str(t.amount),
                    "type": t.txn_type,
                    "status": t.status,
                }
                for t in transactions
            ],
            "payments": [
                {
                    "id": str(p.id),
                    "card_id": str(p.card_id),
                    "payment_date": str(p.payment_date),
                    "amount": str(p.amount),
                    "payment_method": p.payment_method,
                    "reference_number": p.reference_number,
                    "status": p.status,
                }
                for p in payments
            ],
            "reward_programs": [
                {
                    "id": str(prog.id),
                    "card_id": str(prog.card_id),
                    "program_name": prog.program_name,
                    "reward_type": prog.reward_type,
                    "rules": [
                        {
                            "id": str(r.id),
                            "name": r.rule_name,
                            "type": r.rule_type,
                            "rate": str(r.reward_rate),
                            "exclusions": r.exclusions,
                        }
                        for r in prog.rules
                    ],
                }
                for prog in programs
            ],
            "reward_ledger_count": len(ledgers),
            "email_connections": [
                {
                    "id": str(conn.id),
                    "email_address": conn.email_address,
                    "provider": conn.provider,
                    "sync_status": conn.sync_status,
                }
                for conn in connections
            ],
            "conversations_count": len(conversations),
            "documents_count": len(documents),
        }

    @classmethod
    async def export_transactions_csv(cls, db: AsyncSession, user_id: uuid.UUID) -> str:
        """Export all transactions as a standard CSV format."""
        stmt = (
            select(Transaction, CreditCard)
            .join(CreditCard, Transaction.card_id == CreditCard.id)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc())
        )
        res = await db.execute(stmt)
        rows = res.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Transaction ID",
                "Date",
                "Card Issuer",
                "Card Name",
                "Last 4 Digits",
                "Description",
                "Merchant",
                "Category",
                "Amount (INR)",
                "Type",
                "Status",
            ]
        )

        for txn, card in rows:
            writer.writerow(
                [
                    str(txn.id),
                    str(txn.transaction_date),
                    card.issuer,
                    card.card_name,
                    card.last_four_digits,
                    txn.cleaned_description,
                    txn.merchant_name or "",
                    txn.category,
                    f"{txn.amount:.2f}",
                    txn.txn_type,
                    txn.status,
                ]
            )

        return output.getvalue()

    @classmethod
    async def purge_all(
        cls,
        db: AsyncSession,
        storage: StorageProvider,
        user_id: uuid.UUID,
    ) -> int:
        """Permanently cascades and deletes all data for the specified user."""
        # Deleting the user will cascade delete credit_cards, statements, transactions, payments,
        # reward_programs, reward_ledger, email_connections, ai_conversations, and documents
        stmt = delete(User).where(User.id == user_id)
        res = await db.execute(stmt)
        await db.commit()

        # Storage cleanup
        try:
            await storage.delete(f"statements/{user_id}")
            await storage.delete(f"policies/{user_id}")
        except Exception:
            pass

        return res.rowcount
