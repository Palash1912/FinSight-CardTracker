"""Create users and credit_cards tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-13

Written by hand to match app/models (no running database was available for
autogenerate). Verify with: alembic upgrade head --sql
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "credit_cards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("issuer", sa.String(length=100), nullable=False),
        sa.Column("card_name", sa.String(length=150), nullable=False),
        sa.Column("network", sa.String(length=20), nullable=False),
        sa.Column("last_four_digits", sa.String(length=4), nullable=False),
        sa.Column("billing_cycle_day", sa.Integer(), nullable=False),
        sa.Column("payment_due_days", sa.Integer(), nullable=False),
        sa.Column("credit_limit", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column(
            "current_balance",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "annual_fee",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_credit_cards_user_id"), "credit_cards", ["user_id"], unique=False)
    op.create_index(op.f("ix_credit_cards_status"), "credit_cards", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_credit_cards_status"), table_name="credit_cards")
    op.drop_index(op.f("ix_credit_cards_user_id"), table_name="credit_cards")
    op.drop_table("credit_cards")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
