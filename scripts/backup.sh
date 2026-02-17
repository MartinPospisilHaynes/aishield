#!/bin/zsh
# ═══════════════════════════════════════════════════════════════
# AIshield — Automatický zálohovací systém
# Spouští se každou hodinu přes launchd (macOS)
# Drží posledních 10 záloh, starší přepisuje
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_DIR="$HOME/Projects/aishield"
BACKUP_BASE="$HOME/Projects/aishield_backups"
MAX_BACKUPS=10
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_BASE}/${BACKUP_NAME}"

# Vytvoř backup složku
mkdir -p "$BACKUP_BASE"

# Zkopíruj celý projekt (bez node_modules, .next, __pycache__, .git)
rsync -a \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.vercel' \
    --exclude='venv' \
    "$PROJECT_DIR/" "$BACKUP_PATH/"

# Ulož git stav pro referenci
cd "$PROJECT_DIR"
git log --oneline -1 > "${BACKUP_PATH}/_GIT_STATE.txt"
git status --short >> "${BACKUP_PATH}/_GIT_STATE.txt"
echo "Backup: ${TIMESTAMP}" >> "${BACKUP_PATH}/_GIT_STATE.txt"

# Smaž nejstarší zálohy, pokud jich je víc než MAX_BACKUPS
cd "$BACKUP_BASE"
BACKUP_COUNT=$(ls -d backup_* 2>/dev/null | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    EXCESS=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -d backup_* | sort | head -n "$EXCESS" | xargs rm -rf
fi

echo "[$(date)] Záloha vytvořena: ${BACKUP_PATH} (celkem: $(ls -d backup_* 2>/dev/null | wc -l | tr -d ' ')/${MAX_BACKUPS})"
