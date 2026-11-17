"""Deterministic SQL analytics service for spend breakdowns and dashboard metrics."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import CreditCard
from app.models.transaction import Transaction
from app.schemas.analytics import (
    CardSpendPoint,
    CategorySpendPoint,
    DashboardSummary,
    MerchantSpendPoint,
    MonthlySpendPoint,
)
from app.services.payment_service import PaymentService


class AnalyticsService:
    """Calculates deterministic financial analytics via direct SQL queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_monthly_spend(
        self, user_id: uuid.UUID, card_id: uuid.UUID | None = None
    ) -> list[MonthlySpendPoint]:
        """Group debit spend by month (YYYY-MM)."""
        year_col = extract("year", Transaction.transaction_date).label("txn_year")
        month_col = extract("month", Transaction.transaction_date).label("txn_month")

        stmt = (
            select(
                year_col,
                month_col,
                func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_spend"),
                func.count(Transaction.id).label("txn_count"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.txn_type == "debit",
                Transaction.status.in_(["posted", "reconciled"]),
            )
            .group_by(year_col, month_col)
            .order_by(year_col.asc(), month_col.asc())
        )

        if card_id:
            stmt = stmt.where(Transaction.card_id == card_id)

        res = await self.db.execute(stmt)
        rows = res.all()

        points: list[MonthlySpendPoint] = []
        for r in rows:
            yr = int(r.txn_year)
            mo = int(r.txn_month)
            points.append(
                MonthlySpendPoint(
                    month=f"{yr:04d}-{mo:02d}",
                    total_spend=Decimal(str(r.total_spend)),
                    transaction_count=int(r.txn_count),
                )
            )
        return points

    async def get_category_spend(
        self,
        user_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        card_id: uuid.UUID | None = None,
    ) -> list[CategorySpendPoint]:
        """Spend breakdown by category."""
        stmt = select(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_spend"),
        ).where(
            Transaction.user_id == user_id,
            Transaction.txn_type == "debit",
            Transaction.status.in_(["posted", "reconciled"]),
        )

        if card_id:
            stmt = stmt.where(Transaction.card_id == card_id)
        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)

        stmt = stmt.group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc())

        res = await self.db.execute(stmt)
        rows = res.all()

        total_sum = sum((Decimal(str(r.total_spend)) for r in rows), Decimal("0"))

        points: list[CategorySpendPoint] = []
        for r in rows:
            spend = Decimal(str(r.total_spend))
            pct = float((spend / total_sum) * 100) if total_sum > 0 else 0.0
            points.append(
                CategorySpendPoint(
                    category=r.category,
                    total_spend=spend,
                    percentage=round(pct, 1),
                )
            )
        return points

    async def get_merchant_spend(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        card_id: uuid.UUID | None = None,
    ) -> list[MerchantSpendPoint]:
        """Top merchants by spend."""
        merchant_col = func.coalesce(Transaction.merchant_name, Transaction.cleaned_description)

        stmt = (
            select(
                merchant_col.label("merchant"),
                func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_spend"),
                func.count(Transaction.id).label("txn_count"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.txn_type == "debit",
                Transaction.status.in_(["posted", "reconciled"]),
            )
            .group_by(merchant_col)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )

        if card_id:
            stmt = stmt.where(Transaction.card_id == card_id)

        res = await self.db.execute(stmt)
        rows = res.all()

        return [
            MerchantSpendPoint(
                merchant=r.merchant,
                total_spend=Decimal(str(r.total_spend)),
                transaction_count=int(r.txn_count),
            )
            for r in rows
        ]

    async def get_card_spend(self, user_id: uuid.UUID) -> list[CardSpendPoint]:
        """Spend grouped by card."""
        stmt = (
            select(
                CreditCard.id.label("card_id"),
                CreditCard.card_name,
                CreditCard.issuer,
                func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_spend"),
            )
            .select_from(CreditCard)
            .join(Transaction, Transaction.card_id == CreditCard.id, isouter=True)
            .where(
                CreditCard.user_id == user_id,
                (Transaction.txn_type == "debit") | (Transaction.id.is_(None)),
            )
            .group_by(CreditCard.id, CreditCard.card_name, CreditCard.issuer)
            .order_by(func.sum(Transaction.amount).desc())
        )

        res = await self.db.execute(stmt)
        rows = res.all()

        return [
            CardSpendPoint(
                card_id=r.card_id,
                card_name=r.card_name,
                issuer=r.issuer,
                total_spend=Decimal(str(r.total_spend)),
            )
            for r in rows
        ]

    async def get_dashboard_summary(self, user_id: uuid.UUID) -> DashboardSummary:
        """Calculate live summary cards for the main overview."""
        today = date.today()

        # 1. Card balance & limit aggregation
        cards_res = await self.db.execute(
            select(
                func.count(CreditCard.id).label("cnt"),
                func.coalesce(func.sum(CreditCard.credit_limit), Decimal("0")).label("total_limit"),
                func.coalesce(func.sum(CreditCard.current_balance), Decimal("0")).label("total_balance"),
            ).where(
                CreditCard.user_id == user_id,
                CreditCard.status == "active",
            )
        )
        card_stats = cards_res.one()
        cnt = int(card_stats.cnt)
        total_limit = Decimal(str(card_stats.total_limit))
        total_balance = Decimal(str(card_stats.total_balance))
        total_available = max(Decimal("0"), total_limit - total_balance)
        utilization = float((total_balance / total_limit) * 100) if total_limit > 0 else 0.0

        # 2. Current Month Spend vs Previous Month Spend
        curr_yr = today.year
        curr_mo = today.month
        prev_yr = curr_yr if curr_mo > 1 else curr_yr - 1
        prev_mo = curr_mo - 1 if curr_mo > 1 else 12

        curr_spend_res = await self.db.execute(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
                Transaction.user_id == user_id,
                Transaction.txn_type == "debit",
                Transaction.status.in_(["posted", "reconciled"]),
                extract("year", Transaction.transaction_date) == curr_yr,
                extract("month", Transaction.transaction_date) == curr_mo,
            )
        )
        curr_spend = curr_spend_res.scalar_one()

        prev_spend_res = await self.db.execute(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
                Transaction.user_id == user_id,
                Transaction.txn_type == "debit",
                Transaction.status.in_(["posted", "reconciled"]),
                extract("year", Transaction.transaction_date) == prev_yr,
                extract("month", Transaction.transaction_date) == prev_mo,
            )
        )
        prev_spend = prev_spend_res.scalar_one()

        pct_change: float | None = None
        if prev_spend > 0:
            diff = float(curr_spend - prev_spend)
            pct_change = round((diff / float(prev_spend)) * 100, 1)

        # 3. Upcoming Dues
        payment_service = PaymentService(self.db)
        bills = await payment_service.get_cards_bill_status(user_id, today)

        upcoming_bills = [
            b for b in bills if 0 <= b.days_until_due <= 10 and b.remaining_balance > 0
        ]
        upcoming_dues_count = len(upcoming_bills)
        upcoming_dues_total = sum((b.remaining_balance for b in upcoming_bills), Decimal("0"))

        return DashboardSummary(
            total_outstanding=total_balance,
            total_credit_limit=total_limit,
            total_available_credit=total_available,
            overall_utilization=round(utilization, 1),
            active_cards_count=cnt,
            current_month_spend=curr_spend,
            previous_month_spend=prev_spend,
            spend_change_percentage=pct_change,
            upcoming_dues_count=upcoming_dues_count,
            upcoming_dues_total=upcoming_dues_total,
        )
