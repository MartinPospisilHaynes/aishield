#!/bin/bash
# Nightly invoice backup script
# Backs up invoices to git repo and keeps local VPS copies
# Run via crontab: 0 2 * * * /opt/aishield/backend/scripts/backup_invoices.sh >> /var/log/aishield-invoice-backup.log 2>&1

set -e

INVOICES_DIR="/opt/aishield/invoices"
REPO_DIR="/opt/aishield"
LOG_PREFIX="[invoice-backup $(date '+%Y-%m-%d %H:%M:%S')]"

echo "$LOG_PREFIX Starting invoice backup..."

# Check if invoices dir exists
if [ ! -d "$INVOICES_DIR" ]; then
    echo "$LOG_PREFIX No invoices directory found. Nothing to backup."
    exit 0
fi

# Count invoices
INVOICE_COUNT=$(find "$INVOICES_DIR" -name "*.pdf" | wc -l)
echo "$LOG_PREFIX Found $INVOICE_COUNT invoice PDF(s)"

if [ "$INVOICE_COUNT" -eq 0 ]; then
    echo "$LOG_PREFIX No invoices to backup."
    exit 0
fi

# Git backup
cd "$REPO_DIR"

# Make sure git is configured
git config user.email "backup@aishield.cz" 2>/dev/null || true
git config user.name "AIshield Backup" 2>/dev/null || true

# Add invoices to git
git add invoices/ 2>/dev/null || true

# Check if there are changes to commit
if git diff --cached --quiet 2>/dev/null; then
    echo "$LOG_PREFIX No new invoices to commit."
else
    git commit -m "Backup: $INVOICE_COUNT invoices - $(date '+%Y-%m-%d')" 2>/dev/null
    git push origin main 2>/dev/null && echo "$LOG_PREFIX Git push successful" || echo "$LOG_PREFIX Git push failed (will retry next run)"
fi

# Create compressed backup
BACKUP_DIR="/opt/aishield/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/invoices-$(date '+%Y%m%d').tar.gz"
tar -czf "$BACKUP_FILE" -C /opt/aishield invoices/
echo "$LOG_PREFIX Compressed backup saved: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Keep only last 30 daily backups
find "$BACKUP_DIR" -name "invoices-*.tar.gz" -mtime +30 -delete 2>/dev/null || true

echo "$LOG_PREFIX Backup complete!"
