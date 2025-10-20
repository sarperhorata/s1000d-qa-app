#!/bin/bash
# S1000D QA System - Automated Backup Script
# Usage: ./backup_chromadb.sh [backup_name]

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME=${1:-"chromadb_${TIMESTAMP}"}
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "Creating backup: ${BACKUP_NAME}"
echo "Source: ./chroma_data"
echo "Destination: ${BACKUP_PATH}"

# Create backup
cp -r ./chroma_data "${BACKUP_PATH}"

# Get size
SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)
echo "✅ Backup completed successfully"
echo "📦 Backup size: ${SIZE}"
echo "📍 Location: ${BACKUP_PATH}"

# List recent backups
echo ""
echo "📋 Recent backups:"
ls -la ${BACKUP_DIR}/ | tail -6

echo ""
echo "🔧 Management commands:"
echo "   Restore: cp -r ${BACKUP_PATH} ./chroma_data"
echo "   Clean old: find ${BACKUP_DIR} -name 'chromadb_*' -mtime +7 -delete"

