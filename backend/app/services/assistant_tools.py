"""Deterministic read-only financial tools for FinSight AI Assistant (Phase 8).

Strict rule: All financial metrics, bill balances, and reward amounts come
from deterministic calculations — zero arithmetic performed by the LLM.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import CreditCard
from app.models.transaction import Transaction
from app.schemas.reward import CardRecommendationRequest
from app.services.analytics_service import AnalyticsService
from app.services.billing import calculate_card_summary
from app.services.payment_service import PaymentService
from app.services.purchase_advisor import PurchaseAdvisor
from app.services.reward_reconciliation import RewardReconciliationService

ASSISTANT_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_card_summary",
            "description": "Get all active credit cards with limits, current balances, credit utilization %, and upcoming statement/due dates.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_dues",
            "description": "Get upcoming credit card bill amounts, minimum dues, due dates, overdue statuses, and days remaining for payment.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spending_analytics",
            "description": "Get monthly spend totals, month-over-month change %, top spending categories, and top merchants.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_purchase_rewards",
            "description": "Evaluate which credit card yields the highest cashback/points reward for a planned spend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Purchase amount in INR (e.g. 5000)"},
                    "merchant": {"type": "string", "description": "Merchant name (e.g. Amazon, Swiggy, Flipkart, HPCL)"},
                    "category": {"type": "string", "description": "Category (e.g. Shopping, Food & Dining, Travel, Fuel, Bills)"},
                    "channel": {"type": "string", "enum": ["online", "offline", "any"], "description": "Online or in-store purchase"},
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cap_status",
            "description": "Get current consumption and remaining balances for reward caps across all cards (e.g. 5% monthly partner caps).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_missing_rewards",
            "description": "Audit statement transactions for missed rewards, excluded categories (fuel/rent), and cap losses.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_transactions",
            "description": "Search recent transactions by merchant or description keywords.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword to search for (e.g. Swiggy, Amazon, Uber)"},
                    "limit": {"type": "integer", "description": "Maximum number of transactions to return (default 10)"},
                },
                "required": ["query"],
            },
        },
    },
]


class AssistantTools:
    """Executes deterministic read-only financial tools for the AI assistant."""

    @classmethod
    async def get_card_summary(cls, db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        card_stmt = select(CreditCard).where(
            CreditCard.user_id == user_id, CreditCard.status == "active"
        )
        cards = list((await db.execute(card_stmt)).scalars().all())

        results = []
        for c in cards:
            summary = calculate_card_summary(c)
            results.append(
                {
                    "card_id": str(c.id),
                    "issuer": c.issuer,
                    "card_name": c.card_name,
                    "last_four": c.last_four_digits,
                    "credit_limit": float(c.credit_limit),
                    "current_balance": float(c.current_balance),
                    "available_credit": float(summary.available_credit),
                    "utilization_percent": round(summary.utilization_percent, 1),
                    "next_statement_date": str(summary.next_statement_date),
                    "next_due_date": str(summary.next_due_date),
                }
            )
        return {"total_active_cards": len(results), "cards": results}

    @classmethod
    async def get_upcoming_dues(cls, db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        bills = await PaymentService(db).get_card_bills(user_id)
        results = []
        for b in bills:
            results.append(
                {
                    "card_name": b.card_name,
                    "issuer": b.issuer,
                    "last_four": b.last_four_digits,
                    "statement_amount": float(b.statement_amount),
                    "minimum_due": float(b.minimum_due),
                    "total_paid": float(b.total_paid),
                    "remaining_balance": float(b.remaining_balance),
                    "due_date": str(b.due_date),
                    "days_until_due": b.days_until_due,
                    "status": b.status,
                    "is_overdue": b.is_overdue,
                }
            )
        return {"bills": results}

    @classmethod
    async def get_spending_analytics(cls, db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        analytics = AnalyticsService(db)
        summary = await analytics.get_dashboard_summary(user_id)
        categories = await analytics.get_category_spend(user_id)
        merchants = await analytics.get_top_merchants(user_id, limit=5)

        return {
            "current_month_spend": float(summary.current_month_spend),
            "previous_month_spend": float(summary.previous_month_spend),
            "spend_change_percent": summary.spend_change_percentage,
            "overall_utilization_percent": summary.overall_utilization,
            "total_outstanding": float(summary.total_outstanding),
            "top_categories": [
                {"category": c.category, "spend": float(c.total_spend), "percentage": c.percentage}
                for c in categories[:5]
            ],
            "top_merchants": [
                {"merchant": m.merchant, "spend": float(m.total_spend), "count": m.transaction_count}
                for m in merchants
            ],
        }

    @classmethod
    async def evaluate_purchase_rewards(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: float,
        merchant: str = "",
        category: str = "Shopping",
        channel: str = "online",
    ) -> dict[str, Any]:
        req = CardRecommendationRequest(
            amount=Decimal(str(amount)),
            merchant=merchant,
            category=category,
            channel=channel,  # type: ignore[arg-type]
        )
        res = await PurchaseAdvisor.recommend_card(db, user_id, req)

        if not res.best_card:
            return {"error": "No active cards configured or spend is excluded from rewards."}

        cards_eval = [
            {
                "card_name": c.card_name,
                "issuer": c.issuer,
                "last_four": c.last_four_digits,
                "rank": c.rank,
                "is_recommended": c.is_recommended,
                "effective_rate_percent": c.effective_rate_percent,
                "net_reward_inr": float(c.inr_value),
                "rule_applied": c.rule_applied,
                "explanation": c.explanation,
                "remaining_cap_after": float(c.remaining_cap_after) if c.remaining_cap_after else None,
            }
            for c in res.cards
        ]

        return {
            "recommended_card": {
                "card_name": res.best_card.card_name,
                "issuer": res.best_card.issuer,
                "last_four": res.best_card.last_four_digits,
                "effective_rate_percent": res.best_card.effective_rate_percent,
                "net_reward_inr": float(res.best_card.inr_value),
                "explanation": res.best_card.explanation,
            },
            "all_cards_comparison": cards_eval,
            "disclaimer": res.disclaimer,
        }

    @classmethod
    async def get_cap_status(cls, db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        caps = await PurchaseAdvisor.get_cap_utilization(db, user_id)
        results = [
            {
                "card_name": c.card_name,
                "issuer": c.issuer,
                "cap_name": c.cap_name,
                "cap_period": c.cap_period,
                "cap_amount": float(c.cap_amount),
                "consumed_amount": float(c.consumed_amount),
                "remaining_amount": float(c.remaining_amount),
                "utilization_percent": c.utilization_percentage,
                "next_reset_date": str(c.next_reset_date),
            }
            for c in caps
        ]
        return {"caps": results}

    @classmethod
    async def detect_missing_rewards(cls, db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        rep = await RewardReconciliationService.get_reconciliation_report(db, user_id)
        discrepancies = [
            {
                "date": str(i.transaction_date),
                "card": i.card_name,
                "description": i.description,
                "amount": float(i.amount),
                "status": i.status,
                "reason": i.discrepancy_reason or i.notes,
            }
            for i in rep.items
            if i.is_discrepancy
        ]
        return {
            "total_expected_rewards_inr": float(rep.total_rewards_inr),
            "total_excluded_spend_inr": float(rep.total_excluded_spend),
            "total_capped_lost_inr": float(rep.total_capped_lost_inr),
            "discrepancy_count": rep.discrepancy_count,
            "flagged_items": discrepancies[:10],
        }

    @classmethod
    async def search_transactions(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        q_clean = f"%{query.strip().lower()}%"
        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                (Transaction.cleaned_description.ilike(q_clean))
                | (Transaction.merchant_name.ilike(q_clean)),
            )
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )
        txns = list((await db.execute(stmt)).scalars().all())
        results = [
            {
                "date": str(t.transaction_date),
                "description": t.cleaned_description,
                "merchant": t.merchant_name,
                "category": t.category,
                "amount": float(t.amount),
                "type": t.txn_type,
            }
            for t in txns
        ]
        return {"count": len(results), "transactions": results}
