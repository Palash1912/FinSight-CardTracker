"""Gmail OAuth integration and bank statement discovery service (Phase 7)."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.card import CreditCard
from app.models.email import EmailConnection, EmailImport
from app.models.statement import Statement
from app.schemas.email import GmailSyncResponse
from app.services.statement_service import DuplicateStatementError, StatementService
from app.services.token_encryption import decrypt_token, encrypt_token
from app.storage.local import LocalStorageProvider

logger = logging.getLogger(__name__)

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Major Indian card issuers sender domains and patterns
BANK_ISSUER_QUERIES = [
    '(from:(alerts@hdfcbank.net OR statements@hdfcbank.net OR netbanking@hdfcbank.bank) filename:pdf (statement OR "credit card"))',
    '(from:(credit_cards@icicibank.com OR statements@icicibank.com OR donotreply@icicibank.com) filename:pdf (statement OR "e-statement"))',
    '(from:(hsbc@hsbc.co.in OR statement@hsbc.co.in) filename:pdf statement)',
    '(from:(ebpp@axisbank.com OR alerts@axisbank.com) filename:pdf statement)',
    '(from:(sbicard.com OR customer.care@sbicard.com) filename:pdf statement)',
    '(has:attachment filename:pdf ("credit card statement" OR "e-statement" OR "account statement"))',
]


class GmailService:
    """Manages Gmail OAuth token exchange and statement attachment discovery."""

    @classmethod
    def build_auth_url(cls, state: str) -> str:
        """Construct the Google OAuth consent URL requesting read-only access."""
        settings = get_settings()
        params = {
            "client_id": settings.google_client_id or "placeholder_client_id.apps.googleusercontent.com",
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(GMAIL_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_BASE}?{urlencode(params)}"

    @classmethod
    def build_search_query(cls, days_back: int = 90) -> str:
        """Compose search query for bank statement PDF attachments within the date window."""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
        combined_issuers = " OR ".join(BANK_ISSUER_QUERIES)
        return f"({combined_issuers}) after:{cutoff_date}"

    @classmethod
    async def exchange_code(cls, code: str) -> dict[str, Any]:
        """Exchange authorization code for OAuth tokens."""
        settings = get_settings()
        if not settings.google_client_id or not settings.google_client_secret:
            # Simulated exchange for local sandbox testing
            return {
                "access_token": f"mock_access_{uuid.uuid4().hex}",
                "refresh_token": f"mock_refresh_{uuid.uuid4().hex}",
                "expires_in": 3600,
                "email": settings.local_user_email,
            }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # Retrieve user email address
            access_token = data["access_token"]
            profile_resp = await client.get(
                f"{GMAIL_API_BASE}/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            email_addr = settings.local_user_email
            if profile_resp.status_code == 200:
                email_addr = profile_resp.json().get("emailAddress", email_addr)

            data["email"] = email_addr
            return data

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> str:
        """Refresh expired Google OAuth access token."""
        settings = get_settings()
        if not settings.google_client_id or not settings.google_client_secret:
            return f"mock_refreshed_access_{uuid.uuid4().hex}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    @classmethod
    async def sync_statements(
        cls,
        db: AsyncSession,
        connection: EmailConnection,
        days_back: int = 90,
    ) -> GmailSyncResponse:
        """Discover and download statement PDF attachments from connected Gmail account."""
        settings = get_settings()
        connection.sync_status = "syncing"
        connection.error_message = None
        await db.commit()

        plain_access = decrypt_token(connection.encrypted_access_token)
        plain_refresh = decrypt_token(connection.encrypted_refresh_token)

        errors: list[str] = []
        messages_found = 0
        attachments_downloaded = 0
        statements_created = 0
        duplicates_skipped = 0

        # Check if running in mock/demo mode (no live Google credentials)
        is_mock = not settings.google_client_id or (plain_access and plain_access.startswith("mock_"))

        if is_mock:
            # Execute synthetic discovery for local / demonstration environment
            sim_res = await cls._simulate_statement_sync(db, connection)
            connection.sync_status = "idle"
            connection.last_synced_at = datetime.now(timezone.utc)
            await db.commit()
            return sim_res

        # Real Google API discovery
        try:
            # Refresh token if expired
            if connection.token_expiry and connection.token_expiry <= datetime.now(timezone.utc):
                if plain_refresh:
                    plain_access = await cls.refresh_access_token(plain_refresh)
                    connection.encrypted_access_token = encrypt_token(plain_access)
                    connection.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=3600)
                    await db.commit()

            query = cls.build_search_query(days_back)
            storage = LocalStorageProvider(settings.storage_path)
            stmt_service = StatementService(db, storage)

            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {plain_access}"}
                list_url = f"{GMAIL_API_BASE}/messages?q={urlencode({'q': query})[2:]}&maxResults=20"
                resp = await client.get(list_url, headers=headers)
                resp.raise_for_status()
                msg_list = resp.json().get("messages", [])
                messages_found = len(msg_list)

                for msg_ref in msg_list:
                    msg_id = msg_ref["id"]

                    # Check if already processed
                    existing_import = (
                        await db.execute(
                            select(EmailImport).where(
                                EmailImport.connection_id == connection.id,
                                EmailImport.message_id == msg_id,
                            )
                        )
                    ).scalar_one_or_none()

                    if existing_import and existing_import.status in ("ingested", "skipped_duplicate"):
                        continue

                    # Fetch message detail
                    m_resp = await client.get(f"{GMAIL_API_BASE}/messages/{msg_id}", headers=headers)
                    if m_resp.status_code != 200:
                        continue
                    m_data = m_resp.json()

                    payload = m_data.get("payload", {})
                    headers_map = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
                    sender = headers_map.get("from", "Unknown Sender")
                    subject = headers_map.get("subject", "Credit Card Statement")
                    internal_date_ms = int(m_data.get("internalDate", "0"))
                    received_at = (
                        datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)
                        if internal_date_ms
                        else datetime.now(timezone.utc)
                    )

                    # Extract PDF attachment parts
                    parts = payload.get("parts", [payload])
                    for part in parts:
                        filename = part.get("filename", "")
                        body = part.get("body", {})
                        attachment_id = body.get("attachmentId")

                        if not filename.lower().endswith(".pdf") or not attachment_id:
                            continue

                        # Fetch attachment binary
                        att_url = f"{GMAIL_API_BASE}/messages/{msg_id}/attachments/{attachment_id}"
                        att_resp = await client.get(att_url, headers=headers)
                        if att_resp.status_code != 200:
                            continue

                        att_data_b64 = att_resp.json().get("data", "")
                        file_bytes = base64.urlsafe_b64decode(att_data_b64.encode("utf-8"))
                        file_sha256 = hashlib.sha256(file_bytes).hexdigest()
                        attachments_downloaded += 1

                        # Ingest through StatementService
                        try:
                            stmt_review = await stmt_service.ingest_pdf(
                                user_id=connection.user_id,
                                file_bytes=file_bytes,
                                file_name=filename,
                            )
                            statements_created += 1

                            imp = EmailImport(
                                user_id=connection.user_id,
                                connection_id=connection.id,
                                statement_id=stmt_review.id,
                                card_id=stmt_review.card_id,
                                message_id=msg_id,
                                thread_id=m_data.get("threadId"),
                                sender=sender,
                                subject=subject,
                                received_at=received_at,
                                attachment_name=filename,
                                attachment_sha256=file_sha256,
                                status="ingested",
                            )
                            db.add(imp)
                            await db.commit()

                        except DuplicateStatementError:
                            duplicates_skipped += 1
                            # Record duplicate skipped
                            imp = EmailImport(
                                user_id=connection.user_id,
                                connection_id=connection.id,
                                message_id=msg_id,
                                thread_id=m_data.get("threadId"),
                                sender=sender,
                                subject=subject,
                                received_at=received_at,
                                attachment_name=filename,
                                attachment_sha256=file_sha256,
                                status="skipped_duplicate",
                                error_message="Duplicate PDF statement already exists.",
                            )
                            db.add(imp)
                            await db.commit()

                        except Exception as exc:
                            errors.append(f"Failed to ingest {filename}: {exc}")
                            imp = EmailImport(
                                user_id=connection.user_id,
                                connection_id=connection.id,
                                message_id=msg_id,
                                thread_id=m_data.get("threadId"),
                                sender=sender,
                                subject=subject,
                                received_at=received_at,
                                attachment_name=filename,
                                attachment_sha256=file_sha256,
                                status="failed",
                                error_message=str(exc),
                            )
                            db.add(imp)
                            await db.commit()

            connection.sync_status = "idle"
            connection.last_synced_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as exc:
            logger.error("Gmail sync failed: %s", exc, exc_info=True)
            connection.sync_status = "error"
            connection.error_message = str(exc)
            await db.commit()
            errors.append(str(exc))

        return GmailSyncResponse(
            connection_id=connection.id,
            email_address=connection.email_address,
            messages_found=messages_found,
            attachments_downloaded=attachments_downloaded,
            statements_created=statements_created,
            duplicates_skipped=duplicates_skipped,
            errors=errors,
        )

    @classmethod
    async def _simulate_statement_sync(
        cls,
        db: AsyncSession,
        connection: EmailConnection,
    ) -> GmailSyncResponse:
        """Simulates finding and processing statement emails in sandbox environment."""
        # Find active user cards to match
        card_stmt = select(CreditCard).where(
            CreditCard.user_id == connection.user_id,
            CreditCard.status == "active",
        )
        cards = list((await db.execute(card_stmt)).scalars().all())

        if not cards:
            return GmailSyncResponse(
                connection_id=connection.id,
                email_address=connection.email_address,
                messages_found=0,
                attachments_downloaded=0,
                statements_created=0,
                duplicates_skipped=0,
                errors=["No active credit cards registered to match statements."],
            )

        card = cards[0]
        now = datetime.now(timezone.utc)
        sim_msg_id = f"sim_msg_{now.strftime('%Y%m%d%H%M')}_{uuid.uuid4().hex[:6]}"
        sim_filename = f"{card.issuer.replace(' ', '_')}_{card.last_four_digits}_Statement_{now.strftime('%b%Y')}.pdf"

        # Check if already simulated recently
        dup_check = (
            await db.execute(
                select(EmailImport).where(
                    EmailImport.connection_id == connection.id,
                    EmailImport.attachment_name == sim_filename,
                )
            )
        ).scalar_one_or_none()

        if dup_check:
            return GmailSyncResponse(
                connection_id=connection.id,
                email_address=connection.email_address,
                messages_found=1,
                attachments_downloaded=1,
                statements_created=0,
                duplicates_skipped=1,
                errors=[],
            )

        # Record simulated import audit entry
        sim_sha = hashlib.sha256(sim_filename.encode("utf-8")).hexdigest()
        imp = EmailImport(
            user_id=connection.user_id,
            connection_id=connection.id,
            card_id=card.id,
            message_id=sim_msg_id,
            sender=f"statements@{card.issuer.lower().replace(' ', '')}.com",
            subject=f"Your Credit Card E-Statement for Ending {card.last_four_digits}",
            received_at=now - timedelta(days=2),
            attachment_name=sim_filename,
            attachment_sha256=sim_sha,
            status="ingested",
        )
        db.add(imp)
        await db.commit()

        return GmailSyncResponse(
            connection_id=connection.id,
            email_address=connection.email_address,
            messages_found=1,
            attachments_downloaded=1,
            statements_created=1,
            duplicates_skipped=0,
            errors=[],
        )
