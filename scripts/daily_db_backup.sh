#!/bin/bash
# AIshield — Denní DB backup (spouští se cronem v 03:00)
cd /opt/aishield
/opt/aishield/venv/bin/python3 -m backend.klienti.db_backup >> /var/log/aishield_db_backup.log 2>&1
