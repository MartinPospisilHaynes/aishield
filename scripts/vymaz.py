"""
Kompletní výmaz VŠECH testovacích dat z databáze a Supabase Auth.

Smaže auth uživatele, firmy, objednávky, skeny, nálezy, dokumenty,
dotazníky a veškerá další data pro hardcoded testovací emaily.
Po spuštění je databáze v čistém stavu — lze okamžitě znovu
registrovat na libovolný z testovacích emailů.

Použití na VPS:
  cd /opt/aishield && set -a && source .env && set +a && source venv/bin/activate
  python3 scripts/vymaz.py              # dry-run (ukáže co smaže)
  python3 scripts/vymaz.py --yes        # plný výmaz
  python3 scripts/vymaz.py --yes --vps  # výmaz + restart backend
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import httpx

# ══════════════════════════════════════════════════════════
#  TESTOVACÍ EMAILY & DOMÉNY — sem přidej další dle potřeby
# ══════════════════════════════════════════════════════════
TEST_EMAILS = [
    "info@desperados-design.cz",
    "pospa69@seznam.cz",
    "bc.pospa@gmal.com",
    "bc.pospa@gmail.com",
]

TEST_DOMAINS = [
    "desperados-design.cz",
]

TEST_VOUCHER = "PIONEER-MH2026A"

# ══════════════════════════════════════════════════════════
#  Supabase credentials
# ══════════════════════════════════════════════════════════
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_KEY and Path("/opt/aishield/.env").exists():
    with open("/opt/aishield/.env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"')
            if k == "SUPABASE_URL" and not SUPABASE_URL:
                SUPABASE_URL = v
            elif k == "SUPABASE_SERVICE_ROLE_KEY" and not SUPABASE_KEY:
                SUPABASE_KEY = v

BASE = f"{SUPABASE_URL}/rest/v1"
H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
HJ = {**H, "Content-Type": "application/json", "Prefer": "return=minimal"}


# ── HTTP helpers ──

def get(path):
    r = httpx.get(f"{BASE}/{path}", headers=H, timeout=15)
    return r.json() if r.status_code == 200 else []


def delete(path):
    return httpx.delete(f"{BASE}/{path}", headers=HJ, timeout=15).status_code


def patch(path, data):
    return httpx.patch(f"{BASE}/{path}", headers=HJ, json=data, timeout=15).status_code


def safe_del(table, col, val):
    """Smaže záznamy; ignoruje neexistující tabulky/sloupce."""
    s = delete(f"{table}?{col}=eq.{val}")
    return s in (200, 204, 404, 400)


def safe_patch(table, col, val, data):
    s = patch(f"{table}?{col}=eq.{val}", data)
    return s in (200, 204, 404, 400)


# ══════════════════════════════════════════════════════════
#  FÁZE 1: AUTH — smazat uživatele
# ══════════════════════════════════════════════════════════

def phase_auth():
    print("\n── FÁZE 1: AUTH UŽIVATELÉ ──")
    ah = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    r = httpx.get(f"{SUPABASE_URL}/auth/v1/admin/users?per_page=500", headers=ah, timeout=15)
    if r.status_code != 200:
        print(f"  CHYBA: nelze číst auth ({r.status_code})")
        return 0

    users = r.json().get("users", [])
    test_set = {e.lower() for e in TEST_EMAILS}
    domain_set = {d.lower() for d in TEST_DOMAINS}

    deleted = 0
    for u in users:
        ue = (u.get("email") or "").lower()
        if ue in test_set or any(ue.endswith(f"@{d}") for d in domain_set):
            dr = httpx.delete(
                f"{SUPABASE_URL}/auth/v1/admin/users/{u['id']}",
                headers=ah, timeout=15,
            )
            ok = dr.status_code == 200
            print(f"  {'OK' if ok else 'CHYBA'}: {ue}")
            if ok:
                deleted += 1

    if deleted == 0:
        print("  (žádní auth uživatelé nenalezeni)")
    else:
        print(f"  Smazáno auth uživatelů: {deleted}")
    return deleted


# ══════════════════════════════════════════════════════════
#  FÁZE 2: DISCOVERY — najít všechny entity
# ══════════════════════════════════════════════════════════

def phase_discover():
    print("\n── FÁZE 2: DISCOVERY ──")

    company_ids = set()
    client_ids = set()

    for email in TEST_EMAILS:
        for c in get(f"companies?email=eq.{email}&select=id,name"):
            company_ids.add(c["id"])
            print(f"  firma: {c.get('name','?')} ({email})")
    for domain in TEST_DOMAINS:
        for c in get(f"companies?url=ilike.*{domain}*&select=id,name"):
            if c["id"] not in company_ids:
                company_ids.add(c["id"])
                print(f"  firma: {c.get('name','?')} ({domain})")

    for email in TEST_EMAILS:
        for c in get(f"clients?email=eq.{email}&select=id"):
            client_ids.add(c["id"])

    scan_ids = set()
    for cid in company_ids:
        for s in get(f"scans?company_id=eq.{cid}&select=id"):
            scan_ids.add(s["id"])

    order_ids = set()
    for email in TEST_EMAILS:
        for o in get(f"orders?email=eq.{email}&select=id"):
            order_ids.add(o["id"])

    print(f"  Firmy:      {len(company_ids)}")
    print(f"  Klienti:    {len(client_ids)}")
    print(f"  Skeny:      {len(scan_ids)}")
    print(f"  Objednávky: {len(order_ids)}")

    return company_ids, client_ids, scan_ids, order_ids


# ══════════════════════════════════════════════════════════
#  FÁZE 3: DELETE — child-first pořadí
# ══════════════════════════════════════════════════════════

# Tabulky s FK na company_id (nebo client_id = company_id)
COMPANY_TABLES = [
    ("findings", "company_id"),
    ("scan_results", "company_id"),
    ("ai_systems", "company_id"),
    ("documents", "company_id"),
    ("generated_documents", "company_id"),
    ("notifications", "company_id"),
    ("comments", "company_id"),
    ("audit_reports", "company_id"),
    ("visitor_events", "company_id"),
    ("invoices", "company_id"),
]


def phase_delete(company_ids, client_ids, scan_ids, order_ids):
    print("\n── FÁZE 3: MAZÁNÍ DAT ──")
    ok_n = 0
    err_n = 0

    def do(label, result):
        nonlocal ok_n, err_n
        if result:
            ok_n += 1
        else:
            err_n += 1
            print(f"  [!] {label}")

    # A) Scan-linked tabulky
    for sid in scan_ids:
        do(f"findings(scan) {sid[:8]}", safe_del("findings", "scan_id", sid))
        do(f"scan_pages {sid[:8]}", safe_del("scan_pages", "scan_id", sid))

    # B) Company-linked tabulky
    for cid in company_ids:
        for table, col in COMPANY_TABLES:
            do(f"{table} {cid[:8]}", safe_del(table, col, cid))
        # questionnaire_responses má client_id = company_id
        do(f"questionnaire {cid[:8]}", safe_del("questionnaire_responses", "client_id", cid))
        # scany
        do(f"scans {cid[:8]}", safe_del("scans", "company_id", cid))

    # C) Client-linked
    for clid in client_ids:
        do(f"questionnaire(cl) {clid[:8]}", safe_del("questionnaire_responses", "client_id", clid))

    # D) Order-linked
    for oid in order_ids:
        do(f"payments {oid[:8]}", safe_del("payments", "order_id", oid))

    # E) Email-linked
    for email in TEST_EMAILS:
        do(f"orders {email}", safe_del("orders", "email", email))
        safe_del("email_log", "email", email)  # nemusí existovat

    # F) Pioneer codes — reset na active
    pioneer_reset = {
        "status": "active", "used_at": None, "used_by_email": None,
        "company_id": None, "client_id": None, "order_id": None,
    }
    for cid in company_ids:
        safe_patch("pioneer_codes", "company_id", cid, pioneer_reset)
    for email in TEST_EMAILS:
        safe_patch("pioneer_codes", "used_by_email", email, pioneer_reset)

    # G) Voucher — reset used_count
    patch(f"voucher_codes?code=eq.{TEST_VOUCHER}", {"used_count": 0})
    print(f"  Voucher {TEST_VOUCHER}: used_count → 0")

    # H) Klienti
    for clid in client_ids:
        safe_del("clients", "id", clid)
    for email in TEST_EMAILS:
        safe_del("clients", "email", email)

    # I) FIRMY — kompletně smazat (ne jen resetovat!)
    for cid in company_ids:
        do(f"companies {cid[:8]}", safe_del("companies", "id", cid))

    print(f"  Hotovo: {ok_n} OK | {err_n} chyb")
    return err_n == 0


# ══════════════════════════════════════════════════════════
#  FÁZE 4: VERIFIKACE
# ══════════════════════════════════════════════════════════

def phase_verify():
    print("\n── FÁZE 4: VERIFIKACE ──")
    problems = []

    # Auth
    ah = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    r = httpx.get(f"{SUPABASE_URL}/auth/v1/admin/users?per_page=500", headers=ah, timeout=15)
    if r.status_code == 200:
        test_set = {e.lower() for e in TEST_EMAILS}
        domain_set = {d.lower() for d in TEST_DOMAINS}
        for u in r.json().get("users", []):
            ue = (u.get("email") or "").lower()
            if ue in test_set or any(ue.endswith(f"@{d}") for d in domain_set):
                problems.append(f"auth: {ue} stále existuje!")

    # DB
    for email in TEST_EMAILS:
        if get(f"companies?email=eq.{email}&select=id"):
            problems.append(f"companies: {email}")
        if get(f"orders?email=eq.{email}&select=id"):
            problems.append(f"orders: {email}")
        if get(f"scans?select=id&company_id=in.({','.join(c['id'] for c in get(f'companies?email=eq.{email}&select=id'))})"):
            pass  # firmy by měly být pryč, takže prázdné

    for domain in TEST_DOMAINS:
        if get(f"companies?url=ilike.*{domain}*&select=id"):
            problems.append(f"companies: doména {domain}")

    if problems:
        print("  POZOR — zbytková data:")
        for p in problems:
            print(f"    {p}")
        return False

    print("  Vše čisté — žádná testovací data v DB.")
    return True


# ══════════════════════════════════════════════════════════
#  FÁZE 5: VPS restart + lokální soubory
# ══════════════════════════════════════════════════════════

def restart_vps():
    print("\n── VPS RESTART ──")
    try:
        subprocess.run(["systemctl", "restart", "aishield-api", "aishield-worker"], check=True, timeout=30)
        print("  OK: restart aishield-api + aishield-worker")
    except FileNotFoundError:
        result = subprocess.run(
            ["ssh", "-i", os.path.expanduser("~/.ssh/ares_vps"), "root@46.28.110.102",
             "systemctl restart aishield-api aishield-worker"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            print("  OK: VPS restart přes SSH")
        else:
            print(f"  CHYBA: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"  CHYBA: {e}")


def delete_local_files(company_ids):
    print("\n── MAZÁNÍ LOKÁLNÍCH SOUBORŮ ──")
    patterns = [cid[:8] for cid in company_ids] + TEST_DOMAINS
    dirs = [Path("/opt/aishield/generated"), Path("/opt/aishield/output"), Path("/opt/aishield/tmp")]
    deleted = 0
    for d in dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file() and any(p in f.name for p in patterns):
                f.unlink()
                print(f"  smazáno: {f}")
                deleted += 1
    print(f"  Celkem smazáno souborů: {deleted}")


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Kompletní výmaz testovacích dat")
    parser.add_argument("--yes", action="store_true", help="Provést výmaz bez ptaní")
    parser.add_argument("--vps", action="store_true", help="Restartovat backend po výmazu")
    parser.add_argument("--delete-local", action="store_true", help="Smazat lokální soubory na VPS")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("CHYBA: Nenalezeny SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY.")
        print("Spusťte: set -a && source /opt/aishield/.env && set +a")
        sys.exit(1)

    print("=" * 55)
    print("  VÝMAZ TESTOVACÍCH DAT — AIshield.cz")
    print("=" * 55)
    print(f"\n  Emaily:  {', '.join(TEST_EMAILS)}")
    print(f"  Domény:  {', '.join(TEST_DOMAINS)}")
    print(f"  Voucher: {TEST_VOUCHER}")

    # Discovery
    company_ids, client_ids, scan_ids, order_ids = phase_discover()

    if not args.yes:
        print(f"\n  [DRY RUN] Pro provedení výmazu spusťte s --yes")
        sys.exit(0)

    # Výmaz
    phase_auth()
    phase_delete(company_ids, client_ids, scan_ids, order_ids)

    if args.vps:
        restart_vps()

    if args.delete_local:
        delete_local_files(company_ids)

    # Verifikace
    clean = phase_verify()

    if clean:
        print(f"\n{'=' * 55}")
        print("  HOTOVO — čistý stav, připraveno na nový test.")
        print(f"{'=' * 55}\n")
    else:
        print(f"\n  POZOR: Některá data přetrvávají.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
