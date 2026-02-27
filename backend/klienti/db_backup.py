#!/usr/bin/env python3
"""
AIshield — Denní DB Backup per klient
======================================

Spouští se cronem denně v 03:00.
Pro každého klienta exportuje:
  - companies, clients, scans, findings, questionnaire_responses, documents, orders

Data jsou šifrována (PII) a uložena do:
  KLIENTI/{slug}/db_snapshot/{date}.json
"""

import json
import logging
import os
import sys

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_supabase
from backend.klienti.client_folder_manager import (
    save_db_snapshot,
    save_client_profile,
    slugify_company_name,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DB-BACKUP] %(message)s",
)
logger = logging.getLogger(__name__)

TABLES_TO_BACKUP = [
    "clients",
    "companies", 
    "scans",
    "findings",
    "questionnaire_responses",
    "documents",
    "orders",
]


def run_daily_backup():
    """Hlavní funkce — exportuje DB data per klient."""
    sb = get_supabase()
    
    # 1. Načti všechny firmy s klienty
    companies_res = sb.table("companies").select("*").execute()
    if not companies_res.data:
        logger.warning("Žádné firmy v DB — přeskakuji backup")
        return
    
    logger.info(f"Nalezeno {len(companies_res.data)} firem")
    
    for company in companies_res.data:
        company_id = company["id"]
        company_name = company.get("name", "Unknown")
        
        if not company_name or company_name == "Unknown":
            continue
        
        logger.info(f"Backup: {company_name} ({company_id})")
        
        try:
            # Sestavit snapshot
            snapshot = {}
            
            # Company record
            snapshot["companies"] = [company]
            
            # Related clients
            clients_res = sb.table("clients").select("*").eq("company_id", company_id).execute()
            snapshot["clients"] = clients_res.data or []
            
            client_ids = [c["id"] for c in snapshot["clients"]]
            
            # Scans
            scans_res = sb.table("scans").select("*").eq("company_id", company_id).execute()
            snapshot["scans"] = scans_res.data or []
            
            # Findings
            findings_res = sb.table("findings").select("*").eq("company_id", company_id).execute()
            snapshot["findings"] = findings_res.data or []
            
            # Questionnaire responses (per client)
            all_responses = []
            for cid in client_ids:
                qr = sb.table("questionnaire_responses").select("*").eq("client_id", cid).execute()
                all_responses.extend(qr.data or [])
            snapshot["questionnaire_responses"] = all_responses
            
            # Documents
            docs_res = sb.table("documents").select("*").eq("company_id", company_id).execute()
            snapshot["documents"] = docs_res.data or []
            
            # Orders
            orders_res = sb.table("orders").select("*").eq("company_id", company_id).execute()
            snapshot["orders"] = orders_res.data or []
            
            # Uložit snapshot (s šifrováním PII)
            save_db_snapshot(company_name, snapshot)
            
            # Aktualizovat profil
            profile_data = dict(company)
            if snapshot["clients"]:
                profile_data.update(snapshot["clients"][0])
            save_client_profile(company_name, profile_data)
            
            logger.info(f"  ✅ {company_name}: "
                        f"{len(snapshot['scans'])} scans, "
                        f"{len(snapshot['findings'])} findings, "
                        f"{len(snapshot['questionnaire_responses'])} responses, "
                        f"{len(snapshot['documents'])} docs")
            
        except Exception as e:
            logger.error(f"  ❌ {company_name}: {e}", exc_info=True)
    
    logger.info("Denní backup dokončen")


if __name__ == "__main__":
    run_daily_backup()
