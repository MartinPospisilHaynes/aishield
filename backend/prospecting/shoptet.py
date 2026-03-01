"""
AIshield.cz — Shoptet Katalog Scraper (DEPRECATED)
===================================================
⚠️ Shoptet zrušil katalog obchodů (shoptet.cz/katalog-obchodu/ vrací 404).
Tento modul je zachován jako stub pro zpětnou kompatibilitu.
Data e-shopů získáváme z Heureka (obchody.heureka.cz) přes Playwright.
Viz: backend/prospecting/heureka.py

Datum deprecace: 2025-06-28
"""

import asyncio
from dataclasses import dataclass


@dataclass
class ShoptetShop:
    name: str
    url: str
    category: str = ""
    description: str = ""


# Shoptet katalog odstraněn — vrací 404
SHOPTET_CATEGORIES = []
KATALOG_URL = "https://www.shoptet.cz/katalog-obchodu"  # 404


async def scrape_shoptet_category(
    category: str = "",
    page: int = 1,
    max_pages: int = 10,
) -> list[ShoptetShop]:
    """DEPRECATED — Shoptet katalog zrušen. Vrací prázdný seznam."""
    print("[Shoptet] ⚠️ Katalog zrušen (404). Použij Heureka scraper.")
    return []


async def scrape_all_categories(**kwargs) -> list[ShoptetShop]:
    """DEPRECATED — Shoptet katalog zrušen."""
    print("[Shoptet] ⚠️ Katalog zrušen (404). Použij Heureka scraper.")
    return []


async def import_shoptet_to_db(**kwargs) -> dict:
    """DEPRECATED — Shoptet katalog zrušen."""
    print("[Shoptet] ⚠️ Katalog zrušen (404). Použij Heureka scraper.")
    return {"scraped": 0, "new": 0, "skipped_existing": 0, "errors": 0, "deprecated": True}
