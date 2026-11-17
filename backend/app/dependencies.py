"""FastAPI dependency shortcuts — import from here in route modules."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User

# Annotated type aliases for Depends injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentSettings = Annotated[Settings, Depends(get_settings)]


async def get_current_user(db: DbSession, settings: CurrentSettings) -> User:
    """Return the owner of all data in single-local-user mode.

    Creates the account on first use. Replace with real authentication later
    without changing the rest of the codebase.
    """
    result = await db.execute(select(User).where(User.email == settings.local_user_email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=settings.local_user_email, display_name="Local owner", is_active=True)
        db.add(user)
        await db.flush()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

__all__ = ["DbSession", "CurrentSettings", "CurrentUser", "get_db", "get_settings"]
