"""Purchase advisor service for pre-purchase recommendation and cap tracking."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import CreditCard
from app.models.reward import RewardCap, RewardLedger, RewardProgram, RewardRule
from app.schemas.reward import (
    CapUtilizationItem,
    CardRecommendationItem,
    CardRecommendationRequest,
    CardRecommendationResponse,
    RewardSummaryOverview,
)
from app.services.cap_tracker import (
    get_consumed_cap,
    get_next_reset_date,
    get_period_key,
)
from app.services.reward_engine import RewardEngine


class PurchaseAdvisor:
    """Orchestrates pre-purchase card selection and live cap analytics."""

    @classmethod
    async def recommend_card(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        req: CardRecommendationRequest,
    ) -> CardRecommendationResponse:
        """Evaluate all active cards and rank them for the requested purchase."""
        eval_date = req.purchase_date or date.today()

        # 1. Fetch user's active cards
        card_stmt = (
            select(CreditCard)
            .where(CreditCard.user_id == user_id, CreditCard.status == "active")
            .order_by(CreditCard.card_name.asc())
        )
        card_res = await db.execute(card_stmt)
        cards = list(card_res.scalars().all())

        if not cards:
            return CardRecommendationResponse(
                best_card=None,
                cards=[],
                purchase_amount=req.amount,
            )

        # 2. Fetch reward programs with rules and caps for these cards
        prog_stmt = (
            select(RewardProgram)
            .where(
                RewardProgram.user_id == user_id,
                RewardProgram.card_id.in_([c.id for c in cards]),
            )
            .options(
                selectinload(RewardProgram.rules).selectinload(RewardRule.caps)
            )
        )
        prog_res = await db.execute(prog_stmt)
        programs = list(prog_res.scalars().all())
        prog_by_card: dict[uuid.UUID, RewardProgram] = {p.card_id: p for p in programs}

        evaluations: list[CardRecommendationItem] = []

        for card in cards:
            program = prog_by_card.get(card.id)
            if not program or not program.rules:
                # No reward program configured for this card
                evaluations.append(
                    CardRecommendationItem(
                        card_id=card.id,
                        card_name=card.card_name,
                        issuer=card.issuer,
                        network=card.network,
                        last_four_digits=card.last_four_digits,
                        is_recommended=False,
                        rank=99,
                        effective_rate_percent=0.0,
                        estimated_reward=Decimal("0"),
                        inr_value=Decimal("0"),
                        reward_type="cashback",
                        rule_applied="None",
                        remaining_cap_before=None,
                        remaining_cap_after=None,
                        cap_period=None,
                        explanation="No reward program configured. Add reward rules to unlock recommendations.",
                        verification_status="unverified",
                        confidence_notes=None,
                    )
                )
                continue

            # Query consumed caps for rules in this program
            consumed_map: dict[uuid.UUID, Decimal] = {}
            for r in program.rules:
                if r.caps:
                    for cap in r.caps:
                        period_key = get_period_key(
                            cap.reset_basis, eval_date, card.billing_cycle_day
                        )
                        consumed = await get_consumed_cap(
                            db, user_id, card.id, r.id, period_key
                        )
                        consumed_map[r.id] = consumed

            res = RewardEngine.evaluate_card(
                card=card,
                program=program,
                rules=program.rules,
                amount=req.amount,
                merchant=req.merchant,
                category=req.category,
                channel=req.channel,
                purchase_date=eval_date,
                consumed_caps_map=consumed_map,
            )

            evaluations.append(
                CardRecommendationItem(
                    card_id=card.id,
                    card_name=card.card_name,
                    issuer=card.issuer,
                    network=card.network,
                    last_four_digits=card.last_four_digits,
                    is_recommended=False,
                    rank=99,
                    effective_rate_percent=res.effective_rate_percent,
                    estimated_reward=res.net_reward,
                    inr_value=res.inr_value,
                    reward_type=program.reward_type,
                    rule_applied=res.rule.rule_name if res.rule else "None",
                    remaining_cap_before=res.remaining_cap_before,
                    remaining_cap_after=res.remaining_cap_after,
                    cap_period=res.cap_period,
                    explanation=res.explanation,
                    verification_status=res.rule.verification_status if res.rule else "unverified",
                    confidence_notes=res.confidence_notes,
                )
            )

        # 3. Rank cards: inr_value desc, effective_rate_percent desc, issuer asc
        evaluations.sort(
            key=lambda it: (it.inr_value, it.effective_rate_percent),
            reverse=True,
        )

        best_card: CardRecommendationItem | None = None
        for idx, item in enumerate(evaluations):
            item.rank = idx + 1
            if idx == 0 and item.inr_value > Decimal("0"):
                item.is_recommended = True
                best_card = item
            elif idx == 0 and len(evaluations) == 1:
                best_card = item

        return CardRecommendationResponse(
            best_card=best_card,
            cards=evaluations,
            purchase_amount=req.amount,
        )

    @classmethod
    async def get_cap_utilization(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[CapUtilizationItem]:
        """Aggregate active cap utilization across all user cards."""
        today = date.today()

        stmt = (
            select(RewardCap)
            .join(RewardCap.rule)
            .join(RewardRule.program)
            .join(CreditCard, RewardProgram.card_id == CreditCard.id)
            .where(CreditCard.user_id == user_id, CreditCard.status == "active")
            .options(
                selectinload(RewardCap.rule).selectinload(RewardRule.program).selectinload(RewardProgram.rules)
            )
        )
        # Or load cards with programs directly for cleaner relationships
        cards_stmt = (
            select(CreditCard)
            .where(CreditCard.user_id == user_id, CreditCard.status == "active")
            .order_by(CreditCard.card_name.asc())
        )
        cards_res = await db.execute(cards_stmt)
        cards = list(cards_res.scalars().all())

        items: list[CapUtilizationItem] = []

        for card in cards:
            p_stmt = (
                select(RewardProgram)
                .where(RewardProgram.card_id == card.id, RewardProgram.user_id == user_id)
                .options(selectinload(RewardProgram.rules).selectinload(RewardRule.caps))
            )
            p_res = await db.execute(p_stmt)
            program = p_res.scalar_one_or_none()
            if not program:
                continue

            for rule in program.rules:
                for cap in rule.caps:
                    period_key = get_period_key(cap.reset_basis, today, card.billing_cycle_day)
                    consumed = await get_consumed_cap(db, user_id, card.id, rule.id, period_key)
                    rem = max(Decimal("0"), cap.cap_amount - consumed)
                    util_pct = (
                        min(100.0, float((consumed / cap.cap_amount) * 100))
                        if cap.cap_amount > 0
                        else 0.0
                    )
                    next_reset = get_next_reset_date(cap.reset_basis, today, card.billing_cycle_day)

                    items.append(
                        CapUtilizationItem(
                            card_id=card.id,
                            card_name=card.card_name,
                            issuer=card.issuer,
                            cap_name=cap.cap_name,
                            cap_period=cap.cap_period,
                            reset_basis=cap.reset_basis,
                            cap_amount=cap.cap_amount,
                            consumed_amount=consumed,
                            remaining_amount=rem,
                            utilization_percentage=round(util_pct, 1),
                            next_reset_date=next_reset,
                        )
                    )

        return items

    @classmethod
    async def get_reward_summary(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> RewardSummaryOverview:
        """Compute high-level rewards overview metrics."""
        # Total cashback
        cb_stmt = select(func.coalesce(func.sum(RewardLedger.inr_value), Decimal("0"))).where(
            RewardLedger.user_id == user_id,
            RewardLedger.reward_type == "cashback",
            RewardLedger.status.in_(["confirmed", "credited"]),
        )
        cb_res = await db.execute(cb_stmt)
        total_cashback = cb_res.scalar_one()

        # Total points balance
        pts_stmt = select(func.coalesce(func.sum(RewardLedger.reward_amount), Decimal("0"))).where(
            RewardLedger.user_id == user_id,
            RewardLedger.reward_type == "reward_points",
            RewardLedger.status.in_(["confirmed", "credited"]),
        )
        pts_res = await db.execute(pts_stmt)
        total_points = int(pts_res.scalar_one())

        # Total inr value
        inr_stmt = select(func.coalesce(func.sum(RewardLedger.inr_value), Decimal("0"))).where(
            RewardLedger.user_id == user_id,
            RewardLedger.status.in_(["confirmed", "credited"]),
        )
        inr_res = await db.execute(inr_stmt)
        total_inr = inr_res.scalar_one()

        # Active programs count
        prog_stmt = select(func.count(RewardProgram.id)).where(RewardProgram.user_id == user_id)
        prog_res = await db.execute(prog_stmt)
        active_progs = prog_res.scalar_one()

        return RewardSummaryOverview(
            total_cashback_earned=total_cashback,
            total_points_balance=total_points,
            total_inr_value=total_inr,
            active_programs_count=active_progs,
        )
