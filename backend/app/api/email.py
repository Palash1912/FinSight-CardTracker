"""Email integration & Gmail statement discovery API router — /api/v1/email."""

from __future__ import annotations

import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, DbSession
from app.models.email import EmailConnection, EmailImport
from app.schemas.email import (
    EmailConnectionRead,
    EmailImportRead,
    GmailAuthUrlResponse,
    GmailCallbackRequest,
    GmailSyncRequest,
    GmailSyncResponse,
)
from app.services.gmail_service import GMAIL_SCOPES, GmailService
from app.services.token_encryption import encrypt_token

router = APIRouter(prefix="/email")


@router.get("/connections", response_model=list[EmailConnectionRead])
async def list_connections(
    user: CurrentUser,
    db: DbSession,
) -> list[EmailConnectionRead]:
    """List connected email accounts for statement discovery."""
    stmt = (
        select(EmailConnection)
        .where(EmailConnection.user_id == user.id)
        .order_by(EmailConnection.created_at.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/auth-url", response_model=GmailAuthUrlResponse)
async def get_auth_url(
    user: CurrentUser,
) -> GmailAuthUrlResponse:
    """Generate Google OAuth authorization URL requesting read-only Gmail access."""
    state = secrets.token_urlsafe(16)
    url = GmailService.build_auth_url(state)
    return GmailAuthUrlResponse(auth_url=url, state=state)


@router.post("/callback", response_model=EmailConnectionRead, status_code=status.HTTP_201_CREATED)
async def handle_oauth_callback(
    user: CurrentUser,
    db: DbSession,
    body: GmailCallbackRequest,
) -> EmailConnectionRead:
    """Exchange OAuth code for tokens and store encrypted connection credentials."""
    try:
        tokens = await GmailService.exchange_code(body.code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authorization failed: {exc}",
        ) from exc

    email_address = tokens.get("email", user.email)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # Check if connection already exists for this email
    stmt = select(EmailConnection).where(
        EmailConnection.user_id == user.id,
        EmailConnection.email_address == email_address,
    )
    connection = (await db.execute(stmt)).scalar_one_or_none()

    if not connection:
        connection = EmailConnection(
            user_id=user.id,
            email_address=email_address,
            provider="gmail",
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(refresh_token),
            scopes=GMAIL_SCOPES,
            sync_status="idle",
        )
        db.add(connection)
    else:
        connection.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            connection.encrypted_refresh_token = encrypt_token(refresh_token)
        connection.sync_status = "idle"
        connection.error_message = None

    await db.commit()
    await db.refresh(connection)
    return connection


@router.post("/sync", response_model=GmailSyncResponse)
async def sync_statements(
    user: CurrentUser,
    db: DbSession,
    body: GmailSyncRequest,
) -> GmailSyncResponse:
    """Trigger on-demand statement email discovery and ingestion."""
    if body.connection_id:
        stmt = select(EmailConnection).where(
            EmailConnection.id == body.connection_id,
            EmailConnection.user_id == user.id,
        )
        connection = (await db.execute(stmt)).scalar_one_or_none()
    else:
        stmt = (
            select(EmailConnection)
            .where(EmailConnection.user_id == user.id)
            .order_by(EmailConnection.created_at.desc())
        )
        connection = (await db.execute(stmt)).scalars().first()

    if not connection:
        # Create a default local connection if none exists
        connection = EmailConnection(
            user_id=user.id,
            email_address=user.email,
            provider="gmail",
            encrypted_access_token=encrypt_token(f"mock_token_{uuid.uuid4().hex}"),
            scopes=GMAIL_SCOPES,
            sync_status="idle",
        )
        db.add(connection)
        await db.commit()
        await db.refresh(connection)

    return await GmailService.sync_statements(db, connection, days_back=body.days_back)


@router.delete("/connections/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    user: CurrentUser,
    db: DbSession,
    id: uuid.UUID,
) -> None:
    """Disconnect email provider and revoke stored tokens."""
    stmt = select(EmailConnection).where(
        EmailConnection.id == id,
        EmailConnection.user_id == user.id,
    )
    conn = (await db.execute(stmt)).scalar_one_or_none()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email connection not found.",
        )
    await db.delete(conn)
    await db.commit()


@router.get("/imports", response_model=list[EmailImportRead])
async def list_email_imports(
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[EmailImportRead]:
    """Retrieve audit history of discovered statement emails and status."""
    stmt = (
        select(EmailImport)
        .where(EmailImport.user_id == user.id)
        .order_by(EmailImport.received_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
