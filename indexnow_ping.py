#!/usr/bin/env python3
"""
IndexNow ping — spouští se po každém novém blog postu (cron + auto_blog).
Odešle klíčové URL do Bing, Yandex a Naver IndexNow API.
"""
import json
import urllib.request
import sys
from datetime import datetime

KEY = "aishield2026czaiact"
HOST = "aishield.cz"
KEY_URL = f"https://{HOST}/{KEY}.txt"

# Statické klíčové URL (vždy)
BASE_URLS = [
    f"https://{HOST}/",
    f"https://{HOST}/scan",
    f"https://{HOST}/pricing",
    f"https://{HOST}/blog",
    f"https://{HOST}/faq",
    f"https://{HOST}/ai-act/co-je-ai-act",
    f"https://{HOST}/ai-act/e-shopy",
    f"https://{HOST}/ai-act/pokuty",
    f"https://{HOST}/ai-act/checklist",
    f"https://{HOST}/ai-act/clanek-50",
    f"https://{HOST}/ai-act/rizikove-kategorie",
]

ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://yandex.com/indexnow",
    "https://searchadvisor.naver.com/indexnow",
]

def ping(urls: list[str]):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_URL,
        "urlList": urls,
    }
    data = json.dumps(payload).encode()
    results = []
    for endpoint in ENDPOINTS:
        try:
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            name = endpoint.split("/")[2]
            results.append(f"  {name}: HTTP {resp.status}")
        except Exception as e:
            name = endpoint.split("/")[2]
            results.append(f"  {name}: CHYBA — {e}")
    return results

if __name__ == "__main__":
    # Volitelně přijímá extra URL jako argumenty
    extra = sys.argv[1:] if len(sys.argv) > 1 else []
    urls = list(set(BASE_URLS + extra))
    
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] IndexNow ping — {len(urls)} URL")
    for line in ping(urls):
        print(line)
    print()
