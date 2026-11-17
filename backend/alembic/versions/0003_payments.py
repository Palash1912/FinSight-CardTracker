"""Create payments table.

Revision ID: 0003_payments
Revises: 0002_statements_and_transactions
Create Date: 2026-11-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_payments"
down_revision: str | None = "0002_statements_and_transactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column(
            "payment_method",
            sa.String(length=50),
            server_default="net_banking",
            nullable=False,
        ),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="completed",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)
    op.create_index(op.f("ix_payments_card_id"), "payments", ["card_id"], unique=False)
    op.create_index(
        op.f("ix_payments_statement_id"), "payments", ["statement_id"], unique=False
    )
    op.create_index(
        op.f("ix_payments_payment_date"), "payments", ["payment_date"], unique=False
    )
    op.create_index(op.f("ix_payments_status"), "payments", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_status"), table_name="payments")
    op.drop_index(op.f("ix_payments_payment_date"), table_name="payments")
    op.drop_index(op.f("ix_payments_statement_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_card_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_table("payments")
