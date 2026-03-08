"""
AIshield.cz — Shoptet Addon: E-shop Scanner
Lehký scan e-shopu po vyplnění dotazníku.
Detekuje AI skripty na stránce (chatboty, analytika, widgety).
Výsledky se přidají ke stávajícím AI systémům ze source="scanner".
"""

import asyncio
import logging
from datetime import datetime, timezone

from backend.database import get_supabase

logger = logging.getLogger("shoptet.scanner")

# Známé AI skripty — pattern v HTML / script URL → metadata
AI_SCRIPT_SIGNATURES: list[dict] = [
    {
        "pattern": "smartsupp.com",
        "provider": "Smartsupp",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    {
        "pattern": "tidio.co",
        "provider": "Tidio",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    {
        "pattern": "livechatinc.com",
        "provider": "LiveChat",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    {
        "pattern": "zopim.com",
        "provider": "Zendesk Chat",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    {
        "pattern": "intercom.io",
        "provider": "Intercom",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    {
        "pattern": "drift.com",
        "provider": "Drift",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    {
        "pattern": "luigisbox.com",
        "provider": "Luigi's Box",
        "ai_type": "search",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI vyhledávání a doporučovací systém",
    },
    {
        "pattern": "data-luigisbox",
        "provider": "Luigi's Box",
        "ai_type": "search",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI vyhledávání a doporučovací systém",
    },
    {
        "pattern": "persoo.cz",
        "provider": "Persoo",
        "ai_type": "recommendation",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI personalizace a doporučovací systém",
    },
    {
        "pattern": "recombee.com",
        "provider": "Recombee",
        "ai_type": "recommendation",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI doporučovací systém produktů",
    },
    {
        "pattern": "algolia.net",
        "provider": "Algolia",
        "ai_type": "search",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI vyhledávání na e-shopu",
    },
    {
        "pattern": "doofinder.com",
        "provider": "Doofinder",
        "ai_type": "search",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI vyhledávání na e-shopu",
    },
    {
        "pattern": "rtbhouse.com",
        "provider": "RTB House",
        "ai_type": "other",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI retargeting a reklama",
    },
    {
        "pattern": "criteo.com",
        "provider": "Criteo",
        "ai_type": "other",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI retargeting a reklama",
    },
    {
        "pattern": "exponea.com",
        "provider": "Bloomreach (Exponea)",
        "ai_type": "recommendation",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI personalizace a zákaznická analytika",
    },
    {
        "pattern": "bloomreach.com",
        "provider": "Bloomreach",
        "ai_type": "recommendation",
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI personalizace a doporučovací systém",
    },
]


async def scan_eshop(installation_id: str) -> dict:
    """
    Provede lehký scan e-shopu a uloží nalezené AI systémy.
    Vrací souhrn: {"scanned": True, "found": [...], "error": None}
    """
    sb = get_supabase()
    result = {"scanned": False, "found": [], "error": None}

    try:
        # Načíst instalaci
        inst = sb.table("shoptet_installations").select(
            "id, eshop_url, status"
        ).eq("id", installation_id).execute()

        if not inst.data:
            result["error"] = "Instalace nenalezena"
            return result

        eshop_url = inst.data[0].get("eshop_url")
        if not eshop_url:
            result["error"] = "Chybí URL e-shopu"
            return result

        # Scan stránky
        logger.info(f"Scan e-shopu: {eshop_url} (installation={installation_id})")
        html = await _fetch_page_html(eshop_url)

        if not html:
            result["error"] = "Nepodařilo se načíst stránku"
            # I tak aktualizovat scan_completed_at
            sb.table("shoptet_installations").update({
                "scan_completed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", installation_id).execute()
            result["scanned"] = True
            return result

        # Detekce AI signatur
        html_lower = html.lower()
        found_providers = set()
        found_systems = []

        for sig in AI_SCRIPT_SIGNATURES:
            if sig["pattern"].lower() in html_lower and sig["provider"] not in found_providers:
                found_providers.add(sig["provider"])
                found_systems.append(sig)

        # Smazat staré scanner záznamy (idempotence)
        sb.table("shoptet_ai_systems").delete().eq(
            "installation_id", installation_id,
        ).eq("source", "scanner").execute()

        # Uložit nalezené
        if found_systems:
            records = []
            for s in found_systems:
                records.append({
                    "installation_id": installation_id,
                    "source": "scanner",
                    "provider": s["provider"],
                    "ai_type": s["ai_type"],
                    "ai_act_article": s["ai_act_article"],
                    "risk_level": s["risk_level"],
                    "confidence": "probable",
                    "is_active": True,
                    "details": {"description_cs": s["description_cs"]},
                })
            sb.table("shoptet_ai_systems").insert(records).execute()

        # Aktualizovat timestamp
        sb.table("shoptet_installations").update({
            "scan_completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", installation_id).execute()

        result["scanned"] = True
        result["found"] = [s["provider"] for s in found_systems]
        logger.info(
            f"Scan hotov: {eshop_url} → {len(found_systems)} AI systémů nalezeno"
        )

    except Exception as e:
        logger.error(f"Scan selhal pro {installation_id}: {e}")
        result["error"] = str(e)
        # Pokusit se alespoň zapsat timestamp
        try:
            sb.table("shoptet_installations").update({
                "scan_completed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", installation_id).execute()
        except Exception:
            pass

    return result


async def _fetch_page_html(url: str) -> str | None:
    """Stáhne HTML stránky. Zkusí WebScanner (Playwright), fallback na httpx."""
    # Priorita: WebScanner (má Playwright, JS rendering)
    try:
        from backend.scanner.web_scanner import WebScanner
        scanner = WebScanner(
            use_proxy=False,
            device_type="desktop",
            timeout_ms=30_000,
            wait_after_load_ms=3_000,
        )
        page = await scanner.scan(url)
        if page.html and len(page.html) > 500:
            return page.html
    except Exception as e:
        logger.warning(f"WebScanner fallback: {e}")

    # Fallback: jednoduchý HTTP request (bez JS)
    try:
        import httpx
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "AIshield/1.0 (AI Act compliance scanner)"},
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.text) > 500:
                return resp.text
    except Exception as e:
        logger.warning(f"httpx fallback selhal: {e}")

    return None
