"""Create email_connections and email_imports tables for Phase 7.

Revision ID: 0005_email_imports
Revises: 0004_rewards
Create Date: 2026-11-17

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_email_imports"
down_revision: str | None = "0004_rewards"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. email_connections
    op.create_table(
        "email_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=50), server_default="gmail", nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=True),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.Column("sync_status", sa.String(length=30), server_default="idle", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_connections_user_id"), "email_connections", ["user_id"], unique=False)
    op.create_index(op.f("ix_email_connections_sync_status"), "email_connections", ["sync_status"], unique=False)

    # 2. email_imports
    op.create_table(
        "email_imports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=True),
        sa.Column("card_id", sa.Uuid(), nullable=True),
        sa.Column("message_id", sa.String(length=100), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=True),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("attachment_name", sa.String(length=255), nullable=False),
        sa.Column("attachment_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="discovered", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["connection_id"], ["email_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["card_id"], ["credit_cards.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_imports_user_id"), "email_imports", ["user_id"], unique=False)
    op.create_index(op.f("ix_email_imports_connection_id"), "email_imports", ["connection_id"], unique=False)
    op.create_index(op.f("ix_email_imports_statement_id"), "email_imports", ["statement_id"], unique=False)
    op.create_index(op.f("ix_email_imports_card_id"), "email_imports", ["card_id"], unique=False)
    op.create_index(op.f("ix_email_imports_message_id"), "email_imports", ["message_id"], unique=False)
    op.create_index(op.f("ix_email_imports_received_at"), "email_imports", ["received_at"], unique=False)
    op.create_index(op.f("ix_email_imports_attachment_sha256"), "email_imports", ["attachment_sha256"], unique=False)
    op.create_index(op.f("ix_email_imports_status"), "email_imports", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("email_imports")
    op.drop_table("email_connections")
