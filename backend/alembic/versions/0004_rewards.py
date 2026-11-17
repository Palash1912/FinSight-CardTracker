"""Create reward programs, rules, caps, and ledger tables.

Revision ID: 0004_rewards
Revises: 0003_payments
Create Date: 2026-11-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_rewards"
down_revision: str | None = "0003_payments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. reward_programs
    op.create_table(
        "reward_programs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("program_name", sa.String(length=150), nullable=False),
        sa.Column("reward_type", sa.String(length=30), server_default="cashback", nullable=False),
        sa.Column("reward_currency", sa.String(length=20), server_default="INR", nullable=False),
        sa.Column("point_value_inr", sa.Numeric(precision=18, scale=4), server_default="1.0", nullable=False),
        sa.Column("expiry_months", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reward_programs_user_id"), "reward_programs", ["user_id"], unique=False)
    op.create_index(op.f("ix_reward_programs_card_id"), "reward_programs", ["card_id"], unique=False)

    # 2. reward_rules
    op.create_table(
        "reward_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("rule_name", sa.String(length=150), nullable=False),
        sa.Column("rule_type", sa.String(length=30), server_default="base", nullable=False),
        sa.Column("reward_rate", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("reward_rate_type", sa.String(length=20), server_default="percentage", nullable=False),
        sa.Column("min_transaction_amount", sa.Numeric(precision=18, scale=4), server_default="0", nullable=False),
        sa.Column("max_eligible_amount", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("merchant_pattern", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=20), server_default="any", nullable=True),
        sa.Column("exclusions", sa.JSON(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("last_verified_at", sa.Date(), nullable=True),
        sa.Column("verification_status", sa.String(length=30), server_default="verified", nullable=False),
        sa.Column("confidence_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["reward_programs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reward_rules_user_id"), "reward_rules", ["user_id"], unique=False)
    op.create_index(op.f("ix_reward_rules_program_id"), "reward_rules", ["program_id"], unique=False)
    op.create_index(op.f("ix_reward_rules_category"), "reward_rules", ["category"], unique=False)
    op.create_index(op.f("ix_reward_rules_merchant_pattern"), "reward_rules", ["merchant_pattern"], unique=False)

    # 3. reward_caps
    op.create_table(
        "reward_caps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("cap_name", sa.String(length=150), nullable=False),
        sa.Column("cap_period", sa.String(length=20), server_default="monthly", nullable=False),
        sa.Column("reset_basis", sa.String(length=30), server_default="calendar_month", nullable=False),
        sa.Column("cap_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("cap_currency", sa.String(length=20), server_default="INR", nullable=False),
        sa.Column("pending_consumes_cap", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("refunds_reverse_cap", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["rule_id"], ["reward_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reward_caps_rule_id"), "reward_caps", ["rule_id"], unique=False)

    # 4. reward_ledger
    op.create_table(
        "reward_ledger",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("cap_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="confirmed", nullable=False),
        sa.Column("reward_type", sa.String(length=30), server_default="cashback", nullable=False),
        sa.Column("calculated_rate", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("base_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("reward_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("inr_value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("period_key", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cap_id"], ["reward_caps.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rule_id"], ["reward_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reward_ledger_user_id"), "reward_ledger", ["user_id"], unique=False)
    op.create_index(op.f("ix_reward_ledger_card_id"), "reward_ledger", ["card_id"], unique=False)
    op.create_index(op.f("ix_reward_ledger_rule_id"), "reward_ledger", ["rule_id"], unique=False)
    op.create_index(op.f("ix_reward_ledger_period_key"), "reward_ledger", ["period_key"], unique=False)
    op.create_index(op.f("ix_reward_ledger_status"), "reward_ledger", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("reward_ledger")
    op.drop_table("reward_caps")
    op.drop_table("reward_rules")
    op.drop_table("reward_programs")
