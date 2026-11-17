"""Post-purchase reward reconciliation service.

Evaluates statement transactions against credit card reward rules, detects
discrepancies (unrewarded spend, capped benefits, rate mismatches), and writes
to the deterministic RewardLedger.
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import CreditCard
from app.models.reward import RewardCap, RewardLedger, RewardProgram, RewardRule
from app.models.transaction import Transaction
from app.schemas.reward import (
    RewardReconciliationItem,
    RewardReconciliationSummary,
)
from app.services.cap_tracker import get_consumed_cap, get_period_key
from app.services.reward_engine import RewardEngine

CASHBACK_KEYWORDS = re.compile(r"(cashback|cash\s*point|reward\s*credit|reward\s*points)", re.IGNORECASE)
REFUND_KEYWORDS = re.compile(r"(refund|reversal|reversed|return)", re.IGNORECASE)


class RewardReconciliationService:
    """Orchestrates post-purchase reward calculations and discrepancy auditing."""

    @classmethod
    async def reconcile(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        card_id: uuid.UUID | None = None,
        statement_id: uuid.UUID | None = None,
        force_recalculate: bool = False,
    ) -> RewardReconciliationSummary:
        """Process transactions, calculate expected rewards, detect discrepancies, and persist ledger."""
        # 1. Fetch matching transactions
        query = select(Transaction).where(Transaction.user_id == user_id)
        if statement_id:
            query = query.where(Transaction.statement_id == statement_id)
        if card_id:
            query = query.where(Transaction.card_id == card_id)

        query = query.order_by(Transaction.transaction_date.asc(), Transaction.created_at.asc())
        txn_res = await db.execute(query)
        transactions = list(txn_res.scalars().all())

        if not transactions:
            return RewardReconciliationSummary(
                total_transactions=0,
                total_spend=Decimal("0.0000"),
                total_rewards_inr=Decimal("0.0000"),
                total_excluded_spend=Decimal("0.0000"),
                total_capped_lost_inr=Decimal("0.0000"),
                discrepancy_count=0,
                items=[],
            )

        # 2. Fetch cards involved
        card_ids = list({t.card_id for t in transactions})
        card_stmt = select(CreditCard).where(CreditCard.id.in_(card_ids))
        card_map: dict[uuid.UUID, CreditCard] = {
            c.id: c for c in (await db.execute(card_stmt)).scalars().all()
        }

        # 3. Fetch programs with rules and caps
        prog_stmt = (
            select(RewardProgram)
            .where(RewardProgram.user_id == user_id, RewardProgram.card_id.in_(card_ids))
            .options(selectinload(RewardProgram.rules).selectinload(RewardRule.caps))
        )
        programs = list((await db.execute(prog_stmt)).scalars().all())
        prog_map: dict[uuid.UUID, RewardProgram] = {p.card_id: p for p in programs}

        # 4. Fetch existing ledger entries for these transactions
        txn_ids = [t.id for t in transactions]
        existing_ledger_stmt = select(RewardLedger).where(
            RewardLedger.user_id == user_id,
            RewardLedger.transaction_id.in_(txn_ids),
        )
        existing_ledgers = list((await db.execute(existing_ledger_stmt)).scalars().all())
        existing_map: dict[uuid.UUID, RewardLedger] = {
            lg.transaction_id: lg for lg in existing_ledgers if lg.transaction_id
        }

        if force_recalculate and existing_ledgers:
            # Delete existing ledger entries for clean recalculation
            del_stmt = delete(RewardLedger).where(
                RewardLedger.id.in_([lg.id for lg in existing_ledgers])
            )
            await db.execute(del_stmt)
            await db.flush()
            existing_map.clear()

        # Track running consumed caps per (card_id, rule_id, period_key)
        running_consumed_caps: dict[tuple[uuid.UUID, uuid.UUID, str], Decimal] = {}

        items: list[RewardReconciliationItem] = []
        total_spend = Decimal("0")
        total_rewards_inr = Decimal("0")
        total_excluded_spend = Decimal("0")
        total_capped_lost_inr = Decimal("0")
        discrepancy_count = 0

        for txn in transactions:
            card = card_map.get(txn.card_id)
            card_name = card.card_name if card else "Unknown Card"
            program = prog_map.get(txn.card_id)

            # Handle credit transactions (payments, refunds, cashback credits)
            if txn.txn_type == "credit":
                is_cashback = bool(CASHBACK_KEYWORDS.search(txn.cleaned_description))
                is_refund = bool(REFUND_KEYWORDS.search(txn.cleaned_description))

                status = "credited" if is_cashback else ("reversed" if is_refund else "payment")
                reward_amt = txn.amount if is_cashback else Decimal("0")
                inr_val = reward_amt

                item = RewardReconciliationItem(
                    transaction_id=txn.id,
                    card_id=txn.card_id,
                    card_name=card_name,
                    transaction_date=txn.transaction_date,
                    description=txn.cleaned_description,
                    merchant_name=txn.merchant_name,
                    category=txn.category,
                    amount=txn.amount,
                    txn_type="credit",
                    rule_name="Statement Credit / Refund" if not is_cashback else "Cashback Posting",
                    rate_percent=0.0,
                    reward_amount=reward_amt,
                    inr_value=inr_val,
                    status=status,
                    is_discrepancy=False,
                    discrepancy_reason=None,
                    period_key=None,
                    notes="Direct statement credit/refund entry.",
                )
                items.append(item)
                continue

            # Debit Transaction (normal spend)
            total_spend += txn.amount

            # If already reconciled and not force_recalculate, reuse ledger
            existing_lg = existing_map.get(txn.id)
            if existing_lg:
                rule_name = existing_lg.rule.rule_name if existing_lg.rule else "Saved Rule"
                rate_pct = float(existing_lg.calculated_rate * 100) if existing_lg.calculated_rate <= 1 else float(existing_lg.calculated_rate)
                total_rewards_inr += existing_lg.inr_value

                is_discrepancy = existing_lg.status == "excluded" and txn.amount >= Decimal("1000")
                if is_discrepancy:
                    discrepancy_count += 1

                items.append(
                    RewardReconciliationItem(
                        transaction_id=txn.id,
                        card_id=txn.card_id,
                        card_name=card_name,
                        transaction_date=txn.transaction_date,
                        description=txn.cleaned_description,
                        merchant_name=txn.merchant_name,
                        category=txn.category,
                        amount=txn.amount,
                        txn_type="debit",
                        rule_name=rule_name,
                        rate_percent=rate_pct,
                        reward_amount=existing_lg.reward_amount,
                        inr_value=existing_lg.inr_value,
                        status=existing_lg.status,
                        is_discrepancy=is_discrepancy,
                        discrepancy_reason="Spend was excluded from rewards" if is_discrepancy else None,
                        period_key=existing_lg.period_key,
                        notes=existing_lg.notes,
                    )
                )
                continue

            # Evaluate with RewardEngine
            if not program or not program.rules:
                # No rules configured
                item = RewardReconciliationItem(
                    transaction_id=txn.id,
                    card_id=txn.card_id,
                    card_name=card_name,
                    transaction_date=txn.transaction_date,
                    description=txn.cleaned_description,
                    merchant_name=txn.merchant_name,
                    category=txn.category,
                    amount=txn.amount,
                    txn_type="debit",
                    rule_name="Unconfigured",
                    rate_percent=0.0,
                    reward_amount=Decimal("0"),
                    inr_value=Decimal("0"),
                    status="unconfigured",
                    is_discrepancy=True,
                    discrepancy_reason="No reward rules configured for card.",
                    period_key=None,
                    notes="Configure card reward program to calculate earnings.",
                )
                items.append(item)
                discrepancy_count += 1
                continue

            # Load active period consumed cap map for rules on this card
            cycle_day = card.billing_cycle_day if card else 15
            consumed_map: dict[uuid.UUID, Decimal] = {}
            for r in program.rules:
                if r.caps:
                    for cap in r.caps:
                        pk = get_period_key(cap.reset_basis, txn.transaction_date, cycle_day)
                        running_key = (txn.card_id, r.id, pk)
                        if running_key not in running_consumed_caps:
                            db_consumed = await get_consumed_cap(db, user_id, txn.card_id, r.id, pk)
                            running_consumed_caps[running_key] = db_consumed
                        consumed_map[r.id] = running_consumed_caps[running_key]

            eval_res = RewardEngine.evaluate_card(
                card=card,  # type: ignore[arg-type]
                program=program,
                rules=program.rules,
                amount=txn.amount,
                merchant=txn.merchant_name or txn.cleaned_description,
                category=txn.category,
                channel="any",
                purchase_date=txn.transaction_date,
                consumed_caps_map=consumed_map,
            )

            # Determine period partition key
            primary_cap = eval_res.rule.caps[0] if (eval_res.rule and eval_res.rule.caps) else None
            reset_basis = primary_cap.reset_basis if primary_cap else "calendar_month"
            period_key = get_period_key(reset_basis, txn.transaction_date, cycle_day)

            # Discrepancy checks
            is_discrepancy = False
            discrepancy_reason: str | None = None

            if not eval_res.eligible:
                status = "excluded"
                total_excluded_spend += txn.amount
                if txn.amount >= Decimal("500"):
                    is_discrepancy = True
                    discrepancy_reason = f"Excluded spend: {eval_res.explanation}"
            else:
                status = "confirmed"
                total_rewards_inr += eval_res.inr_value

                # Cap loss check (if gross was reduced by cap)
                loss = eval_res.gross_reward - eval_res.net_reward
                if loss > Decimal("0"):
                    loss_inr = loss * (program.point_value_inr if program.reward_type == "reward_points" else Decimal("1"))
                    total_capped_lost_inr += loss_inr
                    is_discrepancy = True
                    discrepancy_reason = f"Reward capped: ₹{loss_inr:.2f} benefit lost due to {eval_res.cap_period} cap."

                # Update running consumed cap for this rule
                if eval_res.rule and eval_res.rule.caps:
                    running_key = (txn.card_id, eval_res.rule.id, period_key)
                    running_consumed_caps[running_key] = running_consumed_caps.get(running_key, Decimal("0")) + eval_res.net_reward

            if is_discrepancy:
                discrepancy_count += 1

            # Persist to RewardLedger
            if eval_res.rule:
                ledger_entry = RewardLedger(
                    user_id=user_id,
                    card_id=txn.card_id,
                    transaction_id=txn.id,
                    rule_id=eval_res.rule.id,
                    cap_id=primary_cap.id if primary_cap else None,
                    status=status,
                    reward_type=program.reward_type,
                    calculated_rate=Decimal(f"{eval_res.effective_rate_percent / 100:.6f}"),
                    base_amount=txn.amount,
                    reward_amount=eval_res.net_reward,
                    inr_value=eval_res.inr_value,
                    period_key=period_key,
                    notes=eval_res.explanation,
                )
                db.add(ledger_entry)

            items.append(
                RewardReconciliationItem(
                    transaction_id=txn.id,
                    card_id=txn.card_id,
                    card_name=card_name,
                    transaction_date=txn.transaction_date,
                    description=txn.cleaned_description,
                    merchant_name=txn.merchant_name,
                    category=txn.category,
                    amount=txn.amount,
                    txn_type="debit",
                    rule_name=eval_res.rule.rule_name if eval_res.rule else "No Match",
                    rate_percent=eval_res.effective_rate_percent,
                    reward_amount=eval_res.net_reward,
                    inr_value=eval_res.inr_value,
                    status=status,
                    is_discrepancy=is_discrepancy,
                    discrepancy_reason=discrepancy_reason,
                    period_key=period_key,
                    notes=eval_res.explanation,
                )
            )

        await db.commit()

        return RewardReconciliationSummary(
            total_transactions=len(items),
            total_spend=total_spend,
            total_rewards_inr=total_rewards_inr,
            total_excluded_spend=total_excluded_spend,
            total_capped_lost_inr=total_capped_lost_inr,
            discrepancy_count=discrepancy_count,
            items=items,
        )

    @classmethod
    async def get_reconciliation_report(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        card_id: uuid.UUID | None = None,
        statement_id: uuid.UUID | None = None,
    ) -> RewardReconciliationSummary:
        """Fetch current reconciliation status, automatically reconciling if never processed."""
        # Check if any transactions exist for this filter
        q = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        if statement_id:
            q = q.where(Transaction.statement_id == statement_id)
        if card_id:
            q = q.where(Transaction.card_id == card_id)

        count = (await db.execute(q)).scalar_one()
        if count == 0:
            return RewardReconciliationSummary(
                total_transactions=0,
                total_spend=Decimal("0.0000"),
                total_rewards_inr=Decimal("0.0000"),
                total_excluded_spend=Decimal("0.0000"),
                total_capped_lost_inr=Decimal("0.0000"),
                discrepancy_count=0,
                items=[],
            )

        # Run reconciliation (force_recalculate=False will reuse existing ledgers)
        return await cls.reconcile(
            db=db,
            user_id=user_id,
            card_id=card_id,
            statement_id=statement_id,
            force_recalculate=False,
        )
