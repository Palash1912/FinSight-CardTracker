"""Unit tests for Rewards Intelligence, RewardEngine, CapTracker, and Schemas."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.models.card import CreditCard
from app.models.reward import RewardCap, RewardProgram, RewardRule
from app.schemas.reward import (
    CardRecommendationItem,
    CardRecommendationRequest,
    CardRecommendationResponse,
)
from app.services.cap_tracker import get_next_reset_date, get_period_key
from app.services.reward_engine import RewardEngine


def _make_dummy_card() -> CreditCard:
    return CreditCard(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        issuer="HDFC Bank",
        card_name="Millennia",
        network="visa",
        last_four_digits="4321",
        billing_cycle_day=15,
        payment_due_days=20,
        credit_limit=Decimal("200000.00"),
    )


def test_cap_tracker_period_keys() -> None:
    ref = date(2026, 10, 20)
    # Calendar month
    assert get_period_key("calendar_month", ref) == "2026-10"
    # Calendar quarter
    assert get_period_key("calendar_quarter", ref) == "2026-Q4"
    # Calendar year
    assert get_period_key("calendar_year", ref) == "2026"
    # Statement cycle
    assert get_period_key("statement_cycle", ref, billing_cycle_day=15) == "2026-10-c15"
    early_ref = date(2026, 10, 10)
    assert get_period_key("statement_cycle", early_ref, billing_cycle_day=15) == "2026-09-c15"


def test_cap_tracker_next_reset_date() -> None:
    ref = date(2026, 10, 20)
    # Next month
    assert get_next_reset_date("calendar_month", ref) == date(2026, 11, 1)
    # Next quarter
    assert get_next_reset_date("calendar_quarter", ref) == date(2027, 1, 1)
    # Next cycle
    assert get_next_reset_date("statement_cycle", ref, billing_cycle_day=15) == date(2026, 11, 15)
    early_ref = date(2026, 10, 5)
    assert get_next_reset_date("statement_cycle", early_ref, billing_cycle_day=15) == date(2026, 10, 15)


def test_reward_engine_merchant_accelerator() -> None:
    card = _make_dummy_card()
    program = RewardProgram(
        id=uuid.uuid4(),
        user_id=card.user_id,
        card_id=card.id,
        program_name="CashPoints",
        reward_type="cashback",
        point_value_inr=Decimal("1.0"),
    )
    rule_accel = RewardRule(
        id=uuid.uuid4(),
        user_id=card.user_id,
        program_id=program.id,
        rule_name="5% on Amazon",
        rule_type="merchant_accelerator",
        reward_rate=Decimal("0.05"),
        merchant_pattern=r"amazon",
        effective_from=date(2025, 1, 1),
    )
    rule_base = RewardRule(
        id=uuid.uuid4(),
        user_id=card.user_id,
        program_id=program.id,
        rule_name="1% Base",
        rule_type="base",
        reward_rate=Decimal("0.01"),
        effective_from=date(2025, 1, 1),
    )

    # Spend on Amazon
    res = RewardEngine.evaluate_card(
        card=card,
        program=program,
        rules=[rule_accel, rule_base],
        amount=Decimal("10000.00"),
        merchant="Amazon India",
        category="Shopping",
        channel="online",
        purchase_date=date(2026, 10, 20),
        consumed_caps_map={},
    )
    assert res.eligible is True
    assert res.effective_rate_percent == 5.0
    assert res.net_reward == Decimal("500.00")
    assert res.inr_value == Decimal("500.00")
    assert res.rule.rule_name == "5% on Amazon"


def test_reward_engine_exclusions() -> None:
    card = _make_dummy_card()
    program = RewardProgram(
        id=uuid.uuid4(),
        user_id=card.user_id,
        card_id=card.id,
        program_name="Cashback",
        reward_type="cashback",
        point_value_inr=Decimal("1.0"),
    )
    rule = RewardRule(
        id=uuid.uuid4(),
        user_id=card.user_id,
        program_id=program.id,
        rule_name="1.5% Base",
        rule_type="base",
        reward_rate=Decimal("0.015"),
        exclusions=["Fuel", "Rent", "Wallet"],
        effective_from=date(2025, 1, 1),
    )

    # Spend on HPCL Fuel
    res = RewardEngine.evaluate_card(
        card=card,
        program=program,
        rules=[rule],
        amount=Decimal("3000.00"),
        merchant="HPCL Fuel Pump",
        category="Fuel",
        channel="offline",
        purchase_date=date(2026, 10, 20),
        consumed_caps_map={},
    )
    assert res.eligible is False
    assert res.net_reward == Decimal("0")
    assert "excluded" in res.explanation.lower()


def test_reward_engine_cap_exhaustion() -> None:
    card = _make_dummy_card()
    program = RewardProgram(
        id=uuid.uuid4(),
        user_id=card.user_id,
        card_id=card.id,
        program_name="CashPoints",
        reward_type="cashback",
        point_value_inr=Decimal("1.0"),
    )
    rule_id = uuid.uuid4()
    cap = RewardCap(
        id=uuid.uuid4(),
        rule_id=rule_id,
        cap_name="Monthly Partner Cap",
        cap_period="monthly",
        reset_basis="calendar_month",
        cap_amount=Decimal("1000.00"),
    )
    rule = RewardRule(
        id=rule_id,
        user_id=card.user_id,
        program_id=program.id,
        rule_name="5% on Swiggy",
        rule_type="merchant_accelerator",
        reward_rate=Decimal("0.05"),
        merchant_pattern=r"swiggy",
        effective_from=date(2025, 1, 1),
        caps=[cap],
    )

    # Suppose user already consumed ₹800 of the ₹1000 cap
    consumed = {rule_id: Decimal("800.00")}

    # Spend ₹10,000 -> 5% would normally be ₹500, but only ₹200 cap left!
    res = RewardEngine.evaluate_card(
        card=card,
        program=program,
        rules=[rule],
        amount=Decimal("10000.00"),
        merchant="Swiggy Delivery",
        category="Food & Dining",
        channel="online",
        purchase_date=date(2026, 10, 20),
        consumed_caps_map=consumed,
    )
    assert res.eligible is True
    assert res.gross_reward == Decimal("500.00")
    assert res.net_reward == Decimal("200.00")  # Capped at remaining cap!
    assert res.remaining_cap_before == Decimal("200.00")
    assert res.remaining_cap_after == Decimal("0.00")
    assert "Capped: ₹200.00 remaining" in res.explanation


def test_reconciliation_schemas() -> None:
    from app.schemas.reward import (
        RewardReconcileRequest,
        RewardReconciliationItem,
        RewardReconciliationSummary,
    )

    req = RewardReconcileRequest(force_recalculate=True)
    assert req.force_recalculate is True
    assert req.card_id is None

    item = RewardReconciliationItem(
        transaction_id=uuid.uuid4(),
        card_id=uuid.uuid4(),
        card_name="Millennia",
        transaction_date=date(2026, 10, 20),
        description="SWIGGY BANGALORE",
        merchant_name="Swiggy",
        category="Food & Dining",
        amount=Decimal("1200.00"),
        txn_type="debit",
        rule_name="5% on Swiggy",
        rate_percent=5.0,
        reward_amount=Decimal("60.00"),
        inr_value=Decimal("60.00"),
        status="confirmed",
        is_discrepancy=False,
        discrepancy_reason=None,
        period_key="2026-10",
        notes="Accelerated reward applied.",
    )
    assert item.rate_percent == 5.0
    assert item.reward_amount == Decimal("60.00")

    summary = RewardReconciliationSummary(
        total_transactions=1,
        total_spend=Decimal("1200.00"),
        total_rewards_inr=Decimal("60.00"),
        total_excluded_spend=Decimal("0.00"),
        total_capped_lost_inr=Decimal("0.00"),
        discrepancy_count=0,
        items=[item],
    )
    assert summary.total_transactions == 1
    assert summary.total_rewards_inr == Decimal("60.00")

