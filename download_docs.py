"""Download generated documents from Supabase Storage to local folders."""
import requests
import os
import time

SKEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJzeHdxY3JrdHRsZm5xYmpncGdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDU3MTMxNywiZXhwIjoyMDg2MTQ3MzE3fQ.dxjnj7uQ3-uRRmqFa-MXnM6t3xL-Fci8A-xTqOvy-MU"
BASE_URL = "https://rsxwqcrkttlfnqbjgpgc.supabase.co"
HEADERS = {"apikey": SKEY, "Authorization": f"Bearer {SKEY}"}

CLIENT_MAP = {
    "fff6e7b0-c5e5-44f1-b1ea-7b430e493650": "P01_Kadrenictvi_Martina_BASIC",
    "c977c7bc-6c33-47b8-9ece-30525cf02d8c": "P02_NeuralForge_ENTERPRISE",
    "0a2b1f72-10ac-4f9d-a1d7-017ed11043db": "P03_EkoUcto_ENTERPRISE",
    "402d5fc5-1ec9-4125-bc98-36334d2fc03d": "P04_BioKrasa_PRO",
    "2937b8a8-566f-4e98-a2d6-fba484bd491b": "P05_MediCare_Plus_ENTERPRISE",
    "3b0a69f0-fd3a-4b3e-a036-9c12945fc686": "P06_AK_Novotny_PRO",
    "570816eb-2172-4169-bc4a-d006bc5f607b": "P07_U_Stare_Lipy_BASIC",
    "02c593ef-d664-4e2b-ac66-2cea283390ee": "P08_METRO_Reality_PRO",
    "67328330-b107-4115-ab6a-e64dbf2706ea": "P09_CzechParts_Manufacturing_ENTERPRISE",
    "a70a2702-2b91-4fd2-8b24-15b54675ac90": "P10_Farma_Zeleny_Kopec_BASIC",
}

LOCAL_BASE = "testovaci_dokumenty"
total_ok = 0
total_fail = 0
total_skip = 0

for client_id, folder in CLIENT_MAP.items():
    print(f"\n{'='*60}")
    print(f"  {folder}  (client: {client_id[:8]}...)")
    print(f"{'='*60}")

    r = requests.post(
        f"{BASE_URL}/storage/v1/object/list/documents",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"prefix": client_id, "limit": 50},
        timeout=15,
    )
    files = r.json()

    latest_files = {}
    for f in files:
        name = f["name"]
        parts = name.rsplit("_", 2)
        if len(parts) >= 3:
            template_type = name.rsplit("_", 2)[0]
        else:
            template_type = name
        if template_type not in latest_files or name > latest_files[template_type]:
            latest_files[template_type] = name

    dest_dir = os.path.join(LOCAL_BASE, folder)
    os.makedirs(dest_dir, exist_ok=True)

    for template_type, filename in sorted(latest_files.items()):
        local_path = os.path.join(dest_dir, filename)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
            size_kb = os.path.getsize(local_path) / 1024
            print(f"  SKIP {filename} (already {size_kb:.1f} KB)")
            total_skip += 1
            continue

        storage_path = f"{client_id}/{filename}"
        url = f"{BASE_URL}/storage/v1/object/documents/{storage_path}"

        for attempt in range(3):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                if resp.status_code == 200:
                    with open(local_path, "wb") as fout:
                        fout.write(resp.content)
                    size_kb = len(resp.content) / 1024
                    print(f"  OK {filename} ({size_kb:.1f} KB)")
                    total_ok += 1
                    break
                else:
                    print(f"  FAIL {filename} -- HTTP {resp.status_code}")
                    total_fail += 1
                    break
            except Exception as e:
                if attempt < 2:
                    print(f"  RETRY {filename} (attempt {attempt+2}/3)")
                    time.sleep(2)
                else:
                    print(f"  FAIL {filename} -- timeout")
                    total_fail += 1

print(f"\n{'='*60}")
print(f"Hotovo: {total_ok} stazeno, {total_skip} preskoceno, {total_fail} selhalo")
print(f"{'='*60}")
