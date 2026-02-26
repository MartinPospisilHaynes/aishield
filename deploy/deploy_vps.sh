# ============================================
# AIshield.cz — VPS Deploy Script
# ============================================
# Spusť na VPS (46.28.110.102) jako root:
#   curl -sL https://raw.githubusercontent.com/.../deploy_vps.sh | bash
# nebo zkopíruj a spusť ručně
# ============================================

set -e

APP_DIR="/opt/aishield"
REPO_URL="https://github.com/TODO/aishield.git"  # doplnit po pushnutí na GitHub

echo "🛡️ AIshield VPS Deploy"
echo "======================"

# 1. System deps
echo "📦 Instalace systémových závislostí..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx certbot python3-certbot-nginx git curl

# 2. Playwright system deps (Chromium)
echo "🎭 Instalace Playwright závislostí..."
apt-get install -y -qq libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    libx11-xcb1 fonts-liberation

# 3. Clone/update repo
if [ -d "$APP_DIR" ]; then
    echo "🔄 Aktualizuji repo..."
    cd "$APP_DIR"
    git pull
else
    echo "📥 Klonuji repo..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# 4. Python venv + deps
echo "🐍 Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 5. Playwright browsers
echo "🎭 Instalace Playwright Chromium..."
playwright install chromium

# 6. Environment file
if [ ! -f .env ]; then
    echo "⚠️  Soubor .env neexistuje!"
    echo "   Zkopíruj .env z razvoje a uprav:"
    echo "   - ENVIRONMENT=production"
    echo "   - GOPAY_IS_PRODUCTION=true (až bude schváleno)"
    echo "   - APP_URL=https://aishield.cz"
    echo "   - API_URL=https://api.aishield.cz"
fi

# 7. Systemd service
echo "⚙️ Nastavuji systemd službu..."
cat > /etc/systemd/system/aishield-api.service << 'EOF'
[Unit]
Description=AIshield FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aishield
EnvironmentFile=/opt/aishield/.env
ExecStart=/opt/aishield/venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aishield-api
systemctl restart aishield-api

# 8. Nginx proxy
echo "🌐 Nastavuji Nginx reverse proxy..."
cat > /etc/nginx/sites-available/api.aishield.cz << 'NGINX'
server {
    listen 80;
    server_name api.aishield.cz;

    # Security headers
    server_tokens off;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Skrýt interní hlavičky
        proxy_hide_header X-Powered-By;
        proxy_hide_header Server;
        
        # Dlouhé timeouty pro skeny (až 2 min)
        proxy_read_timeout 180s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        
        # Velikost body pro webhooky
        client_max_body_size 10M;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/api.aishield.cz /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 9. SSL certifikát
echo "🔒 SSL certifikát..."
certbot --nginx -d api.aishield.cz --non-interactive --agree-tos -m info@desperados-design.cz || echo "⚠️ Certbot selhal — zkontroluj DNS"

# 10. Cron jobs
echo "⏰ Nastavuji cron jobs..."
cat > /etc/cron.d/aishield << 'CRON'
# AIshield automatizace
SHELL=/bin/bash
PATH=/opt/aishield/venv/bin:/usr/local/bin:/usr/bin:/bin

# Orchestrátor — denně v 6:00 (prospecting + emaily)
0 6 * * * root cd /opt/aishield && /opt/aishield/venv/bin/python3 -m backend.outbound.orchestrator >> /var/log/aishield-orchestrator.log 2>&1

# Monitoring — týdně v pondělí v 3:00 (re-scan platících klientů)
0 3 * * 1 root cd /opt/aishield && /opt/aishield/venv/bin/python3 -c "import asyncio; from backend.monitoring.diff_engine import run_monitoring_cycle; asyncio.run(run_monitoring_cycle())" >> /var/log/aishield-monitoring.log 2>&1

# Lead scoring — denně v 7:00
0 7 * * * root cd /opt/aishield && /opt/aishield/venv/bin/python3 -c "import asyncio; from backend.prospecting.lead_scoring import score_all_companies; asyncio.run(score_all_companies())" >> /var/log/aishield-scoring.log 2>&1

# Data retention cleanup — denně v 4:00 (audit log, staré eventy, neaktivní firmy)
0 4 * * * root cd /opt/aishield && /opt/aishield/venv/bin/python3 -m backend.security.data_cleanup >> /var/log/aishield-cleanup.log 2>&1
CRON

chmod 644 /etc/cron.d/aishield

echo ""
echo "✅ Deploy dokončen!"
echo ""
echo "Zkontroluj:"
echo "  systemctl status aishield-api"
echo "  curl http://localhost:8000/api/health"
echo "  curl https://api.aishield.cz/api/health"
echo ""
echo "Logy:"
echo "  journalctl -u aishield-api -f"
echo "  tail -f /var/log/aishield-orchestrator.log"
