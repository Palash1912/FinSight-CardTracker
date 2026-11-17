"""Deterministic reward calculator and rule matching engine."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.card import CreditCard
from app.models.reward import RewardCap, RewardProgram, RewardRule
from app.services.cap_tracker import get_next_reset_date, get_period_key


@dataclass
class RuleEvaluationResult:
    """Outcome of evaluating a purchase against a card's reward rules."""

    card: CreditCard
    program: RewardProgram
    rule: RewardRule
    eligible: bool
    effective_rate_percent: float
    gross_reward: Decimal
    net_reward: Decimal
    inr_value: Decimal
    remaining_cap_before: Decimal | None
    remaining_cap_after: Decimal | None
    cap_period: str | None
    explanation: str
    confidence_notes: str | None


class RewardEngine:
    """Evaluates transactions and planned purchases against versioned, effective-dated rules."""

    @staticmethod
    def _is_rule_active(rule: RewardRule, as_of: date) -> bool:
        if rule.effective_from > as_of:
            return False
        if rule.effective_to and rule.effective_to < as_of:
            return False
        return True

    @staticmethod
    def _is_excluded(rule: RewardRule, merchant: str, category: str) -> bool:
        if not rule.exclusions:
            return False
        m_lower = merchant.lower()
        c_lower = category.lower()
        for excl in rule.exclusions:
            e_lower = excl.lower()
            if e_lower in m_lower or e_lower in c_lower:
                return True
        return False

    @classmethod
    def evaluate_card(
        cls,
        card: CreditCard,
        program: RewardProgram,
        rules: list[RewardRule],
        amount: Decimal,
        merchant: str,
        category: str,
        channel: str,
        purchase_date: date,
        consumed_caps_map: dict[uuid.UUID, Decimal],  # rule_id -> consumed
    ) -> RuleEvaluationResult:
        """Evaluate a purchase against a card's rules, find best matching rate, and apply caps."""
        # 1. Filter active rules
        active_rules = [r for r in rules if cls._is_rule_active(r, purchase_date)]

        if not active_rules:
            # Fallback 0% if no rules configured
            return RuleEvaluationResult(
                card=card,
                program=program,
                rule=None,  # type: ignore[arg-type]
                eligible=False,
                effective_rate_percent=0.0,
                gross_reward=Decimal("0"),
                net_reward=Decimal("0"),
                inr_value=Decimal("0"),
                remaining_cap_before=None,
                remaining_cap_after=None,
                cap_period=None,
                explanation="No active reward terms configured for this card.",
                confidence_notes=None,
            )

        # 2. Score and select the best applicable rule
        eligible_matches: list[tuple[RewardRule, str]] = []

        m_clean = merchant.strip().lower()
        c_clean = category.strip().lower()

        for r in active_rules:
            # Check exclusions (e.g. Fuel, Rent, Wallet load)
            if cls._is_excluded(r, m_clean, c_clean):
                continue

            # Check min transaction amount
            if amount < r.min_transaction_amount:
                continue

            # Check channel
            if r.channel and r.channel != "any" and r.channel != channel:
                continue

            # Check Merchant Accelerator
            if r.rule_type == "merchant_accelerator" and r.merchant_pattern:
                if re.search(r.merchant_pattern, merchant, re.IGNORECASE):
                    eligible_matches.append(
                        (r, f"Special accelerator for {merchant} ({float(r.reward_rate * 100):.1f}%)")
                    )
                    continue

            # Check Category Accelerator
            if r.rule_type == "category_accelerator" and r.category:
                if r.category.lower() == c_clean:
                    eligible_matches.append(
                        (r, f"Accelerated category reward for {r.category} ({float(r.reward_rate * 100):.1f}%)")
                    )
                    continue

            # Base rule
            if r.rule_type == "base":
                eligible_matches.append(
                    (r, f"Base reward rate ({float(r.reward_rate * 100):.1f}%)")
                )

        if not eligible_matches:
            # All rules excluded or conditions not met
            return RuleEvaluationResult(
                card=card,
                program=program,
                rule=active_rules[0],
                eligible=False,
                effective_rate_percent=0.0,
                gross_reward=Decimal("0"),
                net_reward=Decimal("0"),
                inr_value=Decimal("0"),
                remaining_cap_before=None,
                remaining_cap_after=None,
                cap_period=None,
                explanation=f"Purchase category '{category}' or merchant '{merchant}' is excluded from rewards.",
                confidence_notes=None,
            )

        # Pick the rule offering highest reward rate
        eligible_matches.sort(key=lambda item: item[0].reward_rate, reverse=True)
        best_rule, reason = eligible_matches[0]

        # 3. Calculate gross reward
        eligible_spend = amount
        if best_rule.max_eligible_amount and amount > best_rule.max_eligible_amount:
            eligible_spend = best_rule.max_eligible_amount

        # Theoretical gross reward
        if program.reward_type == "reward_points":
            points = eligible_spend * best_rule.reward_rate
            gross_reward = points
            gross_inr = points * program.point_value_inr
        else:  # cashback
            gross_reward = eligible_spend * best_rule.reward_rate
            gross_inr = gross_reward

        # 4. Check Cap Restrictions
        net_reward = gross_reward
        rem_before: Decimal | None = None
        rem_after: Decimal | None = None
        cap_period_str: str | None = None
        cap_note = ""

        if best_rule.caps:
            cap = best_rule.caps[0]
            cap_period_str = cap.cap_period
            consumed = consumed_caps_map.get(best_rule.id, Decimal("0"))
            rem_before = max(Decimal("0"), cap.cap_amount - consumed)

            if gross_reward > rem_before:
                net_reward = rem_before
                cap_note = f" (Capped: ₹{rem_before:.2f} remaining of ₹{cap.cap_amount:.0f} {cap.cap_period} cap)"
            else:
                cap_note = f" (Consumes ₹{gross_reward:.2f} of ₹{rem_before:.2f} remaining cap)"

            rem_after = max(Decimal("0"), rem_before - net_reward)

        if program.reward_type == "reward_points":
            final_inr = net_reward * program.point_value_inr
        else:
            final_inr = net_reward

        rate_pct = float(best_rule.reward_rate * 100) if best_rule.reward_rate <= 1 else float(best_rule.reward_rate)

        explanation = f"{reason}{cap_note}."

        return RuleEvaluationResult(
            card=card,
            program=program,
            rule=best_rule,
            eligible=True,
            effective_rate_percent=rate_pct,
            gross_reward=gross_reward,
            net_reward=net_reward,
            inr_value=final_inr,
            remaining_cap_before=rem_before,
            remaining_cap_after=rem_after,
            cap_period=cap_period_str,
            explanation=explanation,
            confidence_notes=best_rule.confidence_notes,
        )
