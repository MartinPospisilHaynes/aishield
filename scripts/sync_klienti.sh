#!/bin/zsh
# ════════════════════════════════════════════════════════════════
# AIshield — Sync klientských dokumentů z VPS na lokální Mac
# Spouští se automaticky každých 5 minut přes LaunchAgent.
# Pokud není síť / VPS nedostupný, tiše skončí.
# ════════════════════════════════════════════════════════════════

VPS="root@46.28.110.102"
REMOTE_DIR="/opt/aishield/klienti/"
LOCAL_DIR="$HOME/Projects/aishield/klienti/"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/OPORTUNITY/dokumenty/"
LOG="$HOME/Projects/aishield/logs/sync_klienti.log"

mkdir -p "$(dirname "$LOG")"
mkdir -p "$LOCAL_DIR"

# Test síťové konektivity (timeout 3s)
if ! ssh -o BatchMode=yes -o ConnectTimeout=3 "$VPS" 'true' 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — VPS nedostupný, přeskakuji" >> "$LOG"
    exit 0
fi

# Rsync — stáhne NOVÉ soubory, nesmaže staré
rsync -avz \
    --timeout=30 \
    -e "ssh -o BatchMode=yes -o ConnectTimeout=5" \
    "$VPS:$REMOTE_DIR" \
    "$LOCAL_DIR" \
    >> "$LOG" 2>&1

STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Sync OK" >> "$LOG"

    # Zrcadlit do iCloud Drive dokumenty/ složky
    if [ -d "$LOCAL_DIR" ]; then
        mkdir -p "$ICLOUD_DIR"
        cp -R "$LOCAL_DIR"* "$ICLOUD_DIR" 2>/dev/null
        echo "$(date '+%Y-%m-%d %H:%M:%S') — Kopie do iCloud OK" >> "$LOG"
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Sync FAILED (exit $STATUS)" >> "$LOG"
fi

# Rotace logu (max 1000 řádků)
if [ -f "$LOG" ] && [ $(wc -l < "$LOG") -gt 1000 ]; then
    tail -500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
