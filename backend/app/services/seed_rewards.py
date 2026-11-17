"""Seed realistic reward rules and programs for credit cards."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import CreditCard
from app.models.reward import RewardCap, RewardProgram, RewardRule


async def seed_user_reward_programs(
    db: AsyncSession,
    user_id: uuid.UUID,
    override_existing: bool = False,
) -> int:
    """Populates realistic synthetic rules for all active cards belonging to user.

    Returns the count of seeded programs.
    """
    card_stmt = select(CreditCard).where(CreditCard.user_id == user_id, CreditCard.status == "active")
    card_res = await db.execute(card_stmt)
    cards = list(card_res.scalars().all())

    seeded_count = 0
    today = date(2025, 1, 1)

    for card in cards:
        # Check if already has program
        p_stmt = select(RewardProgram).where(
            RewardProgram.card_id == card.id, RewardProgram.user_id == user_id
        )
        existing_p = (await db.execute(p_stmt)).scalar_one_or_none()

        if existing_p:
            if not override_existing:
                continue
            # Delete existing
            await db.delete(existing_p)
            await db.flush()

        c_name = card.card_name.lower()
        issuer = card.issuer.lower()

        if "amazon" in c_name or ("icici" in issuer and "amazon" in c_name):
            prog = RewardProgram(
                user_id=user_id,
                card_id=card.id,
                program_name="Amazon Pay ICICI Cashback",
                reward_type="cashback",
                reward_currency="INR",
                point_value_inr=Decimal("1.0"),
            )
            db.add(prog)
            await db.flush()

            # Rule 1: 5% on Amazon
            r1 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="5% on Amazon Shopping",
                rule_type="merchant_accelerator",
                reward_rate=Decimal("0.0500"),
                merchant_pattern=r"amazon",
                exclusions=["Fuel", "Rent", "Wallet Reload", "Government"],
                effective_from=today,
                confidence_notes="Verified via Amazon Pay ICICI cardmember agreement (Prime members 5%, non-Prime 3%).",
            )
            # Rule 2: 2% on Bill Payments
            r2 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="2% on Bill Payments & Flight Bookings",
                rule_type="category_accelerator",
                category="Bills & Utilities",
                reward_rate=Decimal("0.0200"),
                exclusions=["Fuel"],
                effective_from=today,
                confidence_notes="Applicable on Amazon Pay bill payments and recharges.",
            )
            # Rule 3: 1% Base
            r3 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="1% Unlimited on All Other Spends",
                rule_type="base",
                reward_rate=Decimal("0.0100"),
                exclusions=["Fuel", "Rent", "Wallet Reload"],
                effective_from=today,
                confidence_notes="Unlimited 1% automatic statement credit cashback.",
            )
            db.add_all([r1, r2, r3])
            seeded_count += 1

        elif "millennia" in c_name or ("hdfc" in issuer and "millennia" in c_name):
            prog = RewardProgram(
                user_id=user_id,
                card_id=card.id,
                program_name="HDFC Millennia CashPoints",
                reward_type="cashback",
                reward_currency="INR",
                point_value_inr=Decimal("1.0"),
            )
            db.add(prog)
            await db.flush()

            # Rule 1: 5% Partner Merchants with ₹1000/mo cap
            r1 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="5% on Partner Merchants (Amazon, Flipkart, Swiggy, Zomato, Uber)",
                rule_type="merchant_accelerator",
                reward_rate=Decimal("0.0500"),
                merchant_pattern=r"(amazon|flipkart|swiggy|zomato|uber|myntra|tata cliq|cult\.fit|sony liv|bookmyshow)",
                exclusions=["Fuel", "Rent", "Wallet", "Government", "Jewellery"],
                effective_from=today,
                confidence_notes="Subject to ₹1,000 monthly calendar cap across partner merchants.",
            )
            db.add(r1)
            await db.flush()

            c1 = RewardCap(
                rule_id=r1.id,
                cap_name="Millennia 5% Monthly Partner Cap",
                cap_period="monthly",
                reset_basis="calendar_month",
                cap_amount=Decimal("1000.00"),
            )
            db.add(c1)

            # Rule 2: 1% on other spends with ₹1000/mo cap
            r2 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="1% on Other Spends",
                rule_type="base",
                reward_rate=Decimal("0.0100"),
                exclusions=["Fuel", "Rent", "Wallet Reload"],
                effective_from=today,
            )
            db.add(r2)
            await db.flush()

            c2 = RewardCap(
                rule_id=r2.id,
                cap_name="Millennia 1% Monthly Base Cap",
                cap_period="monthly",
                reset_basis="calendar_month",
                cap_amount=Decimal("1000.00"),
            )
            db.add(c2)
            seeded_count += 1

        elif "hsbc" in issuer or "cashback" in c_name:
            prog = RewardProgram(
                user_id=user_id,
                card_id=card.id,
                program_name="HSBC Live+ / Cashback Rewards",
                reward_type="cashback",
                reward_currency="INR",
                point_value_inr=Decimal("1.0"),
            )
            db.add(prog)
            await db.flush()

            # 10% on Dining & Food
            r1 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="10% on Dining, Food Delivery & Grocery",
                rule_type="category_accelerator",
                category="Food & Dining",
                reward_rate=Decimal("0.1000"),
                exclusions=["Fuel", "Wallet"],
                effective_from=today,
                confidence_notes="Cap of ₹1,000 per billing cycle across accelerated categories.",
            )
            db.add(r1)
            await db.flush()

            c1 = RewardCap(
                rule_id=r1.id,
                cap_name="HSBC 10% Dining Billing Cycle Cap",
                cap_period="billing_cycle",
                reset_basis="statement_cycle",
                cap_amount=Decimal("1000.00"),
            )
            db.add(c1)

            # 1.5% Base
            r2 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="1.5% Unlimited Cashback on Other Spends",
                rule_type="base",
                reward_rate=Decimal("0.0150"),
                exclusions=["Fuel", "Rent", "Wallet"],
                effective_from=today,
            )
            db.add(r2)
            seeded_count += 1

        elif "flipkart" in c_name or ("axis" in issuer and "flipkart" in c_name):
            prog = RewardProgram(
                user_id=user_id,
                card_id=card.id,
                program_name="Flipkart Axis Cashback",
                reward_type="cashback",
                reward_currency="INR",
                point_value_inr=Decimal("1.0"),
            )
            db.add(prog)
            await db.flush()

            r1 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="5% on Flipkart & Cleartrip",
                rule_type="merchant_accelerator",
                reward_rate=Decimal("0.0500"),
                merchant_pattern=r"(flipkart|cleartrip)",
                exclusions=["Fuel", "Rent", "Wallet Reload"],
                effective_from=today,
            )
            r2 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="4% on Preferred Partners (Swiggy, Uber, PVR)",
                rule_type="merchant_accelerator",
                reward_rate=Decimal("0.0400"),
                merchant_pattern=r"(swiggy|uber|pvr|cult\.fit)",
                exclusions=["Fuel", "Rent", "Wallet Reload"],
                effective_from=today,
            )
            r3 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="1.5% Unlimited on Other Spends",
                rule_type="base",
                reward_rate=Decimal("0.0150"),
                exclusions=["Fuel", "Rent", "Wallet Reload"],
                effective_from=today,
            )
            db.add_all([r1, r2, r3])
            seeded_count += 1

        else:
            # Generic 2 reward points per ₹100 (0.5% effective)
            prog = RewardProgram(
                user_id=user_id,
                card_id=card.id,
                program_name=f"{card.card_name} Rewards",
                reward_type="reward_points",
                reward_currency="Points",
                point_value_inr=Decimal("0.2500"),
            )
            db.add(prog)
            await db.flush()

            r1 = RewardRule(
                user_id=user_id,
                program_id=prog.id,
                rule_name="Standard Reward Points (2 pts per ₹100)",
                rule_type="base",
                reward_rate=Decimal("0.0200"),
                exclusions=["Fuel", "Cash Withdrawal"],
                effective_from=today,
                confidence_notes="Generic issuer reward program fixture (1 pt = ₹0.25).",
            )
            db.add(r1)
            seeded_count += 1

    await db.commit()
    return seeded_count
