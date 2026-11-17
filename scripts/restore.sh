#!/usr/bin/env bash
# ==============================================================================
# FinSight AI — Database Restore Utility (Phase 10)
# Restores a compressed PostgreSQL database dump from ./backups/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_backup.sql.gz>"
    echo "Available backups in ./backups/:"
    ls -lh "${ROOT_DIR}/backups"/*.sql.gz 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}" >&2
    exit 1
fi

DB_USER="${POSTGRES_USER:-finsight}"
DB_NAME="${POSTGRES_DB:-finsight}"

echo "⚠️  WARNING: Restoring will overwrite existing data in '${DB_NAME}'!"
read -r -p "Are you sure you want to proceed? [y/N] " response
case "$response" in
    [yY][eE][sS]|[yY])
        ;;
    *)
        echo "Restore cancelled."
        exit 0
        ;;
esac

echo "==> Restoring from ${BACKUP_FILE}..."

if command -v docker &>/dev/null && docker compose ps &>/dev/null; then
    echo "==> Restoring into Docker Compose PostgreSQL container..."
    gunzip -c "${BACKUP_FILE}" | docker compose exec -T postgres psql -U "${DB_USER}" -d "${DB_NAME}"
elif command -v psql &>/dev/null; then
    echo "==> Restoring via local psql..."
    gunzip -c "${BACKUP_FILE}" | psql -U "${DB_USER}" -h localhost -d "${DB_NAME}"
else
    echo "ERROR: Neither docker compose nor psql found on path." >&2
    exit 1
fi

echo "✅ Database restore completed successfully!"
