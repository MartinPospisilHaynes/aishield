"""
AIshield — Client Folder Manager
=================================

Správa klientských složek s automatickým šifrováním osobních údajů.

Struktura:
  KLIENTI/{firma_slug}/
    ├── profil.json           # šifrované PII + nešifrovaná metadata
    ├── scan/
    │   └── scan_{id}_{date}.json
    ├── dotaznik/
    │   └── responses_{date}.json
    ├── dokumenty/
    │   └── gen_{timestamp}/  # PDF, HTML, PPTX soubory
    └── db_snapshot/
        └── {date}.json       # denní DB export

Bezpečnost:
  - PII (jméno, email, IČO, telefon, adresa) → Fernet AES šifrování
  - Klíč POUZE v .env na VPS — nikdy na GitHub
  - Git/Mac dostávají šifrované soubory — bez klíče nečitelné
"""

import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════════════

KLIENTI_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "KLIENTI",
)

SUBFOLDERS = ["scan", "dotaznik", "dokumenty", "db_snapshot"]


# ══════════════════════════════════════════════════════════════════════
# ENCRYPTION — Fernet (AES-128-CBC + HMAC-SHA256)
# ══════════════════════════════════════════════════════════════════════

_fernet_instance = None

# Pole, která obsahují osobní údaje a MUSÍ být šifrována
PII_FIELDS = {
    "name", "company_name", "email", "contact_email", "contact_name",
    "phone", "address", "ico", "dic", "contact_role",
    "q_company_legal_name", "q_company_ico", "q_company_contact_email",
    "q_company_contact_name", "q_company_address", "q_company_phone",
    "user_email", "billing_data",
}


def _get_fernet():
    """Lazy-load Fernet instance from env."""
    global _fernet_instance
    if _fernet_instance is None:
        from cryptography.fernet import Fernet
        key = os.environ.get("BACKUP_ENCRYPTION_KEY")
        if not key:
            # Try loading from .env file directly
            env_path = os.path.join(os.path.dirname(KLIENTI_BASE), ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("BACKUP_ENCRYPTION_KEY="):
                            key = line.strip().split("=", 1)[1]
                            break
        if not key:
            raise RuntimeError("BACKUP_ENCRYPTION_KEY not found in environment or .env")
        _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet_instance


def encrypt_value(value: str) -> str:
    """Zašifruje řetězec → base64 Fernet token."""
    f = _get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
    """Dešifruje Fernet token → původní řetězec."""
    f = _get_fernet()
    return f.decrypt(token.encode("utf-8")).decode("utf-8")


def encrypt_pii_fields(data: dict) -> dict:
    """
    Projde dict a zašifruje všechna PII pole.
    Vrátí nový dict kde PII pole jsou nahrazena šifrovaným ekvivalentem.
    Přidá pole '_encrypted_fields' se seznamem šifrovaných klíčů.
    """
    result = {}
    encrypted_fields = []
    
    for key, value in data.items():
        if key in PII_FIELDS and value and isinstance(value, str):
            result[key] = encrypt_value(value)
            encrypted_fields.append(key)
        elif key in PII_FIELDS and isinstance(value, dict):
            # billing_data etc — šifrovat celý JSON
            result[key] = encrypt_value(json.dumps(value, ensure_ascii=False))
            encrypted_fields.append(key)
        else:
            result[key] = value
    
    result["_encrypted_fields"] = encrypted_fields
    result["_encryption"] = "fernet-aes128"
    return result


def decrypt_pii_fields(data: dict) -> dict:
    """Dešifruje PII pole v dictu (inverzní k encrypt_pii_fields)."""
    encrypted_fields = data.get("_encrypted_fields", [])
    result = {}
    
    for key, value in data.items():
        if key in ("_encrypted_fields", "_encryption"):
            continue
        if key in encrypted_fields and isinstance(value, str):
            try:
                decrypted = decrypt_value(value)
                # Try parsing as JSON (for billing_data etc.)
                try:
                    result[key] = json.loads(decrypted)
                except (json.JSONDecodeError, ValueError):
                    result[key] = decrypted
            except Exception:
                result[key] = value  # Can't decrypt — leave as-is
        else:
            result[key] = value
    
    return result


# ══════════════════════════════════════════════════════════════════════
# SLUG HELPER
# ══════════════════════════════════════════════════════════════════════

def slugify_company_name(name: str) -> str:
    """Převede název firmy na bezpečný adresářový název.
    'Škoda Auto a.s.' → 'skoda_auto_a_s'
    """
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")
    return slug or "unknown_company"


# ══════════════════════════════════════════════════════════════════════
# FOLDER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def ensure_client_folder(company_name: str) -> str:
    """
    Vytvoří klientskou složku se všemi podadresáři.
    Vrátí cestu ke klientské složce.
    
    Idempotentní — bezpečné volat opakovaně.
    """
    slug = slugify_company_name(company_name)
    client_dir = os.path.join(KLIENTI_BASE, slug)
    
    for subfolder in SUBFOLDERS:
        os.makedirs(os.path.join(client_dir, subfolder), exist_ok=True)
    
    logger.info(f"[KLIENTI] Složka zajištěna: {client_dir}")
    return client_dir


def get_client_folder(company_name: str) -> str:
    """Vrátí cestu ke klientské složce (bez vytváření)."""
    slug = slugify_company_name(company_name)
    return os.path.join(KLIENTI_BASE, slug)


# ══════════════════════════════════════════════════════════════════════
# SAVE OPERATIONS
# ══════════════════════════════════════════════════════════════════════

def save_client_profile(company_name: str, profile_data: dict) -> str:
    """
    Uloží profil klienta s šifrovanými PII.
    
    Args:
        company_name: Název firmy
        profile_data: Dict s daty klienta (company + client tabulky)
    
    Returns:
        Cesta k uloženému souboru
    """
    client_dir = ensure_client_folder(company_name)
    
    # Šifrování PII
    encrypted_data = encrypt_pii_fields(profile_data)
    encrypted_data["_saved_at"] = datetime.now(timezone.utc).isoformat()
    encrypted_data["_company_slug"] = slugify_company_name(company_name)
    
    filepath = os.path.join(client_dir, "profil.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(encrypted_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[KLIENTI] Profil uložen: {filepath} ({len(encrypted_data.get('_encrypted_fields', []))} PII polí šifrováno)")
    return filepath


def save_scan_results(company_name: str, scan_data: dict, findings: list) -> str:
    """
    Uloží výsledky scanu do scan/ podsložky.
    """
    client_dir = ensure_client_folder(company_name)
    
    scan_id = scan_data.get("id", "unknown")
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    payload = {
        "scan": scan_data,
        "findings": findings,
        "findings_count": len(findings),
        "_saved_at": datetime.now(timezone.utc).isoformat(),
    }
    
    filepath = os.path.join(client_dir, "scan", f"scan_{scan_id}_{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[KLIENTI] Scan uložen: {filepath} ({len(findings)} findings)")
    return filepath


def save_questionnaire(company_name: str, responses: list) -> str:
    """
    Uloží odpovědi z dotazníku s šifrováním PII polí.
    """
    client_dir = ensure_client_folder(company_name)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    # Šifrování PII v odpovědích
    encrypted_responses = []
    for resp in responses:
        qkey = resp.get("question_key", "")
        # Pokud odpověď obsahuje PII (email, jméno, adresa, IČO...)
        if any(pii_hint in qkey.lower() for pii_hint in ["email", "name", "jmeno", "ico", "dic", "adresa", "address", "phone", "telefon"]):
            answer = resp.get("answer", "")
            if answer and isinstance(answer, str):
                encrypted_resp = dict(resp)
                encrypted_resp["answer"] = encrypt_value(answer)
                encrypted_resp["_encrypted"] = True
                encrypted_responses.append(encrypted_resp)
                continue
        encrypted_responses.append(resp)
    
    payload = {
        "responses": encrypted_responses,
        "total_responses": len(responses),
        "_encryption": "fernet-aes128",
        "_saved_at": datetime.now(timezone.utc).isoformat(),
    }
    
    filepath = os.path.join(client_dir, "dotaznik", f"responses_{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[KLIENTI] Dotazník uložen: {filepath} ({len(responses)} odpovědí)")
    return filepath


def save_generation_files(
    company_name: str,
    generation_id: str,
    all_file_bytes: dict,
    generation_report: Optional[dict] = None,
) -> str:
    """
    Uloží dokumenty generace do dokumenty/{gen_id}/ podsložky.
    
    Args:
        company_name: Název firmy
        generation_id: ID generace (gen_20260301_143022)
        all_file_bytes: Dict filename → bytes
        generation_report: Optional JSON report
    
    Returns:
        Cesta k adresáři generace
    """
    client_dir = ensure_client_folder(company_name)
    gen_dir = os.path.join(client_dir, "dokumenty", generation_id)
    os.makedirs(gen_dir, exist_ok=True)
    
    saved = 0
    for filename, file_bytes in all_file_bytes.items():
        try:
            filepath = os.path.join(gen_dir, filename)
            with open(filepath, "wb") as f:
                f.write(file_bytes)
            saved += 1
        except Exception as e:
            logger.error(f"[KLIENTI] Chyba při ukládání {filename}: {e}")
    
    # Uložit generation report pokud je k dispozici
    if generation_report:
        report_path = os.path.join(gen_dir, "generation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(generation_report, f, ensure_ascii=False, indent=2)
        saved += 1
    
    logger.info(f"[KLIENTI] Generace uložena: {gen_dir} ({saved} souborů)")
    return gen_dir


def save_db_snapshot(company_name: str, snapshot_data: dict) -> str:
    """
    Uloží denní DB snapshot s šifrováním PII.
    Drží posledních 30 snapshotů.
    """
    client_dir = ensure_client_folder(company_name)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Šifrování PII ve snapshotu
    encrypted_snapshot = {}
    for table_name, rows in snapshot_data.items():
        if isinstance(rows, list):
            encrypted_rows = []
            for row in rows:
                if isinstance(row, dict):
                    encrypted_rows.append(encrypt_pii_fields(row))
                else:
                    encrypted_rows.append(row)
            encrypted_snapshot[table_name] = encrypted_rows
        else:
            encrypted_snapshot[table_name] = rows
    
    encrypted_snapshot["_saved_at"] = datetime.now(timezone.utc).isoformat()
    encrypted_snapshot["_encryption"] = "fernet-aes128"
    
    snapshot_dir = os.path.join(client_dir, "db_snapshot")
    filepath = os.path.join(snapshot_dir, f"{date_str}.json")
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(encrypted_snapshot, f, ensure_ascii=False, indent=2)
    
    # Rotace — drží max 30 snapshotů
    snapshots = sorted([
        f for f in os.listdir(snapshot_dir)
        if f.endswith(".json") and f[0].isdigit()
    ])
    while len(snapshots) > 30:
        oldest = snapshots.pop(0)
        os.remove(os.path.join(snapshot_dir, oldest))
        logger.info(f"[KLIENTI] Smazán starý snapshot: {oldest}")
    
    logger.info(f"[KLIENTI] DB snapshot uložen: {filepath}")
    return filepath
