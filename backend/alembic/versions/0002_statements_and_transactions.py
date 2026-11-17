"""Create statements and transactions tables.

Revision ID: 0002_statements_and_transactions
Revises: 0001_initial
Create Date: 2026-11-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_statements_and_transactions"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create statements table
    op.create_table(
        "statements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("statement_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column(
            "total_amount_due",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "minimum_amount_due",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "opening_balance",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "closing_balance",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "total_credits",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "total_debits",
            sa.Numeric(precision=18, scale=4),
            server_default="0",
            nullable=False,
        ),
        sa.Column("file_hash_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("parser_used", sa.String(length=50), server_default="generic", nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending_review",
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_statements_user_id"), "statements", ["user_id"], unique=False)
    op.create_index(op.f("ix_statements_card_id"), "statements", ["card_id"], unique=False)
    op.create_index(
        op.f("ix_statements_file_hash_sha256"), "statements", ["file_hash_sha256"], unique=False
    )
    op.create_index(op.f("ix_statements_status"), "statements", ["status"], unique=False)

    # 2. Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("posting_date", sa.Date(), nullable=True),
        sa.Column("original_description", sa.String(length=500), nullable=False),
        sa.Column("cleaned_description", sa.String(length=500), nullable=False),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column(
            "category",
            sa.String(length=100),
            server_default="Uncategorized",
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("txn_type", sa.String(length=10), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "source",
            sa.String(length=20),
            server_default="pdf_statement",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="posted",
            nullable=False,
        ),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_row", sa.Integer(), nullable=True),
        sa.Column("original_values", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["credit_cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_transactions_card_id"), "transactions", ["card_id"], unique=False)
    op.create_index(
        op.f("ix_transactions_statement_id"), "transactions", ["statement_id"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_transaction_date"), "transactions", ["transaction_date"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_merchant_name"), "transactions", ["merchant_name"], unique=False
    )
    op.create_index(op.f("ix_transactions_category"), "transactions", ["category"], unique=False)
    op.create_index(
        op.f("ix_transactions_fingerprint"), "transactions", ["fingerprint"], unique=False
    )
    op.create_index(op.f("ix_transactions_status"), "transactions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_status"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_fingerprint"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_merchant_name"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_transaction_date"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_statement_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_card_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_index(op.f("ix_statements_status"), table_name="statements")
    op.drop_index(op.f("ix_statements_file_hash_sha256"), table_name="statements")
    op.drop_index(op.f("ix_statements_card_id"), table_name="statements")
    op.drop_index(op.f("ix_statements_user_id"), table_name="statements")
    op.drop_table("statements")
