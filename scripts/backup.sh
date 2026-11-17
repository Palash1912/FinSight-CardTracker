#!/usr/bin/env bash
# ==============================================================================
# FinSight AI — Database Backup Utility (Phase 10)
# Creates a compressed PostgreSQL database dump in ./backups/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${ROOT_DIR}/backups"

mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/finsight_backup_${TIMESTAMP}.sql.gz"

DB_USER="${POSTGRES_USER:-finsight}"
DB_NAME="${POSTGRES_DB:-finsight}"

echo "==> Starting FinSight AI database backup..."
echo "    Database: ${DB_NAME} (User: ${DB_USER})"
echo "    Destination: ${BACKUP_FILE}"

if command -v docker &>/dev/null && docker compose ps &>/dev/null; then
    echo "==> Exporting via Docker Compose PostgreSQL container..."
    docker compose exec -T postgres pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip -9 > "${BACKUP_FILE}"
elif command -v pg_dump &>/dev/null; then
    echo "==> Exporting via local pg_dump..."
    pg_dump -U "${DB_USER}" -h localhost "${DB_NAME}" | gzip -9 > "${BACKUP_FILE}"
else
    echo "ERROR: Neither docker compose nor pg_dump found on path." >&2
    exit 1
fi

FILE_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
echo "✅ Backup successfully created: ${BACKUP_FILE} (${FILE_SIZE})"
