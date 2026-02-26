#!/bin/bash
# AIshield — správný restart backend serveru
# Používá SYSTEMD — nikdy neresetuje logy
# Použití: /opt/aishield/restart.sh

set -e

echo "[$(date)] === AIshield Backend Restart ==="

# 1. Restart přes systemd (SPRÁVNÝ způsob)
echo "[$(date)] Restarting via systemd..."
systemctl restart aishield-api

# 2. Počkat na startup
sleep 3

# 3. Ověřit health
if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "[$(date)] ✓ Backend is HEALTHY"
    systemctl status aishield-api --no-pager | head -5
else
    echo "[$(date)] ✗ Backend FAILED to start — checking logs:"
    journalctl -u aishield-api -n 30 --no-pager
    exit 1
fi

# 4. Restart ARQ worker (pokud běží)
echo "[$(date)] Checking ARQ worker..."
if pgrep -f "arq backend.jobs.worker" > /dev/null; then
    echo "[$(date)] Restarting ARQ worker..."
    pkill -f "arq backend.jobs.worker" || true
    sleep 2
fi
cd /opt/aishield
nohup /opt/aishield/venv/bin/arq backend.jobs.worker.WorkerSettings >> /var/log/aishield-worker.log 2>&1 &
sleep 2
if pgrep -f "arq backend.jobs.worker" > /dev/null; then
    echo "[$(date)] ✓ ARQ worker is RUNNING"
else
    echo "[$(date)] ✗ ARQ worker FAILED to start"
fi

echo "[$(date)] === Restart complete ==="
