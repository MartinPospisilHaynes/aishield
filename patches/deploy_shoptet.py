"""
AIshield.cz — Shoptet Addon: Deploy patch na VPS
Nahraje backend/shoptet/ modul na VPS a restartuje službu.
Spuštění: python3 patches/deploy_shoptet.py
"""

import subprocess
import sys
import os

VPS = "root@46.28.110.102"
SSH_KEY = os.path.expanduser("~/.ssh/ares_vps")
LOCAL_DIR = os.path.expanduser("~/Projects/aishield")
REMOTE_DIR = "/opt/aishield"

def ssh(cmd: str, check: bool = True) -> str:
    """Spustí příkaz na VPS přes SSH."""
    result = subprocess.run(
        ["/usr/bin/ssh", "-i", SSH_KEY, VPS, cmd],
        capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        print(f"  CHYBA: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()

def scp(local: str, remote: str) -> None:
    """Nahraje soubor na VPS."""
    result = subprocess.run(
        ["/usr/bin/scp", "-i", SSH_KEY, local, f"{VPS}:{remote}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  SCP CHYBA: {result.stderr.strip()}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("  DEPLOY: Shoptet Addon → VPS")
    print("=" * 50)

    # 1. Vytvořit adresář na VPS
    print("\n[1/5] Vytvářím adresář na VPS...")
    ssh(f"mkdir -p {REMOTE_DIR}/backend/shoptet")
    print("  OK")

    # 2. Nahrát soubory
    print("\n[2/5] Nahrávám backend/shoptet/ moduly...")
    shoptet_dir = os.path.join(LOCAL_DIR, "backend", "shoptet")
    files = [f for f in os.listdir(shoptet_dir) if f.endswith(".py")]
    for fname in sorted(files):
        local_path = os.path.join(shoptet_dir, fname)
        remote_path = f"{REMOTE_DIR}/backend/shoptet/{fname}"
        scp(local_path, remote_path)
        print(f"  {fname}")
    print(f"  Nahráno {len(files)} souborů")

    # 3. Nahrát testy
    print("\n[3/5] Nahrávám testy...")
    scp(
        os.path.join(LOCAL_DIR, "scripts", "test_shoptet.py"),
        f"{REMOTE_DIR}/scripts/test_shoptet.py",
    )
    print("  test_shoptet.py")

    # 4. Nahrát migraci
    print("\n[4/5] Nahrávám DB migraci...")
    scp(
        os.path.join(LOCAL_DIR, "database", "migrations", "010_shoptet_addon.sql"),
        f"{REMOTE_DIR}/database/migrations/010_shoptet_addon.sql",
    )
    print("  010_shoptet_addon.sql")

    # 5. Patch main.py — přidat Shoptet router (idempotentní)
    print("\n[5/5] Patchuji main.py na VPS...")
    patch_script = '''
import os

MAIN_PY = "/opt/aishield/backend/main.py"
with open(MAIN_PY) as f:
    content = f.read()

# Import
IMPORT_LINE = "from backend.shoptet.router import router as shoptet_router"
if IMPORT_LINE not in content:
    # Přidat za poslední import
    anchor = "from backend.api.pioneer import router as pioneer_router"
    assert anchor in content, f"Guard failed — {anchor!r} not found"
    content = content.replace(anchor, anchor + "\\n" + IMPORT_LINE)
    print("  Import přidán")
else:
    print("  Import již existuje")

# Router registrace
ROUTER_LINE = 'app.include_router(shoptet_router, prefix="/shoptet", tags=["Shoptet"])'
if ROUTER_LINE not in content:
    anchor2 = 'app.include_router(pioneer_router, prefix="/api/pioneer", tags=["Pioneer"])'
    assert anchor2 in content, f"Guard failed — {anchor2!r} not found"
    content = content.replace(anchor2, anchor2 + "\\n" + ROUTER_LINE)
    print("  Router registrace přidána")
else:
    print("  Router registrace již existuje")

# CORS — Shoptet admin iframe
CORS_ORIGIN = '"https://admin.myshoptet.com"'
if CORS_ORIGIN not in content:
    cors_anchor = '"https://www.aishield.cz"'
    assert cors_anchor in content, f"Guard failed — {cors_anchor!r} not found"
    content = content.replace(
        cors_anchor + ",",
        cors_anchor + ',\\n        ' + CORS_ORIGIN + ',  # Shoptet admin iframe'
    )
    print("  CORS origin přidán")
else:
    print("  CORS origin již existuje")

with open(MAIN_PY, "w") as f:
    f.write(content)
print("  main.py OK")
'''

    # Uložit patch skript na VPS a spustit
    ssh(f"cat > /tmp/patch_shoptet_main.py << 'PYEOF'\n{patch_script}\nPYEOF")
    output = ssh(f"cd {REMOTE_DIR} && {REMOTE_DIR}/venv/bin/python3 /tmp/patch_shoptet_main.py")
    print(output)

    # 6. Spustit testy na VPS
    print("\n[BONUS] Spouštím testy na VPS...")
    test_output = ssh(
        f"cd {REMOTE_DIR} && {REMOTE_DIR}/venv/bin/python3 scripts/test_shoptet.py",
        check=False,
    )
    print(test_output)

    # 7. Restart služby
    print("\n[RESTART] Restartuji aishield-api službu...")
    ssh("systemctl restart aishield-api")
    import time
    time.sleep(2)
    status = ssh("systemctl is-active aishield-api", check=False)
    print(f"  Status: {status}")

    if status == "active":
        print("\n" + "=" * 50)
        print("  DEPLOY ÚSPĚŠNÝ")
        print("=" * 50)
    else:
        print("\n  VAROVÁNÍ: Služba neběží! Zkontroluj logy:")
        print("  journalctl -u aishield-api --no-pager -n 20")
        sys.exit(1)

if __name__ == "__main__":
    main()
