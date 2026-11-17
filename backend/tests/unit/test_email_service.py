"""Unit tests for Phase 7: Gmail OAuth statement ingestion and token encryption."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas.email import (
    EmailConnectionRead,
    EmailImportRead,
    GmailAuthUrlResponse,
    GmailSyncResponse,
)
from app.services.gmail_service import GmailService
from app.services.token_encryption import decrypt_token, encrypt_token


def test_token_encryption_roundtrip() -> None:
    original = "ya29.a0AfH6SMD_mock_sample_google_access_token_123456789"
    encrypted = encrypt_token(original)
    assert encrypted is not None
    assert encrypted != original

    decrypted = decrypt_token(encrypted)
    assert decrypted == original


def test_gmail_auth_url_construction() -> None:
    state = "secure_random_state_xyz"
    url = GmailService.build_auth_url(state)
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "gmail.readonly" in url
    assert "access_type=offline" in url
    assert f"state={state}" in url


def test_gmail_search_query_builder() -> None:
    query = GmailService.build_search_query(days_back=60)
    assert "hdfcbank" in query
    assert "icicibank" in query
    assert "hsbc" in query
    assert "axisbank" in query
    assert "filename:pdf" in query
    assert "after:" in query


def test_email_schemas() -> None:
    now = datetime.now(timezone.utc)
    conn_id = uuid.uuid4()

    conn = EmailConnectionRead(
        id=conn_id,
        email_address="owner@finsight.local",
        provider="gmail",
        sync_status="idle",
        last_synced_at=now,
        error_message=None,
        created_at=now,
    )
    assert conn.email_address == "owner@finsight.local"
    assert conn.sync_status == "idle"

    imp = EmailImportRead(
        id=uuid.uuid4(),
        connection_id=conn_id,
        statement_id=uuid.uuid4(),
        card_id=uuid.uuid4(),
        sender="statements@hdfcbank.net",
        subject="Your HDFC Credit Card Statement",
        received_at=now,
        attachment_name="HDFC_Millennia_Oct2026.pdf",
        status="ingested",
        error_message=None,
        created_at=now,
    )
    assert imp.status == "ingested"
    assert "hdfcbank" in imp.sender

    resp = GmailSyncResponse(
        connection_id=conn_id,
        email_address="owner@finsight.local",
        messages_found=5,
        attachments_downloaded=2,
        statements_created=2,
        duplicates_skipped=0,
        errors=[],
    )
    assert resp.messages_found == 5
    assert resp.statements_created == 2
