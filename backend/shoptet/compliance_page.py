"""
AIshield.cz — Shoptet Addon: Compliance stránka
Generuje HTML compliance stránku a publikuje ji na eshop přes Shoptet Pages API.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.database import get_supabase
from backend.shoptet.client import (
    create_page,
    get_api_token_for_installation,
    update_page,
)

logger = logging.getLogger("shoptet.compliance_page")

COMPLIANCE_PAGE_TITLE = "Informace o využití AI — AI Act"
COMPLIANCE_PAGE_SLUG = "ai-compliance"


def _generate_compliance_html(eshop_name: str, ai_systems: list[dict]) -> str:
    """
    Generuje HTML obsah compliance stránky.
    Stránka informuje zákazníky o používaných AI systémech dle Article 50 AI Act.
    """
    # Rozdělit na Art 50 (vyžaduje disclosure) a ostatní
    art50_systems = [s for s in ai_systems if s.get("ai_act_article") == "art50"]
    other_systems = [s for s in ai_systems if s.get("ai_act_article") != "art50"]

    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    # Art 50 tabulka
    art50_rows = ""
    for s in art50_systems:
        details = s.get("details", {})
        art50_rows += f"""
        <tr>
            <td>{_escape(s.get('provider', 'N/A'))}</td>
            <td>{_escape(details.get('description_cs', s.get('ai_type', '')))}</td>
            <td>Omezené riziko (Article 50)</td>
        </tr>"""

    # Ostatní AI tabulka
    other_rows = ""
    for s in other_systems:
        details = s.get("details", {})
        other_rows += f"""
        <tr>
            <td>{_escape(s.get('provider', 'N/A'))}</td>
            <td>{_escape(details.get('description_cs', s.get('ai_type', '')))}</td>
            <td>Minimální riziko (Article 4)</td>
        </tr>"""

    html = f"""<div class="ai-compliance-page" style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: inherit;">
    <h1>Informace o využití umělé inteligence</h1>
    <p><strong>{_escape(eshop_name)}</strong> v souladu s Nařízením EU 2024/1689
    (AI Act) transparentně informuje o AI systémech používaných v tomto e-shopu.</p>

    <p><em>Poslední aktualizace: {now}</em></p>
"""

    if art50_systems:
        html += f"""
    <h2>AI systémy s povinností transparence (Article 50)</h2>
    <p>Následující AI systémy komunikují přímo se zákazníky nebo generují obsah,
    a proto podléhají povinnosti informovat uživatele dle Article 50 AI Act
    (účinnost od 2. srpna 2026):</p>

    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
        <thead>
            <tr style="background: #f5f5f5;">
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Poskytovatel</th>
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Účel</th>
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Kategorie</th>
            </tr>
        </thead>
        <tbody>{art50_rows}
        </tbody>
    </table>
"""

    if other_systems:
        html += f"""
    <h2>Další AI systémy (evidenční povinnost)</h2>
    <p>Následující AI systémy jsou evidovány dle Article 4 AI Act (AI Literacy,
    účinnost od 2. února 2025). Nepodléhají povinnosti přímé informace zákazníkům,
    ale uvádíme je pro úplnou transparenci:</p>

    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
        <thead>
            <tr style="background: #f5f5f5;">
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Poskytovatel</th>
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Účel</th>
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Kategorie</th>
            </tr>
        </thead>
        <tbody>{other_rows}
        </tbody>
    </table>
"""

    if not art50_systems and not other_systems:
        html += """
    <p>V tomto e-shopu aktuálně nebyly identifikovány žádné AI systémy
    podléhající regulaci AI Act.</p>
"""

    html += f"""
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="font-size: 0.85em; color: #666;">
        Tato stránka slouží k informování zákazníků v souladu s Nařízením EU 2024/1689 (AI Act).
        Informace jsou poskytovány na základě sebehodnocení provozovatele e-shopu
        a nepředstavují právní poradenství.
        <br><br>
        Generováno systémem <a href="https://aishield.cz" target="_blank"
        rel="noopener">AIshield.cz</a> — AI Act compliance pro e-shopy.
    </p>
</div>"""

    return html


def _escape(text: str) -> str:
    """Základní HTML escape."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


async def publish_compliance_page(installation_id: str) -> dict:
    """
    Hlavní funkce — vygeneruje a publikuje compliance stránku:
    1. Načte instalaci a AI systémy z DB
    2. Vygeneruje HTML
    3. Publikuje přes Shoptet Pages API (create nebo update)
    4. Uloží do shoptet_compliance_pages
    """
    sb = get_supabase()

    # Načíst instalaci
    inst = sb.table("shoptet_installations").select("*").eq(
        "id", installation_id,
    ).single().execute()
    installation = inst.data

    # Načíst AI systémy
    systems = sb.table("shoptet_ai_systems").select("*").eq(
        "installation_id", installation_id,
    ).eq("is_active", True).execute()
    ai_systems = systems.data or []

    eshop_name = installation.get("eshop_name", "Tento e-shop")

    # Generovat HTML
    html_content = _generate_compliance_html(eshop_name, ai_systems)

    # Získat API token
    encrypted_token = installation.get("oauth_access_token")
    if not encrypted_token:
        raise ValueError("Instalace nemá OAuth token")

    api_token = await get_api_token_for_installation(encrypted_token)

    # Zkontrolovat, jestli stránka už existuje
    existing = sb.table("shoptet_compliance_pages").select("*").eq(
        "installation_id", installation_id,
    ).execute()

    shoptet_page_id: Optional[int] = None

    if existing.data:
        # Update existující stránky
        page_record = existing.data[0]
        shoptet_page_id = page_record.get("shoptet_page_id")
        if shoptet_page_id:
            await update_page(api_token, shoptet_page_id, html_content)
            logger.info(f"Compliance stránka aktualizována: page_id={shoptet_page_id}")
        else:
            # Stará stránka bez page_id — vytvořit novou
            result = await create_page(api_token, COMPLIANCE_PAGE_TITLE, COMPLIANCE_PAGE_SLUG, html_content)
            shoptet_page_id = result.get("data", {}).get("id")
            logger.info(f"Compliance stránka vytvořena: page_id={shoptet_page_id}")

        # Update DB záznam
        sb.table("shoptet_compliance_pages").update({
            "html_content": html_content,
            "shoptet_page_id": shoptet_page_id,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }).eq("installation_id", installation_id).execute()
    else:
        # Vytvořit novou stránku
        result = await create_page(api_token, COMPLIANCE_PAGE_TITLE, COMPLIANCE_PAGE_SLUG, html_content)
        shoptet_page_id = result.get("data", {}).get("id")
        logger.info(f"Compliance stránka vytvořena: page_id={shoptet_page_id}")

        sb.table("shoptet_compliance_pages").insert({
            "installation_id": installation_id,
            "html_content": html_content,
            "shoptet_page_id": shoptet_page_id,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "page_slug": COMPLIANCE_PAGE_SLUG,
        }).execute()

    # Aktualizovat compliance skóre (+30 za stránku)
    return {
        "status": "published",
        "shoptet_page_id": shoptet_page_id,
        "slug": COMPLIANCE_PAGE_SLUG,
        "ai_systems_count": len(ai_systems),
    }
