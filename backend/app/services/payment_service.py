"""Payment tracking and bill status computation service."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import CreditCard
from app.models.payment import Payment
from app.models.statement import Statement
from app.schemas.payment import CardBillStatus, PaymentCreate
from app.services.billing import next_due_date, next_statement_date


class PaymentNotFoundError(Exception):
    """Payment record not found."""


class CardAccessError(Exception):
    """Card does not belong to user."""


class PaymentService:
    """Manages bill settlements, payments, and due date tracking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_payment(self, user_id: uuid.UUID, body: PaymentCreate) -> Payment:
        """Record a credit card payment and reduce the outstanding card balance."""
        # Validate card belongs to user
        card_res = await self.db.execute(
            select(CreditCard).where(
                CreditCard.id == body.card_id,
                CreditCard.user_id == user_id,
            )
        )
        card = card_res.scalar_one_or_none()
        if not card:
            raise CardAccessError("Credit card not found or access denied.")

        payment = Payment(
            user_id=user_id,
            card_id=card.id,
            statement_id=body.statement_id,
            payment_date=body.payment_date,
            amount=body.amount,
            currency="INR",
            payment_method=body.payment_method,
            reference_number=body.reference_number,
            notes=body.notes,
            status="completed",
        )
        self.db.add(payment)

        # Reduce card current balance (cannot go below zero)
        new_balance = max(Decimal("0"), card.current_balance - body.amount)
        card.current_balance = new_balance

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def list_payments(
        self,
        user_id: uuid.UUID,
        card_id: uuid.UUID | None = None,
        statement_id: uuid.UUID | None = None,
    ) -> list[Payment]:
        """List user payments with optional filters."""
        stmt = select(Payment).where(Payment.user_id == user_id)
        if card_id:
            stmt = stmt.where(Payment.card_id == card_id)
        if statement_id:
            stmt = stmt.where(Payment.statement_id == statement_id)

        stmt = stmt.order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete_payment(self, user_id: uuid.UUID, payment_id: uuid.UUID) -> bool:
        """Cancel and delete payment, restoring card balance."""
        res = await self.db.execute(
            select(Payment).where(Payment.id == payment_id, Payment.user_id == user_id)
        )
        payment = res.scalar_one_or_none()
        if not payment:
            raise PaymentNotFoundError("Payment not found.")

        # Restore card balance
        card_res = await self.db.execute(
            select(CreditCard).where(CreditCard.id == payment.card_id)
        )
        card = card_res.scalar_one_or_none()
        if card:
            card.current_balance += payment.amount

        await self.db.delete(payment)
        await self.db.commit()
        return True

    async def get_cards_bill_status(
        self, user_id: uuid.UUID, today: date | None = None
    ) -> list[CardBillStatus]:
        """Compute the active billing status, due date, and payment progress for all active cards."""
        current_date = today or date.today()

        # Fetch active cards
        cards_res = await self.db.execute(
            select(CreditCard).where(
                CreditCard.user_id == user_id,
                CreditCard.status == "active",
            )
        )
        cards = cards_res.scalars().all()

        bill_statuses: list[CardBillStatus] = []

        for card in cards:
            # Look for the latest statement for this card
            stmt_res = await self.db.execute(
                select(Statement)
                .where(
                    Statement.card_id == card.id,
                    Statement.status.in_(["imported", "pending_review"]),
                )
                .order_by(Statement.statement_date.desc())
                .limit(1)
            )
            latest_stmt = stmt_res.scalar_one_or_none()

            due = next_due_date(card.billing_cycle_day, card.payment_due_days, current_date)
            stmt_date = next_statement_date(card.billing_cycle_day, current_date)
            stmt_id = None
            statement_amount = card.current_balance
            minimum_due = Decimal("0")

            if latest_stmt:
                stmt_id = latest_stmt.id
                stmt_date = latest_stmt.statement_date
                due = latest_stmt.due_date
                statement_amount = latest_stmt.total_amount_due
                minimum_due = latest_stmt.minimum_amount_due

                # Calculate sum of payments made against this statement
                pay_res = await self.db.execute(
                    select(func.coalesce(func.sum(Payment.amount), Decimal("0"))).where(
                        Payment.card_id == card.id,
                        Payment.status == "completed",
                        (Payment.statement_id == latest_stmt.id)
                        | (Payment.payment_date >= latest_stmt.statement_date),
                    )
                )
                total_paid = pay_res.scalar_one()
            else:
                total_paid = Decimal("0")

            remaining = max(Decimal("0"), statement_amount - total_paid)
            days_until_due = (due - current_date).days

            # Determine status
            if statement_amount <= Decimal("0"):
                status = "NO_BILL"
            elif remaining <= Decimal("0"):
                status = "PAID"
            elif total_paid > Decimal("0"):
                status = "PARTIALLY_PAID"
            else:
                status = "UNPAID"

            is_overdue = days_until_due < 0 and remaining > Decimal("0")

            bill_statuses.append(
                CardBillStatus(
                    card_id=card.id,
                    card_name=card.card_name,
                    issuer=card.issuer,
                    last_four_digits=card.last_four_digits,
                    statement_id=stmt_id,
                    statement_date=stmt_date,
                    due_date=due,
                    statement_amount=statement_amount,
                    minimum_due=minimum_due,
                    total_paid=total_paid,
                    remaining_balance=remaining,
                    days_until_due=days_until_due,
                    status=status,
                    is_overdue=is_overdue,
                )
            )

        # Sort by nearest due date first
        bill_statuses.sort(key=lambda b: b.due_date)
        return bill_statuses
