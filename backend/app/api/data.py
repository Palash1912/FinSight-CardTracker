"""Data export, CSV download, and GDPR privacy purge API router — /api/v1/data."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.services.data_export_service import DataExportService
from app.storage.local import LocalStorageProvider

router = APIRouter(prefix="/data")


@router.get("/export", response_model=dict[str, Any])
async def export_data(
    user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Export complete user financial records in structured JSON format."""
    return await DataExportService.export_all(db, user.id)


@router.get("/transactions.csv", response_class=PlainTextResponse)
async def export_transactions_csv(
    user: CurrentUser,
    db: DbSession,
) -> Response:
    """Download all transactions as a CSV file."""
    csv_content = await DataExportService.export_transactions_csv(db, user.id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="finsight_transactions.csv"'},
    )


@router.delete("/purge", status_code=status.HTTP_200_OK)
async def purge_user_data(
    user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Permanently delete all financial data, statements, cards, and audit logs."""
    settings = get_settings()
    storage = LocalStorageProvider(settings.storage_path)

    await DataExportService.purge_all(db, storage, user.id)
    return {
        "status": "success",
        "message": "All user data, records, and files have been permanently purged.",
    }
