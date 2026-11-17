"""Declarative base and shared mixins for all SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        default=None,
        onupdate=func.now(),
        server_onupdate=None,
    )


def uuid_pk() -> Mapped[uuid.UUID]:
    """Return a mapped_column configured as a UUID primary key."""
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
