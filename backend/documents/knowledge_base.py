"""
AIshield Knowledge Base — Statická fakta o AI nástrojích.

Hybridní přístup:
  1. Známý nástroj (bublina v dotazníku) → předepsaný text z KB
  2. Neznámý nástroj ("Jiné") → LLM generuje text

Pokrývá ~45 nástrojů z předdefinovaných bublin dotazníku.
"""
from __future__ import annotations

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════
# 0. METADATA & PRÁVNÍ OCHRANA
# ════════════════════════════════════════════════════════════════════

KB_VERSION_DATE = "2026-02-24"  # Datum poslední aktualizace KB

KB_DISCLAIMER_CS = (
    "Údaje o poskytovatelích AI nástrojů v této znalostní bázi vycházejí z veřejně "
    "dostupných informací na webových stránkách příslušných poskytovatelů a z jejich "
    "oficiální dokumentace ke dni {kb_date}. Poskytovatelé mohou své podmínky, "
    "certifikace, umístění datových center a smluvní dokumenty (včetně DPA) kdykoli "
    "změnit bez předchozího upozornění. AIshield provádí pravidelnou revizi těchto "
    "údajů; v případě zjištění změny na straně poskytovatele si vyhrazujeme lhůtu "
    "30 kalendářních dnů na provedení aktualizace. Klient je povinen si klíčové údaje "
    "(zejména dostupnost DPA, umístění dat a certifikace) ověřit přímo u svého "
    "poskytovatele v rámci dodavatelského auditu. "
    "AIshield poskytuje informační a analytickou službu — nenahrazuje právní poradenství."
)

KB_SOURCE_NOTE_CS = (
    "Zdroj dat: veřejně dostupné informace z webových stránek poskytovatelů, "
    "oficiální bezpečnostní dokumentace, trust centra a veřejné compliance stránky. "
    "Stav ke dni: {kb_date}."
)

KB_VENDOR_FOOTER_CS = (
    "<p style=\"font-size:0.85em;color:#666;margin-top:1.5em;border-top:1px solid #ddd;padding-top:0.8em\">"
    "<strong>Upozornění:</strong> Údaje o poskytovatelích AI nástrojů vycházejí z veřejně dostupných "
    "informací ke dni {kb_date}. Poskytovatelé mohou své podmínky, certifikace a umístění datových center "
    "kdykoliv změnit. V případě zjištění změny si AIshield vyhrazuje lhůtu 30 kalendářních dnů na aktualizaci. "
    "Doporučujeme klíčové údaje ověřit přímo u příslušného poskytovatele v rámci dodavatelského auditu. "
    "AIshield poskytuje informační a analytickou službu — nenahrazuje právní poradenství.</p>"
)


def get_disclaimer(template: str = None) -> str:
    """Vrátí disclaimer s doplněným datem."""
    tmpl = template or KB_DISCLAIMER_CS
    return tmpl.format(kb_date=KB_VERSION_DATE)


def get_vendor_footer() -> str:
    """Vrátí HTML footer s disclaimerem pro vložení pod vendor assessment a další sekce."""
    return KB_VENDOR_FOOTER_CS.format(kb_date=KB_VERSION_DATE)


# ════════════════════════════════════════════════════════════════════
# 1. TOOL KNOWLEDGE BASE — fakta o konkrétních AI nástrojích
# ════════════════════════════════════════════════════════════════════
#
# Pole v každém záznamu:
#   provider        — právní název poskytovatele
#   provider_hq     — sídlo (město, stát)
#   website         — URL
#   data_regions    — kde se data zpracovávají
#   eu_based        — je poskytovatel v EU/EEA?
#   dpa_available   — nabízí DPA?
#   dpa_note        — poznámka k DPA
#   gdpr_mechanisms — SCC, DPA, BCR, …
#   certifications  — SOC 2, ISO 27001, …
#   description_cs  — stručný popis (česky)
#   key_risks_cs    — hlavní rizika (česky)
#   measures_cs     — doporučená opatření (česky)
#   monitoring_kpis_cs  — co monitorovat
#   training_focus_cs   — na co školit zaměstnance
#   transparency_cs     — vzorový transparenční text
# ════════════════════════════════════════════════════════════════════

TOOL_KB: dict[str, dict] = {

    # ══════════════ VELKÉ LLM PLATFORMY ══════════════

    "ChatGPT": {
        "provider": "OpenAI, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://openai.com",
        "data_regions": ["US (Microsoft Azure)", "EU (volitelně pro API/Enterprise)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "openai.com/policies/data-processing-addendum",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "Generativní AI chatbot a LLM platforma pro textovou komunikaci, analýzu a generování obsahu.",
        "key_risks_cs": [
            "Hallucination — generování nepravdivých informací",
            "Únik citlivých dat přes prompt",
            "Závislost na externím poskytovateli (vendor lock-in)",
        ],
        "measures_cs": [
            "Zakázat vkládání osobních údajů a obchodních tajemství do promptů",
            "Aktivovat opt-out z trénování na firemních datech (Settings → Data Controls)",
            "Vždy ověřovat výstupy AI — nikdy nepublikovat bez lidské kontroly",
            "Uzavřít DPA s OpenAI před zpracováním osobních údajů",
        ],
        "monitoring_kpis_cs": [
            "Přesnost odpovědí (% fakticky správných)",
            "Počet incidentů s hallucination za měsíc",
            "Počet případů vložení citlivých dat do promptu",
        ],
        "training_focus_cs": [
            "Správná formulace promptů bez citlivých dat",
            "Rozpoznání hallucination a ověřování výstupů",
            "Firemní pravidla pro AI dle interní politiky",
        ],
        "transparency_cs": "Tento obsah byl vytvořen s pomocí AI (ChatGPT). Výstupy byly zkontrolovány člověkem.",
    },

    "Claude": {
        "provider": "Anthropic, PBC",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://anthropic.com",
        "data_regions": ["US (Google Cloud Platform)", "EU (volitelně pro API)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná na anthropic.com/policies",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "Pokročilý AI asistent s důrazem na bezpečnost a přesnost odpovědí.",
        "key_risks_cs": [
            "Hallucination — přesvědčivě znějící nepravdivé informace",
            "Únik dat přes konverzaci",
            "Závislost na externím US poskytovateli",
        ],
        "measures_cs": [
            "Nesdílet osobní údaje ani obchodní tajemství v konverzacích",
            "Ověřovat faktické výstupy před použitím",
            "Uzavřít DPA s Anthropic pro firemní použití",
        ],
        "monitoring_kpis_cs": [
            "Přesnost a relevance odpovědí",
            "Počet eskalací na člověka",
        ],
        "training_focus_cs": [
            "Kritické hodnocení AI výstupů",
            "Bezpečné zacházení s firemními daty",
        ],
        "transparency_cs": "Tento obsah byl vytvořen s pomocí AI (Claude). Výstupy byly zkontrolovány člověkem.",
    },

    "Gemini": {
        "provider": "Google LLC (Alphabet Inc.)",
        "provider_hq": "Mountain View, CA, USA",
        "website": "https://gemini.google.com",
        "data_regions": ["Google Cloud (globální)", "EU regiony dostupné"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Cloud Data Processing Addendum (cloud.google.com/terms/data-processing-addendum)",
        "gdpr_mechanisms": ["SCC", "BCR", "DPA"],
        "certifications": ["ISO 27001", "SOC 2", "SOC 3"],
        "opt_out_training": True,
        "description_cs": "Multimodální AI model Google pro text, obrázky, kód a analýzu dat.",
        "key_risks_cs": [
            "Hallucination",
            "Zpracování dat v infrastruktuře Google — široký přístup k datům",
            "Integrace s Google Workspace — riziko rozšíření přístupu AI",
        ],
        "measures_cs": [
            "Konfigurovat zpracování dat výhradně v EU regionech",
            "Aktivovat opt-out z trénování modelu na firemních datech",
            "Uzavřít Google Cloud DPA",
            "Omezit integraci s citlivými Google Workspace dokumenty",
        ],
        "monitoring_kpis_cs": [
            "Přesnost generovaných odpovědí",
            "Využití API (počet volání, náklady)",
        ],
        "training_focus_cs": [
            "Bezpečné sdílení firemních dat s Google AI",
            "Nastavení soukromí v Google Workspace",
        ],
        "transparency_cs": "Tento obsah byl vytvořen s pomocí AI (Google Gemini). Výstupy byly ověřeny člověkem.",
    },

    "Copilot": {
        "provider": "Microsoft Corporation",
        "provider_hq": "Redmond, WA, USA",
        "website": "https://copilot.microsoft.com",
        "data_regions": ["Microsoft Azure (US, EU)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Microsoft Products DPA (microsoft.com/licensing/docs)",
        "gdpr_mechanisms": ["SCC", "DPA", "EU Data Boundary"],
        "certifications": ["ISO 27001", "SOC 2 Type II", "SOC 3"],
        "opt_out_training": True,
        "description_cs": "AI asistent integrovaný do Microsoft 365, Windows a Edge prohlížeče.",
        "key_risks_cs": [
            "Přístup AI k firemním souborům v Microsoft 365",
            "Sdílení kontextu mezi aplikacemi (Outlook, Teams, Word)",
            "Hallucination v generovaných dokumentech",
        ],
        "measures_cs": [
            "Nastavit EU Data Boundary pro zpracování v EU",
            "Konfigurovat oprávnění — omezit přístup Copilota k citlivým souborům",
            "Uzavřít Microsoft DPA",
            "Kontrolovat výstupy Copilota před odesláním",
        ],
        "monitoring_kpis_cs": [
            "Počet dokumentů generovaných Copilotem",
            "Přesnost návrhů v Office aplikacích",
        ],
        "training_focus_cs": [
            "Správné použití Copilota v prostředí Microsoft 365",
            "Nastavení soukromí a oprávnění",
        ],
        "transparency_cs": "Tento obsah byl vytvořen s pomocí AI (Microsoft Copilot).",
    },

    "Perplexity": {
        "provider": "Perplexity AI, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://perplexity.ai",
        "data_regions": ["US"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro Enterprise plán",
        "gdpr_mechanisms": ["SCC"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI vyhledávač kombinující webové vyhledávání s LLM odpovědí a citacemi zdrojů.",
        "key_risks_cs": [
            "Citace neověřených nebo zastaralých zdrojů",
            "Hallucination v syntéze informací",
        ],
        "measures_cs": [
            "Ověřovat citované zdroje před použitím",
            "Nesdílet citlivá data v dotazech",
        ],
        "monitoring_kpis_cs": ["Přesnost citací a zdrojů"],
        "training_focus_cs": ["Ověřování zdrojů AI odpovědí"],
        "transparency_cs": "Tento obsah byl vyhledán a shrnut s pomocí AI (Perplexity).",
    },

    # ══════════════ KÓD / VÝVOJOVÉ NÁSTROJE ══════════════

    "GitHub Copilot": {
        "provider": "GitHub, Inc. (Microsoft)",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://github.com/features/copilot",
        "data_regions": ["Microsoft Azure (US, EU)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "GitHub Customer Agreement + DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI nástroj pro programátory — navrhuje kód, dokončuje funkce a generuje testy.",
        "key_risks_cs": [
            "Vložení zranitelného kódu do produkce",
            "Únik proprietárního kódu přes suggestions",
            "Licenční rizika — návrhy mohou obsahovat open-source kód",
        ],
        "measures_cs": [
            "Povinný code review všech AI-generovaných částí",
            "Aktivovat opt-out z trénování na firemním kódu",
            "Provádět bezpečnostní sken AI-generovaného kódu",
        ],
        "monitoring_kpis_cs": [
            "% AI kódu přijatého vs. upraveného při code review",
            "Počet bezpečnostních nálezů v AI kódu",
        ],
        "training_focus_cs": [
            "Bezpečný code review AI-generovaného kódu",
            "Licenční rizika open-source návrhů",
        ],
        "transparency_cs": "Části kódu byly vytvořeny s asistencí AI (GitHub Copilot) a prošly lidskou kontrolou.",
    },

    "Cursor": {
        "provider": "Anysphere, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://cursor.com",
        "data_regions": ["US"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro Business plán",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI-enhanced kódový editor postavený na VS Code s integrovanými LLM modely.",
        "key_risks_cs": [
            "Odesílání zdrojového kódu na externí servery",
            "Vložení zranitelného kódu",
        ],
        "measures_cs": [
            "Aktivovat Privacy Mode — data se nepoužívají k trénování",
            "Code review všech AI návrhů",
        ],
        "monitoring_kpis_cs": ["% AI kódu upraveného při review"],
        "training_focus_cs": ["Bezpečné použití AI v IDE"],
        "transparency_cs": "Kód vytvořen s asistencí AI (Cursor).",
    },

    "Windsurf": {
        "provider": "Codeium, Inc. (dříve Exafunction, Inc.)",
        "provider_hq": "Mountain View, CA, USA",
        "website": "https://windsurf.com",
        "former_name": "Codeium (přejmenován na Windsurf 2024)",
        "data_regions": ["US"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro Enterprise",
        "gdpr_mechanisms": ["SCC"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI coding IDE (dříve Codeium, od 2024 Windsurf) s autocomplete a chat funkcí pro vývojáře.",
        "key_risks_cs": ["Únik kódu přes cloud zpracování", "Zranitelnosti v návrzích"],
        "measures_cs": ["Code review AI návrhů", "Enterprise self-hosted varianta pro citlivé projekty"],
        "monitoring_kpis_cs": ["Kvalita AI návrhů kódu"],
        "training_focus_cs": ["Bezpečný AI-asistovaný vývoj"],
        "transparency_cs": "Kód vytvořen s asistencí AI (Windsurf).",
    },

    "Amazon Q Developer": {
        "provider": "Amazon Web Services, Inc.",
        "provider_hq": "Seattle, WA, USA",
        "website": "https://aws.amazon.com/q/developer",
        "data_regions": ["AWS (US, EU)"],
        "former_name": "Amazon CodeWhisperer (přejmenován duben 2024)",
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "AWS DPA (d1.awsstatic.com/legal/aws-dpa)",
        "gdpr_mechanisms": ["SCC", "BCR", "DPA"],
        "certifications": ["ISO 27001", "SOC 2", "SOC 3"],
        "opt_out_training": True,
        "description_cs": "AI asistent pro psaní kódu od AWS (dříve CodeWhisperer, od 2024 Amazon Q Developer), integrovaný do IDE a AWS konzole.",
        "key_risks_cs": ["Licenční rizika open-source návrhů", "Vendor lock-in na AWS ekosystém"],
        "measures_cs": ["Aktivovat reference tracking pro licence", "Code review"],
        "monitoring_kpis_cs": ["Kvalita a bezpečnost AI kódu"],
        "training_focus_cs": ["Bezpečné použití AI kodéru v AWS"],
        "transparency_cs": "Kód vytvořen s asistencí AI (Amazon Q Developer).",
    },

    # ══════════════ GENEROVÁNÍ OBSAHU / OBRÁZKŮ ══════════════

    "DALL-E": {
        "provider": "OpenAI, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://openai.com/dall-e",
        "data_regions": ["US (Microsoft Azure)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "sdílená DPA s OpenAI platformou",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": False,
        "description_cs": "AI generátor obrázků od OpenAI — vytváří a edituje obrázky na základě textového popisu.",
        "key_risks_cs": [
            "Generování zavádějícího vizuálního obsahu",
            "Porušení autorských práv k vygenerovaným obrázkům",
            "Čl. 50 odst. 4 AI Act — povinnost označit AI obsah",
        ],
        "measures_cs": [
            "Označit AI-generované obrázky jako umělou inteligenci",
            "Nekopírovat styly konkrétních umělců",
            "Kontrolovat obsah před publikací",
        ],
        "monitoring_kpis_cs": ["Počet AI obrázků publikovaných bez označení"],
        "training_focus_cs": ["Povinnost označování AI obsahu dle čl. 50"],
        "transparency_cs": "Tento obrázek byl vytvořen umělou inteligencí (DALL-E).",
    },

    "Midjourney": {
        "provider": "Midjourney, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://midjourney.com",
        "data_regions": ["US"],
        "eu_based": False,
        "dpa_available": False,
        "dpa_note": "veřejná DPA není k dispozici — nutno vyžádat individuálně",
        "gdpr_mechanisms": ["ToS"],
        "certifications": [],
        "opt_out_training": False,
        "description_cs": "AI generátor vysoce kvalitních uměleckých obrázků přes Discord a webové rozhraní.",
        "key_risks_cs": [
            "Žádná veřejná DPA — GDPR riziko",
            "Generované obrázky jsou ve výchozím stavu veřejné",
            "Čl. 50 odst. 4 — povinnost označit AI obsah",
        ],
        "measures_cs": [
            "Zvážit upgrade na Pro plán (private mode)",
            "Vyžádat DPA od Midjourney před firemním použitím",
            "Označit všechny AI obrázky dle čl. 50",
        ],
        "monitoring_kpis_cs": ["Počet publikovaných AI obrázků", "Soulad s označováním"],
        "training_focus_cs": ["Označování AI obsahu", "Rizika veřejného generování"],
        "transparency_cs": "Tento obrázek byl vytvořen umělou inteligencí (Midjourney).",
    },

    "Stable Diffusion": {
        "provider": "Stability AI Ltd.",
        "provider_hq": "Londýn, Velká Británie",
        "website": "https://stability.ai",
        "data_regions": ["Self-hosted / US (API)"],
        "eu_based": False,
        "gdpr_adequate": True,
        "gdpr_adequate_note": "UK má rozhodnutí o přiměřenosti (adequacy decision) od EU — přenos dat je regulérní.",
        "dpa_available": True,
        "dpa_note": "dostupná pro API zákazníky",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Open-source AI model pro generování obrázků — lze provozovat lokálně (on-premise).",
        "key_risks_cs": [
            "Při lokálním provozu plná odpovědnost za bezpečnost modelu",
            "Čl. 50 odst. 4 — povinnost označit AI obsah",
        ],
        "measures_cs": [
            "Při self-hosted provozu zabezpečit infrastrukturu",
            "Označit AI obrázky i při lokálním generování",
        ],
        "monitoring_kpis_cs": ["Bezpečnost self-hosted infrastruktury"],
        "training_focus_cs": ["Odpovědné použití generativních modelů"],
        "transparency_cs": "Tento obrázek byl vytvořen umělou inteligencí (Stable Diffusion).",
    },

    "Canva AI": {
        "provider": "Canva Pty Ltd.",
        "provider_hq": "Sydney, Austrálie",
        "website": "https://canva.com",
        "data_regions": ["US, Austrálie"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Canva Data Processing Addendum",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "Grafická platforma s AI funkcemi pro generování obrázků, textů a designů.",
        "key_risks_cs": [
            "AI funkce mohou zpracovávat firemní branding a materiály",
            "Čl. 50 odst. 4 — povinnost označit AI obsah",
        ],
        "measures_cs": [
            "Označit AI-generované grafiky",
            "Uzavřít Canva DPA pro firemní tým",
        ],
        "monitoring_kpis_cs": ["Počet AI designů", "Soulad s označováním"],
        "training_focus_cs": ["Označování AI obsahu v marketingových materiálech"],
        "transparency_cs": "Grafika vytvořena s pomocí AI (Canva AI).",
    },

    "Adobe Firefly": {
        "provider": "Adobe Inc.",
        "provider_hq": "San Jose, CA, USA",
        "website": "https://adobe.com/products/firefly",
        "data_regions": ["Adobe Experience Cloud (US, EU)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Adobe DPA (adobe.com/privacy/policy)",
        "gdpr_mechanisms": ["SCC", "BCR", "DPA"],
        "certifications": ["ISO 27001", "SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI generátor obrázků od Adobe, trénovaný na licencovaném obsahu — bezpečnější z hlediska autorských práv.",
        "key_risks_cs": [
            "Čl. 50 odst. 4 — povinnost označit AI obsah",
            "Riziko závislosti na Adobe ekosystému",
        ],
        "measures_cs": [
            "Využívat Content Credentials pro označení AI obsahu",
            "Uzavřít Adobe DPA",
        ],
        "monitoring_kpis_cs": ["Označování AI obsahu přes Content Credentials"],
        "training_focus_cs": ["Správné použití Firefly v rámci Creative Cloud"],
        "transparency_cs": "Obrázek vytvořen s pomocí AI (Adobe Firefly).",
    },

    "Jasper": {
        "provider": "Jasper AI, Inc.",
        "provider_hq": "Austin, TX, USA",
        "website": "https://jasper.ai",
        "data_regions": ["US (Google Cloud)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Jasper DPA dostupná",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro tvorbu marketingového obsahu — blogové články, reklamy, sociální sítě.",
        "key_risks_cs": ["Faktické chyby v generovaném obsahu", "Únik firemního tone of voice"],
        "measures_cs": ["Kontrola všech textů editorem před publikací", "Uzavřít DPA"],
        "monitoring_kpis_cs": ["Přesnost generovaných textů", "Počet korektur editorem"],
        "training_focus_cs": ["Redakční kontrola AI obsahu"],
        "transparency_cs": "Text vytvořen s pomocí AI (Jasper).",
    },

    "Copy.ai": {
        "provider": "Copy.ai, Inc.",
        "provider_hq": "Memphis, TN, USA",
        "website": "https://copy.ai",
        "data_regions": ["US"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro Enterprise",
        "gdpr_mechanisms": ["SCC"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI copywriting nástroj pro generování reklamních textů, emailů a produktových popisů.",
        "key_risks_cs": ["Generické nebo nepřesné texty", "Nekonzistence s firemním stylem"],
        "measures_cs": ["Redakční revize všech výstupů", "Nastavit brand voice"],
        "monitoring_kpis_cs": ["Využití vs. ruční úpravy"],
        "training_focus_cs": ["Kontrola AI copywritingu"],
        "transparency_cs": "Text vytvořen s pomocí AI (Copy.ai).",
    },

    "Suno AI": {
        "provider": "Suno, Inc.",
        "provider_hq": "Cambridge, MA, USA",
        "website": "https://suno.com",
        "data_regions": ["US"],
        "eu_based": False,
        "dpa_available": False,
        "dpa_note": "veřejná DPA není k dispozici",
        "gdpr_mechanisms": ["ToS"],
        "certifications": [],
        "opt_out_training": False,
        "description_cs": "AI generátor hudby a písní — vytváří kompletní skladby na základě textového popisu.",
        "key_risks_cs": [
            "Autorská práva k AI skladbám nejasná",
            "Čl. 50 odst. 4 — povinnost označit AI obsah",
        ],
        "measures_cs": [
            "Označit AI hudbu jako generovanou umělou inteligencí",
            "Nepoužívat pro komerční účely bez právního ověření licencí",
        ],
        "monitoring_kpis_cs": ["Použití AI hudby v komerčním kontextu"],
        "training_focus_cs": ["Autorská práva k AI obsahu"],
        "transparency_cs": "Hudba vytvořena umělou inteligencí (Suno AI).",
    },

    # ══════════════ DEEPFAKE / VIDEO / HLAS ══════════════

    "Sora": {
        "provider": "OpenAI, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://openai.com/sora",
        "data_regions": ["US (Microsoft Azure)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "sdílená DPA s OpenAI platformou",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": False,
        "description_cs": "AI model od OpenAI pro generování videí z textového popisu.",
        "key_risks_cs": [
            "Čl. 50 odst. 4 — povinnost oznámit, že obsah je AI-generovaný",
            "Riziko tvorby deepfake obsahu",
            "Reputační riziko při neoznačeném AI videu",
        ],
        "measures_cs": [
            "Vždy označit AI video viditelným watermarkem nebo textovou zmínkou",
            "Zákaz tvorby deepfake obsahu zobrazujícího reálné osoby bez souhlasu",
            "Uchovávat záznamy o generování (prompt, datum, účel)",
        ],
        "monitoring_kpis_cs": ["Počet AI videí", "Soulad s označováním dle čl. 50"],
        "training_focus_cs": ["Etické a právní aspekty AI videa", "Povinnosti dle čl. 50"],
        "transparency_cs": "Toto video bylo vytvořeno umělou inteligencí (OpenAI Sora).",
    },

    "VEO3": {
        "provider": "Google LLC (Alphabet Inc.)",
        "provider_hq": "Mountain View, CA, USA",
        "website": "https://deepmind.google/technologies/veo",
        "data_regions": ["Google Cloud"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Google Cloud DPA",
        "gdpr_mechanisms": ["SCC", "BCR", "DPA"],
        "certifications": ["ISO 27001", "SOC 2"],
        "opt_out_training": True,
        "description_cs": "AI model Google DeepMind pro generování videí — součást Gemini platformy.",
        "key_risks_cs": [
            "Čl. 50 odst. 4 — povinnost označit AI video",
            "Deepfake riziko",
        ],
        "measures_cs": [
            "Označit všechna AI videa",
            "Používat SynthID watermark (automaticky zabudovaný)",
        ],
        "monitoring_kpis_cs": ["Výskyt AI videí", "Přítomnost označení"],
        "training_focus_cs": ["Povinnosti při AI videu dle čl. 50"],
        "transparency_cs": "Toto video bylo vytvořeno umělou inteligencí (Google VEO).",
    },

    "HeyGen": {
        "provider": "HeyGen, Inc.",
        "provider_hq": "Los Angeles, CA, USA",
        "website": "https://heygen.com",
        "data_regions": ["US (AWS)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro Enterprise plán",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro tvorbu videí s digitálními avatary a překlady videa.",
        "key_risks_cs": [
            "Čl. 50 — deepfake povinné označení",
            "Biometrická data (obličej, hlas) avatara",
            "Riziko zneužití k vydávání se za reálné osoby",
        ],
        "measures_cs": [
            "Označit videa s AI avatarem jako uměle vytvořená",
            "Získat souhlas osob, jejichž podoba je použita",
            "Nepoužívat k vytváření klamavého obsahu",
        ],
        "monitoring_kpis_cs": ["Počet AI videí", "Splnění čl. 50"],
        "training_focus_cs": ["Etika AI avatarů", "Povinné označení deepfake"],
        "transparency_cs": "Toto video využívá AI avatar vytvořený technologií HeyGen.",
    },

    "Synthesia": {
        "provider": "Synthesia Ltd.",
        "provider_hq": "Londýn, Velká Británie",
        "website": "https://synthesia.io",
        "data_regions": ["EU (UK, Irsko)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "Synthesia DPA dostupná",
        "gdpr_mechanisms": ["UK GDPR", "DPA"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro tvorbu školicích a firemních videí s digitálními prezentátory.",
        "key_risks_cs": [
            "Čl. 50 — povinné označení AI obsahu",
            "Biometrická data digitálních avatarů",
        ],
        "measures_cs": [
            "Označit AI videa při zveřejnění",
            "Používat pouze licencované avatary",
        ],
        "monitoring_kpis_cs": ["Počet AI školících videí"],
        "training_focus_cs": ["Správné použití AI videí ve firemní komunikaci"],
        "transparency_cs": "Toto video bylo vytvořeno s pomocí AI (Synthesia).",
    },

    "ElevenLabs": {
        "provider": "ElevenLabs, Inc.",
        "provider_hq": "New York, NY, USA",
        "website": "https://elevenlabs.io",
        "data_regions": ["US, EU"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro firemní zákazníky",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro syntézu řeči, klonování hlasu a dabbing.",
        "key_risks_cs": [
            "Čl. 50 — AI hlas musí být označen",
            "Klonování hlasu — riziko zneužití identity",
            "Biometrická data (hlasový profil)",
        ],
        "measures_cs": [
            "Označit syntetický hlas jako AI-generovaný",
            "Klonovat pouze vlastní hlas nebo s písemným souhlasem",
            "Nepoužívat k podvodnému vydávání se za jinou osobu",
        ],
        "monitoring_kpis_cs": ["Počet AI hlasových výstupů", "Splnění čl. 50"],
        "training_focus_cs": ["Etika klonování hlasu", "Povinné označení AI řeči"],
        "transparency_cs": "Tento hlasový výstup byl vytvořen umělou inteligencí (ElevenLabs).",
    },

    "D-ID": {
        "provider": "D-ID Ltd.",
        "provider_hq": "Tel Aviv, Izrael",
        "website": "https://d-id.com",
        "data_regions": ["US, EU (AWS)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "D-ID DPA dostupná",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro tvorbu mluvících digitálních avatarů z fotografie.",
        "key_risks_cs": ["Deepfake riziko", "Biometrická data", "Čl. 50 povinnosti"],
        "measures_cs": ["Označit AI avatary", "Souhlas zobrazených osob"],
        "monitoring_kpis_cs": ["Počet AI avatarů v produkci"],
        "training_focus_cs": ["Etika digitálních avatarů"],
        "transparency_cs": "Tento avatar byl vytvořen umělou inteligencí (D-ID).",
    },

    "Murf AI": {
        "provider": "Murf Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://murf.ai",
        "data_regions": ["US (AWS)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "dostupná pro Enterprise",
        "gdpr_mechanisms": ["SCC"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "AI platforma pro text-to-speech konverzi s realistickými hlasy.",
        "key_risks_cs": ["Čl. 50 — povinné označení AI hlasu"],
        "measures_cs": ["Označit AI hlasový výstup"],
        "monitoring_kpis_cs": ["Použití AI hlasu"],
        "training_focus_cs": ["Označování AI řeči"],
        "transparency_cs": "Hlasový výstup vytvořen AI (Murf AI).",
    },

    # ══════════════ HR / RECRUITMENT ══════════════

    "LinkedIn Recruiter": {
        "provider": "LinkedIn Corporation (Microsoft)",
        "provider_hq": "Sunnyvale, CA, USA",
        "website": "https://linkedin.com",
        "data_regions": ["US, EU (Irsko)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "LinkedIn DPA / Microsoft DPA",
        "gdpr_mechanisms": ["SCC", "BCR", "DPA"],
        "certifications": ["ISO 27001", "SOC 2"],
        "opt_out_training": True,
        "description_cs": "AI nástroj pro vyhledávání a oslovování kandidátů na LinkedIn platformě.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ SYSTÉM — čl. 6 + Příloha III bod 4 (zaměstnanost)",
            "AI ovlivňuje přístup k zaměstnání — diskriminační riziko",
            "Zpracování osobních údajů kandidátů",
        ],
        "measures_cs": [
            "Implementovat lidský dohled nad AI doporučeními kandidátů",
            "Nesmí být jediné kritérium výběru — vždy lidské rozhodnutí",
            "Dokumentovat kritéria výběru a zvát i kandidáty mimo AI doporučení",
            "Provést FRIA dle čl. 27 AI Act",
        ],
        "monitoring_kpis_cs": [
            "Diverzita vybraných kandidátů (věk, pohlaví)",
            "% rozhodnutí přehodnocených člověkem",
            "Počet kandidátů mimo AI doporučení",
        ],
        "training_focus_cs": [
            "Rizika diskriminace v AI recruitmentu",
            "Povinný lidský dohled dle čl. 14",
        ],
        "transparency_cs": "Při výběrovém řízení využíváme AI nástroje. Konečné rozhodnutí vždy činí člověk.",
    },

    "Teamio": {
        "provider": "LMC s.r.o. (Alma Career)",
        "provider_hq": "Praha, Česká republika",
        "website": "https://teamio.com",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "LMC DPA součástí smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český ATS (Applicant Tracking System) s AI funkcemi pro třídění uchazečů.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ — AI v recruitmentu (Příloha III bod 4)",
            "Automatické třídění životopisů — diskriminační riziko",
        ],
        "measures_cs": [
            "Lidský dohled nad AI řazením kandidátů",
            "Pravidelná kontrola bias v AI doporučeních",
        ],
        "monitoring_kpis_cs": [
            "Diverzita shortlistu",
            "Korelace AI skóre s reálným úspěchem kandidáta",
        ],
        "training_focus_cs": ["Diskriminační rizika AI v HR"],
        "transparency_cs": "V procesu náboru využíváme AI nástroje. Rozhodnutí činí lidský hodnotitel.",
    },

    "LMC/Jobs.cz AI": {
        "provider": "LMC s.r.o. (Alma Career)",
        "provider_hq": "Praha, Česká republika",
        "website": "https://jobs.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "LMC DPA",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Největší český pracovní portál s AI doporučováním kandidátů a pracovních nabídek.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ — AI ovlivňuje přístup k zaměstnání",
            "Riziko diskriminace v AI doporučeních",
        ],
        "measures_cs": [
            "Lidský přezkum AI-doporučených kandidátů",
            "Monitoring diverzity ve výběrovém řízení",
        ],
        "monitoring_kpis_cs": ["Diverzita, nediskriminace"],
        "training_focus_cs": ["AI v recruitmentu — právní povinnosti"],
        "transparency_cs": "Využíváme AI pro doporučení relevantních kandidátů.",
    },

    "Sloneek": {
        "provider": "Sloneek s.r.o.",
        "provider_hq": "Praha, Česká republika",
        "website": "https://sloneek.com",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "Sloneek DPA součástí smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český HR systém s AI funkcemi pro řízení zaměstnanců, docházku a hodnocení.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ pokud AI ovlivňuje hodnocení zaměstnanců",
            "Zpracování citlivých HR dat",
        ],
        "measures_cs": [
            "Lidský dohled nad AI hodnocením zaměstnanců",
            "Audit nediskriminace",
        ],
        "monitoring_kpis_cs": ["Objektivita AI hodnocení"],
        "training_focus_cs": ["Správné využití AI v HR procesech"],
        "transparency_cs": "Pro HR procesy využíváme AI nástroje. Rozhodnutí činí vedoucí pracovník.",
    },

    "Prace.cz AI": {
        "provider": "Prace.cz (Internet Info, s.r.o.)",
        "provider_hq": "Praha, Česká republika",
        "website": "https://prace.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "DPA součástí obchodních podmínek",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český pracovní portál s AI doporučováním pracovních nabídek.",
        "key_risks_cs": ["VYSOCE RIZIKOVÝ — AI v zaměstnanosti"],
        "measures_cs": ["Lidský přezkum AI doporučení"],
        "monitoring_kpis_cs": ["Kvalita AI doporučení"],
        "training_focus_cs": ["AI v recruitmentu"],
        "transparency_cs": "Využíváme AI pro doporučení pracovních pozic.",
    },

    # ══════════════ ÚČETNÍ SOFTWARE ══════════════

    "Fakturoid": {
        "provider": "Fakturoid s.r.o.",
        "provider_hq": "Česká republika",
        "website": "https://fakturoid.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "součástí obchodních podmínek",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český online fakturační systém s AI funkcemi pro automatické zpracování dokladů.",
        "key_risks_cs": [
            "AI zpracovává finanční a osobní údaje",
            "Riziko chybného rozpoznání údajů na fakturách",
        ],
        "measures_cs": [
            "Kontrolovat AI-rozpoznané údaje na fakturách",
            "Data zůstávají v EU — nižší GDPR riziko",
        ],
        "monitoring_kpis_cs": ["Přesnost rozpoznávání faktur"],
        "training_focus_cs": ["Kontrola AI výstupů ve fakturaci"],
        "transparency_cs": "Pro zpracování faktur využíváme AI rozpoznávání.",
    },

    "Money S5": {
        "provider": "Cígler Software, a.s.",
        "provider_hq": "Česká republika",
        "website": "https://money.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "součástí licenční smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český ekonomický a účetní software s AI funkcemi pro automatizaci účetnictví.",
        "key_risks_cs": ["AI v účetnictví — riziko chybných zápisů"],
        "measures_cs": ["Kontrola AI-navržených účetních zápisů účetním"],
        "monitoring_kpis_cs": ["Přesnost AI účetních návrhů"],
        "training_focus_cs": ["Kontrola AI v účetním software"],
        "transparency_cs": "Účetní systém využívá AI pro návrhy zaúčtování.",
    },

    "ABRA": {
        "provider": "ABRA Software a.s.",
        "provider_hq": "Česká republika",
        "website": "https://abra.eu",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "součástí smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český ERP a účetní systém s AI moduly pro automatizaci.",
        "key_risks_cs": ["AI v ERP — chybná automatizace procesů"],
        "measures_cs": ["Kontrola AI automatizací", "Auditní trail"],
        "monitoring_kpis_cs": ["Přesnost automatizovaných procesů"],
        "training_focus_cs": ["Bezpečné použití AI v ERP"],
        "transparency_cs": "ERP systém využívá AI automatizace.",
    },

    "Pohoda": {
        "provider": "STORMWARE s.r.o.",
        "provider_hq": "Jihlava, Česká republika",
        "website": "https://stormware.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "součástí licenční smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Nejrozšířenější český účetní software s AI funkcemi pro automatizaci dokladů.",
        "key_risks_cs": ["Chybné AI zaúčtování", "Zpracování finančních dat"],
        "measures_cs": ["Kontrola AI návrhů účetním", "Pravidelná revize"],
        "monitoring_kpis_cs": ["Přesnost AI zaúčtování"],
        "training_focus_cs": ["Kontrola AI v účetním software"],
        "transparency_cs": "Účetní software využívá AI pro návrhy.",
    },

    "iDoklad": {
        "provider": "Solitea, a.s.",
        "provider_hq": "Česká republika",
        "website": "https://idoklad.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "součástí obchodních podmínek",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český online fakturační systém s OCR a AI rozpoznáváním dokladů.",
        "key_risks_cs": ["Chybné rozpoznání údajů na dokladech"],
        "measures_cs": ["Kontrola AI-rozpoznaných údajů"],
        "monitoring_kpis_cs": ["OCR přesnost"],
        "training_focus_cs": ["Kontrola AI zpracování dokladů"],
        "transparency_cs": "Pro zpracování dokladů využíváme AI rozpoznávání.",
    },

    "Helios": {
        "provider": "Asseco Solutions, a.s.",
        "provider_hq": "Česká republika",
        "website": "https://helios.eu",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "součástí implementační smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": ["ISO 27001"],
        "opt_out_training": True,
        "description_cs": "Český ERP systém (Helios Green/Orange) s AI moduly pro predikci a automatizaci.",
        "key_risks_cs": ["AI predikce mohou vést k chybným obchodním rozhodnutím"],
        "measures_cs": ["Lidská kontrola AI predikcí", "Audit trail"],
        "monitoring_kpis_cs": ["Přesnost AI predikcí"],
        "training_focus_cs": ["Interpretace AI výstupů v ERP"],
        "transparency_cs": "ERP systém využívá AI predikce.",
    },

    # ══════════════ CHATBOT PLATFORMY ══════════════

    "Smartsupp": {
        "provider": "Smartsupp.com, s.r.o.",
        "provider_hq": "Brno, Česká republika",
        "website": "https://smartsupp.com",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "Smartsupp DPA dostupná",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Český live chat a AI chatbot pro zákaznickou podporu na webových stránkách.",
        "key_risks_cs": [
            "Čl. 50 odst. 1 — povinné oznámení o AI chatbotu uživatelům",
            "Chatbot může poskytnout nepřesné informace zákazníkům",
            "Zpracování osobních údajů z konverzací",
        ],
        "measures_cs": [
            'Zobrazit na webu oznámení: \u201eKomunikujete s AI asistentem.\u201c',
            "Umožnit přepojení na lidského operátora",
            "Uzavřít DPA se Smartsupp",
            "Logovat a kontrolovat odpovědi chatbotu",
        ],
        "monitoring_kpis_cs": [
            "% správných odpovědí chatbotu",
            "Počet eskalací na lidského operátora",
            "Spokojenost zákazníků s chatbotem",
        ],
        "training_focus_cs": [
            "Nastavení a údržba AI chatbotu",
            "Kdy zasáhnout a převzít konverzaci",
        ],
        "transparency_cs": "Tento chat je provozován AI asistentem. Můžete požádat o spojení s operátorem.",
    },

    "Tidio": {
        "provider": "Tidio LLC",
        "provider_hq": "San Francisco, CA / Szczecin, Polsko",
        "website": "https://tidio.com",
        "data_regions": ["EU, US"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "Tidio DPA dostupná",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Chatbot a live chat platforma s AI automatizací zákaznické komunikace.",
        "key_risks_cs": [
            "Čl. 50 odst. 1 — povinné oznámení o AI",
            "Nepřesné automatické odpovědi",
        ],
        "measures_cs": [
            "Oznámit uživatelům, že komunikují s AI",
            "Umožnit přepojení na člověka",
        ],
        "monitoring_kpis_cs": ["Přesnost odpovědí", "Eskalace na operátora"],
        "training_focus_cs": ["Správa AI chatbotu"],
        "transparency_cs": "Tento chat využívá AI. Můžete požádat o spojení s operátorem.",
    },

    "Intercom": {
        "provider": "Intercom, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://intercom.com",
        "data_regions": ["US (AWS)", "EU hosting dostupný"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Intercom DPA (intercom.com/legal)",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "Platforma pro zákaznickou komunikaci s AI chatbotem (Fin AI) a automatizací.",
        "key_risks_cs": [
            "Čl. 50 odst. 1 — povinné oznámení o AI",
            "AI Fin může poskytovat nepřesné informace",
            "Data mimo EU ve výchozím nastavení",
        ],
        "measures_cs": [
            "Aktivovat EU data hosting",
            "Konfigurovat Fin AI s firemní knowledge base",
            "Uzavřít Intercom DPA",
        ],
        "monitoring_kpis_cs": ["Přesnost Fin AI", "Resolution rate", "CSAT"],
        "training_focus_cs": ["Správa AI chatbotu Fin", "Údržba knowledge base"],
        "transparency_cs": "Komunikujete s AI asistentem. Můžete být přepojeni na operátora.",
    },

    "Drift": {
        "provider": "Drift (Salesloft, Inc.)",
        "provider_hq": "Boston, MA, USA",
        "website": "https://drift.com",
        "data_regions": ["US (AWS)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Drift DPA dostupná",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "Konverzační marketing a sales chatbot s AI kvalifikací leadů.",
        "key_risks_cs": ["Čl. 50 — oznámení o AI chatbotu", "Data v US"],
        "measures_cs": ["Oznámit AI chatbot na webu", "Uzavřít DPA"],
        "monitoring_kpis_cs": ["Kvalita AI leadů", "Konverzní poměr"],
        "training_focus_cs": ["Správa konverzačního AI"],
        "transparency_cs": "Tento chat využívá AI pro předkvalifikaci. Můžete mluvit s obchodníkem.",
    },

    "Chatbot.cz": {
        "provider": "Chatbot.cz (český poskytovatel)",
        "provider_hq": "Česká republika",
        "website": "https://chatbot.cz",
        "data_regions": ["EU (Česká republika)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "DPA součástí smlouvy",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Česká chatbot platforma pro tvorbu konverzačních AI asistentů.",
        "key_risks_cs": ["Čl. 50 — povinné oznámení o AI"],
        "measures_cs": ["Označit chatbot jako AI", "Data v EU"],
        "monitoring_kpis_cs": ["Přesnost odpovědí chatbotu"],
        "training_focus_cs": ["Správa české chatbot platformy"],
        "transparency_cs": "Komunikujete s AI chatbotem. Můžete požádat o operátora.",
    },

    # ══════════════ EMAIL / SUPPORT AI ══════════════

    "Freshdesk AI": {
        "provider": "Freshworks Inc.",
        "provider_hq": "San Mateo, CA, USA",
        "website": "https://freshworks.com",
        "data_regions": ["US, EU (Německo), Indie"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Freshworks DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI helpdesk platforma pro automatizaci zákaznické podpory a ticketového systému.",
        "key_risks_cs": [
            "AI automatické odpovědi mohou být nepřesné",
            "Zpracování osobních údajů zákazníků",
        ],
        "measures_cs": [
            "Aktivovat EU data center",
            "Kontrolovat AI automatické odpovědi",
            "Uzavřít Freshworks DPA",
        ],
        "monitoring_kpis_cs": ["Přesnost AI odpovědí", "Ticket resolution time"],
        "training_focus_cs": ["Správa AI v helpdesku"],
        "transparency_cs": "Odpovědi zákaznické podpory mohou být předpřipraveny s pomocí AI.",
    },

    "Zendesk AI": {
        "provider": "Zendesk, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://zendesk.com",
        "data_regions": ["US, EU (Německo)"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Zendesk DPA (zendesk.com/company/data-processing-addendum)",
        "gdpr_mechanisms": ["SCC", "BCR", "DPA"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI zákaznická platforma s automatickou triage, odpovídáním a analýzou ticketů.",
        "key_risks_cs": [
            "AI automatické odpovědi mohou být nevhodné",
            "Zpracování osobních údajů zákazníků mimo EU",
        ],
        "measures_cs": [
            "Aktivovat EU hosting",
            "Nastavit pravidla pro AI eskalaci na agenta",
            "Uzavřít Zendesk DPA",
        ],
        "monitoring_kpis_cs": ["CSAT", "AI resolution rate", "Eskalace"],
        "training_focus_cs": ["Správa Zendesk AI funkcí"],
        "transparency_cs": "Zákaznická podpora využívá AI pro zrychlení odpovědí.",
    },

    # ══════════════ KREDITNÍ SKÓRING ══════════════

    "CRIF": {
        "provider": "CRIF S.p.A.",
        "provider_hq": "Bologna, Itálie",
        "website": "https://crif.com",
        "data_regions": ["EU"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "CRIF DPA",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": ["ISO 27001"],
        "opt_out_training": True,
        "description_cs": "Evropská informační agentura pro kreditní skóring a hodnocení rizika.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ — AI rozhoduje o kreditní bonitě (Příloha III bod 5b)",
            "Diskriminační riziko v kreditním modelu",
            "Zpracování citlivých finančních údajů",
        ],
        "measures_cs": [
            "Lidský přezkum každého zamítnutí kreditu",
            "Audit nediskriminace kreditního modelu",
            "Právo na vysvětlení rozhodnutí (čl. 86 AI Act)",
            "FRIA dle čl. 27",
        ],
        "monitoring_kpis_cs": ["False positive/negative rate", "Bias audit výsledky"],
        "training_focus_cs": ["Diskriminace v kreditním skóringu", "Právo na vysvětlení"],
        "transparency_cs": "Pro hodnocení bonity využíváme AI kreditní skóring. Máte právo na vysvětlení.",
    },

    "Bisnode/D&B": {
        "provider": "Dun & Bradstreet Corporation",
        "provider_hq": "Jacksonville, FL, USA",
        "website": "https://dnb.com",
        "data_regions": ["US, EU"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "D&B DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["ISO 27001", "SOC 2"],
        "opt_out_training": True,
        "description_cs": "Globální obchodní informační agentura s AI kreditními modely a analýzou rizik.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ — hodnocení kreditní bonity",
            "Data mohou být zpracovávána v US",
        ],
        "measures_cs": [
            "Lidský přezkum kreditních rozhodnutí",
            "Uzavřít D&B DPA",
            "Audit kreditního modelu na bias",
        ],
        "monitoring_kpis_cs": ["Přesnost kreditního skóringu", "Bias metriky"],
        "training_focus_cs": ["Odpovědné použití kreditního AI"],
        "transparency_cs": "Pro hodnocení obchodních partnerů využíváme AI analýzu.",
    },

    "Scoring Solutions": {
        "provider": "Individuální — závisí na konkrétním poskytovateli kreditního skóringu",
        "provider_hq": "Závisí na poskytovateli",
        "website": "",
        "data_regions": ["Závisí na implementaci — nutno ověřit u konkrétního poskytovatele"],
        "eu_based": False,
        "is_generic_entry": True,
        "generic_note": "Toto je generický záznam pro AI kreditní skóring, kde klient neuvedl konkrétního poskytovatele. Všechny uvedené údaje jsou obecné a musí být ověřeny u konkrétního dodavatele.",
        "dpa_available": True,
        "dpa_note": "DPA MUSÍ být uzavřena s konkrétním poskytovatelem — ověřte její dostupnost",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "AI řešení pro kreditní skóring a hodnocení finančního rizika. Konkrétní poskytovatel nebyl specifikován — údaje jsou obecné.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ — AI rozhoduje o kreditní bonitě (Příloha III bod 5b)",
            "Konkrétní poskytovatel nebyl identifikován — nutný dodavatelský audit",
        ],
        "measures_cs": [
            "Identifikovat a zdokumentovat konkrétního poskytovatele skóringového modelu",
            "Lidský přezkum každého zamítnutí",
            "Audit nediskriminace",
            "FRIA dle čl. 27",
        ],
        "monitoring_kpis_cs": ["Přesnost skórování", "Diskriminační metriky"],
        "training_focus_cs": ["AI v kreditním rozhodování"],
        "transparency_cs": "Pro hodnocení bonity využíváme AI kreditní skóring.",
    },

    # ══════════════ KRITICKÁ INFRASTRUKTURA ══════════════

    "Siemens MindSphere": {
        "provider": "Siemens AG",
        "provider_hq": "Mnichov, Německo",
        "website": "https://siemens.com",
        "data_regions": ["EU (Německo, Nizozemsko)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "Siemens DPA",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": ["ISO 27001", "SOC 2", "IEC 62443"],
        "opt_out_training": True,
        "description_cs": "IoT a AI platforma pro průmyslové řízení, prediktivní údržbu a monitorování.",
        "key_risks_cs": [
            "VYSOCE RIZIKOVÝ — AI v kritické infrastruktuře (Příloha III bod 2)",
            "Bezpečnostní rizika v průmyslovém řízení",
            "Výpadek AI může ovlivnit výrobní proces",
        ],
        "measures_cs": [
            "Implementovat fail-safe mechanismy nezávislé na AI",
            "Redundantní systémy pro kritické procesy",
            "Pravidelné bezpečnostní audity dle IEC 62443",
            "FRIA + QMS dle čl. 9-15",
        ],
        "monitoring_kpis_cs": ["Dostupnost systému", "False alarm rate", "Řízení bezpečnosti"],
        "training_focus_cs": ["Průmyslová AI bezpečnost", "Fail-safe postupy"],
        "transparency_cs": "Průmyslové řízení využívá AI pro optimalizaci a prediktivní údržbu.",
    },

    "ABB Ability": {
        "provider": "ABB Ltd.",
        "provider_hq": "Curych, Švýcarsko",
        "website": "https://abb.com",
        "data_regions": ["EU (Švýcarsko, Německo)"],
        "eu_based": False,
        "gdpr_adequate": True,
        "gdpr_adequate_note": "Švýcarsko má rozhodnutí o přiměřenosti od EU — přenos dat je regulérní.",
        "dpa_available": True,
        "dpa_note": "ABB DPA",
        "gdpr_mechanisms": ["DPA", "SCC"],
        "certifications": ["ISO 27001", "IEC 62443"],
        "opt_out_training": True,
        "description_cs": "AI platforma ABB pro průmyslovou automatizaci a řízení energií.",
        "key_risks_cs": ["VYSOCE RIZIKOVÝ — kritická infrastruktura", "Bezpečnostní rizika"],
        "measures_cs": ["Fail-safe mechanismy", "Redundance", "Pravidelné audity"],
        "monitoring_kpis_cs": ["Dostupnost", "Bezpečnostní incidenty"],
        "training_focus_cs": ["Průmyslová AI bezpečnost"],
        "transparency_cs": "Průmyslové systémy využívají AI od ABB.",
    },

    "Honeywell Forge": {
        "provider": "Honeywell International Inc.",
        "provider_hq": "Charlotte, NC, USA",
        "website": "https://honeywell.com",
        "data_regions": ["US, EU"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Honeywell DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["ISO 27001", "SOC 2", "IEC 62443"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro řízení budov, energetiky a průmyslových procesů.",
        "key_risks_cs": ["VYSOCE RIZIKOVÝ — kritická infrastruktura", "Data v US"],
        "measures_cs": ["Fail-safe mechanismy", "EU data processing", "DPA"],
        "monitoring_kpis_cs": ["Dostupnost", "Energetická efektivita"],
        "training_focus_cs": ["AI v řízení budov a energetiky"],
        "transparency_cs": "Řízení budov využívá AI od Honeywell.",
    },

    # ══════════════ CENOVÁ OPTIMALIZACE ══════════════

    "Prisync": {
        "provider": "Prisync Ltd.",
        "provider_hq": "Istanbul, Turecko",
        "website": "https://prisync.com",
        "data_regions": ["US, EU"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Prisync DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "AI nástroj pro monitoring konkurenčních cen a dynamickou cenotvorbu.",
        "key_risks_cs": ["AI cenové manipulace — riziko nekalé soutěže", "Algoritmická kolůzze"],
        "measures_cs": ["Lidský dohled nad cenovými změnami", "Audit cenové strategie"],
        "monitoring_kpis_cs": ["Cenové odchylky", "Marže", "Zákaznická spokojenost"],
        "training_focus_cs": ["Etická dynamická cenotvorba"],
        "transparency_cs": "Ceny na webu mohou být dynamicky upravovány.",
    },

    "Competera": {
        "provider": "Competera Pricing Platform S.L.",
        "provider_hq": "Barcelona, Španělsko",
        "website": "https://competera.net",
        "data_regions": ["EU"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "Competera DPA",
        "gdpr_mechanisms": ["DPA", "GDPR nativní"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "AI platforma pro cenotvorbu a cenovou optimalizaci v retailu.",
        "key_risks_cs": ["Algoritmická cenová diskriminace"],
        "measures_cs": ["Audit fairness cenového algoritmu", "Transparentní cenová politika"],
        "monitoring_kpis_cs": ["Cenová fairness", "Dopad na zákazníky"],
        "training_focus_cs": ["Etická AI cenotvorba"],
        "transparency_cs": "Ceny jsou optimalizovány s pomocí AI.",
    },

    "Dynamic Yield": {
        "provider": "Dynamic Yield (Mastercard)",
        "provider_hq": "Tel Aviv, Izrael (Mastercard: Purchase, NY)",
        "website": "https://dynamicyield.com",
        "data_regions": ["US, EU"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Mastercard DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI personalizační platforma pro webové stránky — A/B testing, doporučení, cenotvorba.",
        "key_risks_cs": ["Personalizace na základě profilování", "Dynamické ceny"],
        "measures_cs": ["Transparentní personalizační pravidla", "Uzavřít DPA"],
        "monitoring_kpis_cs": ["Personalizační metriky", "Konverzní poměr"],
        "training_focus_cs": ["Etická personalizace"],
        "transparency_cs": "Obsah webu je personalizován s pomocí AI.",
    },

    # ══════════════ POJIŠŤOVACÍ AI ══════════════

    "Guidewire": {
        "provider": "Guidewire Software, Inc.",
        "provider_hq": "San Mateo, CA, USA",
        "website": "https://guidewire.com",
        "data_regions": ["US, EU"],
        "eu_based": False,
        "dpa_available": True,
        "dpa_note": "Guidewire DPA",
        "gdpr_mechanisms": ["SCC", "DPA"],
        "certifications": ["SOC 2", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI platforma pro pojišťovny — automatizace pojistných událostí, pricing, detekce podvodů.",
        "key_risks_cs": ["VYSOCE RIZIKOVÝ — AI rozhoduje o pojistném plnění (Příloha III bod 5c)"],
        "measures_cs": ["Lidský přezkum zamítnutí pojistného plnění", "Audit bias", "FRIA"],
        "monitoring_kpis_cs": ["Přesnost fraud detekce", "Fairness pojistného"],
        "training_focus_cs": ["AI v pojišťovnictví — právní povinnosti"],
        "transparency_cs": "Pro zpracování pojistných událostí využíváme AI systémy.",
    },
    "Salesforce": {
        "provider": "Salesforce, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://www.salesforce.com",
        "data_regions": ["USA", "EU (Frankfurt)", "Austr\u00e1lie", "Japonsko"],
        "eu_based": False,
        "gdpr_adequate": False,
        "dpa_available": True,
        "dpa_note": "Data Processing Addendum (DPA) sou\u010d\u00e1st Trust and Compliance dokumentace",
        "gdpr_mechanisms": ["SCC (standardn\u00ed smluvn\u00ed dolo\u017eky)", "BCR", "EU Data Residency option"],
        "certifications": ["ISO 27001", "SOC 2 Type II", "SOC 3", "FedRAMP"],
        "opt_out_training": True,
        "description_cs": "CRM platforma s integrovan\u00fdm AI asistentem Einstein pro predikce, scoring lead\u016f a automatizaci prodejn\u00edch proces\u016f.",
        "key_risks_cs": ["Transfer dat do USA bez EU Data Residency", "AI scoring m\u016f\u017ee diskriminovat", "GDPR \u2014 zpracov\u00e1n\u00ed osobn\u00edch \u00fadaj\u016f klient\u016f"],
        "measures_cs": ["Aktivovat Salesforce Hyperforce EU pro data residency v EU", "Uzav\u0159\u00edt DPA s klauzul\u00ed o SCC", "Prov\u00e9st DPIA pro Einstein AI scoring"],
        "monitoring_kpis_cs": ["Po\u010det AI-scorovan\u00fdch lead\u016f / m\u011bs\u00edc", "False positive rate prediktivn\u00edho modelu"],
        "training_focus_cs": ["Jak Salesforce Einstein generuje predikce", "Limity AI scoringu"],
        "transparency_cs": "Salesforce Einstein je AI engine integrovan\u00fd do CRM. Predikce a sk\u00f3re jsou generov\u00e1ny strojov\u011b.",
    },
    "HubSpot": {
        "provider": "HubSpot, Inc.",
        "provider_hq": "Cambridge, MA, USA",
        "website": "https://www.hubspot.com",
        "data_regions": ["USA", "EU (Frankfurt)"],
        "eu_based": False,
        "gdpr_adequate": False,
        "dpa_available": True,
        "dpa_note": "DPA dostupn\u00fd online, automaticky platn\u00fd pro EU z\u00e1kazn\u00edky",
        "gdpr_mechanisms": ["SCC (standardn\u00ed smluvn\u00ed dolo\u017eky)", "EU data hosting option"],
        "certifications": ["SOC 2 Type II", "SOC 3", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "Marketingov\u00e1 a CRM platforma s AI funkcemi pro lead scoring, predikci konverz\u00ed a automatizaci kampan\u00ed.",
        "key_risks_cs": ["Transfer dat do USA pokud nen\u00ed zvolen EU hosting", "AI scoring \u2014 riziko profilov\u00e1n\u00ed"],
        "measures_cs": ["Aktivovat EU Data Residency v nastaven\u00ed", "Uzav\u0159\u00edt DPA p\u0159es HubSpot Legal Center"],
        "monitoring_kpis_cs": ["Po\u010det AI-scorovan\u00fdch kontakt\u016f / m\u011bs\u00edc", "Data residency status (EU/US)"],
        "training_focus_cs": ["HubSpot AI features \u2014 co d\u011blaj\u00ed a co ne", "Transparentnost pro kontakty dle AI Act"],
        "transparency_cs": "HubSpot vyu\u017e\u00edv\u00e1 AI pro scoring a predikce. V\u00fdsledky jsou strojov\u00e9 odhady.",
    },
    "Grammarly": {
        "provider": "Grammarly, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://www.grammarly.com",
        "data_regions": ["USA (AWS us-east-1)", "EU zpracov\u00e1n\u00ed voliteln\u00e9 pro Enterprise"],
        "eu_based": False,
        "gdpr_adequate": False,
        "dpa_available": True,
        "dpa_note": "DPA pro Grammarly Business/Enterprise",
        "gdpr_mechanisms": ["SCC (standardn\u00ed smluvn\u00ed dolo\u017eky)", "EU data processing (Enterprise)"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI n\u00e1stroj pro kontrolu a vylep\u0161ov\u00e1n\u00ed textu v angli\u010dtin\u011b a dal\u0161\u00edch jazyc\u00edch. Nab\u00edz\u00ed generativn\u00ed AI funkce.",
        "key_risks_cs": ["Ve\u0161ker\u00fd text proch\u00e1z\u00ed cloudov\u00fdmi servery v USA", "Riziko \u00faniku citliv\u00fdch informac\u00ed"],
        "measures_cs": ["Nasadit pouze Grammarly Business/Enterprise s DPA", "Zak\u00e1zat pou\u017eit\u00ed pro citliv\u00e9 dokumenty"],
        "monitoring_kpis_cs": ["Po\u010det aktivn\u00edch u\u017eivatel\u016f Grammarly"],
        "training_focus_cs": ["Co Grammarly zpracov\u00e1v\u00e1 a ukl\u00e1d\u00e1", "Rizika vkl\u00e1d\u00e1n\u00ed citliv\u00fdch dat"],
        "transparency_cs": "Grammarly pou\u017e\u00edv\u00e1 AI pro kontrolu a generov\u00e1n\u00ed textu. Ve\u0161ker\u00fd vlo\u017een\u00fd text je zpracov\u00e1n cloudov\u011b.",
    },
    "Notion AI": {
        "provider": "Notion Labs, Inc.",
        "provider_hq": "San Francisco, CA, USA",
        "website": "https://www.notion.so",
        "data_regions": ["USA (AWS us-west-2)"],
        "eu_based": False,
        "gdpr_adequate": False,
        "dpa_available": True,
        "dpa_note": "DPA dostupn\u00fd pro Notion Team/Enterprise pl\u00e1ny",
        "gdpr_mechanisms": ["SCC (standardn\u00ed smluvn\u00ed dolo\u017eky)"],
        "certifications": ["SOC 2 Type II", "ISO 27001"],
        "opt_out_training": True,
        "description_cs": "AI asistent integrovan\u00fd do Notion workspace pro generov\u00e1n\u00ed, sumarizaci a organizaci textov\u00e9ho obsahu.",
        "key_risks_cs": ["Ve\u0161ker\u00e1 data ulo\u017eena v USA", "AI funkce zpracov\u00e1vaj\u00ed obsah workspace"],
        "measures_cs": ["Uzav\u0159\u00edt DPA (Team/Enterprise pl\u00e1n)", "Neukl\u00e1dat osobn\u00ed \u00fadaje t\u0159et\u00edch stran do Notion"],
        "monitoring_kpis_cs": ["Po\u010det u\u017eivatel\u016f Notion AI / m\u011bs\u00edc"],
        "training_focus_cs": ["Co Notion AI zpracov\u00e1v\u00e1", "Omezen\u00ed pro citliv\u00fd obsah"],
        "transparency_cs": "Notion AI generuje a sumarizuje obsah na z\u00e1klad\u011b dat ve workspace. V\u00fdstupy jsou strojov\u011b generovan\u00e9.",
    },
    "DeepL": {
        "provider": "DeepL SE",
        "provider_hq": "K\u00f6ln, N\u011bmecko (EU)",
        "website": "https://www.deepl.com",
        "data_regions": ["EU (Finsko \u2014 Hetzner)", "EU (N\u011bmecko)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "DPA sou\u010d\u00e1st Pro/Business smluv; texty v Pro pl\u00e1nu se neukl\u00e1daj\u00ed",
        "gdpr_mechanisms": ["Zpracov\u00e1n\u00ed v\u00fdhradn\u011b v EU", "Bez transferu do t\u0159et\u00edch zem\u00ed"],
        "certifications": ["ISO 27001", "SOC 2 Type II"],
        "opt_out_training": True,
        "description_cs": "P\u0159ekladatelsk\u00fd AI n\u00e1stroj s podporou 30+ jazyk\u016f. Texty v Pro/Business pl\u00e1nu nejsou ukl\u00e1d\u00e1ny ani vyu\u017e\u00edv\u00e1ny k tr\u00e9nov\u00e1n\u00ed.",
        "key_risks_cs": ["Free verze: texty mohou b\u00fdt pou\u017eity ke zlep\u0161en\u00ed modelu", "P\u0159eklad citliv\u00fdch dokument\u016f vy\u017eaduje Pro pl\u00e1n"],
        "measures_cs": ["Pou\u017e\u00edvat v\u00fdhradn\u011b DeepL Pro/Business", "Uzav\u0159\u00edt DPA pro Business pl\u00e1n"],
        "monitoring_kpis_cs": ["Po\u010det p\u0159elo\u017een\u00fdch znak\u016f / m\u011bs\u00edc", "Licence: Free vs Pro (kvart\u00e1ln\u00ed audit)"],
        "training_focus_cs": ["Rozd\u00edl mezi Free a Pro \u2014 GDPR dopady", "Co nep\u0159ekl\u00e1dat p\u0159es DeepL Free"],
        "transparency_cs": "DeepL je AI p\u0159eklada\u010d. V Pro pl\u00e1nu se texty neukl\u00e1daj\u00ed. Ve Free verzi mohou b\u00fdt texty vyu\u017eity ke zlep\u0161en\u00ed slu\u017eby.",
    },
    "Mistral": {
        "provider": "Mistral AI",
        "provider_hq": "Pa\u0159\u00ed\u017e, Francie (EU)",
        "website": "https://mistral.ai",
        "data_regions": ["EU (Francie, Nizozemsko)", "Azure EU (voliteln\u011b)"],
        "eu_based": True,
        "dpa_available": True,
        "dpa_note": "DPA dostupn\u00fd pro API a Enterprise z\u00e1kazn\u00edky",
        "gdpr_mechanisms": ["Zpracov\u00e1n\u00ed v EU", "Bez transferu do t\u0159et\u00edch zem\u00ed (API endpoint EU)"],
        "certifications": ["SOC 2 Type II (v procesu 2025)", "HDS (zdravotnick\u00e1 data, Francie)"],
        "opt_out_training": True,
        "description_cs": "Evropsk\u00fd poskytovatel velk\u00fdch jazykov\u00fdch model\u016f (Mistral Large, Mixtral). API i open-source varianty.",
        "key_risks_cs": ["Open-source modely \u2014 riziko self-hosting bez kontrol", "Relativn\u011b nov\u00fd poskytovatel"],
        "measures_cs": ["Vyu\u017e\u00edvat Mistral API pro zaji\u0161t\u011bn\u00ed logov\u00e1n\u00ed a auditu", "Uzav\u0159\u00edt DPA pro API p\u0159\u00edstup"],
        "monitoring_kpis_cs": ["Po\u010det API vol\u00e1n\u00ed / m\u011bs\u00edc", "Verze modelu v produkci"],
        "training_focus_cs": ["Mistral AI \u2014 evropsk\u00e1 alternativa k OpenAI", "Open-source vs API \u2014 bezpe\u010dnostn\u00ed rozd\u00edly"],
        "transparency_cs": "Mistral AI je evropsk\u00fd LLM poskytovatel. Data jsou zpracov\u00e1na v\u00fdhradn\u011b v EU.",
    },
    "Meta Llama": {
        "provider": "Meta Platforms, Inc.",
        "provider_hq": "Menlo Park, CA, USA",
        "website": "https://ai.meta.com/llama/",
        "data_regions": ["Z\u00e1vis\u00ed na hosting poskytovateli (self-hosted / cloud)"],
        "eu_based": False,
        "gdpr_adequate": False,
        "dpa_available": False,
        "dpa_note": "Open-source model \u2014 DPA z\u00e1vis\u00ed na poskytovateli hostingu",
        "gdpr_mechanisms": ["SCC s hosting poskytovatelem", "Self-hosting v EU eliminuje data transfer"],
        "certifications": [],
        "opt_out_training": True,
        "description_cs": "Open-source rodina velk\u00fdch jazykov\u00fdch model\u016f od Meta. Modely Llama 2/3 lze provozovat self-hosted nebo p\u0159es cloudov\u00e9 API.",
        "key_risks_cs": ["Open-source: bezpe\u010dnost z\u00e1vis\u00ed na provozovateli", "Meta neposkytuje DPA \u2014 odpov\u011bdnost nese deployer"],
        "measures_cs": ["Dokumentovat hosting: kde model b\u011b\u017e\u00ed", "Pokud cloud \u2014 uzav\u0159\u00edt DPA s hosting poskytovatelem", "Jako deployer: splnit povinnosti \u010dl. 26 AI Act"],
        "monitoring_kpis_cs": ["Verze modelu v produkci", "Hosting lokace (EU/non-EU)"],
        "training_focus_cs": ["Open-source AI modely \u2014 odpov\u011bdnost deployera", "\u010cl. 25-26 AI Act: povinnosti poskytovatele vs. nasazovatele"],
        "transparency_cs": "Meta Llama je open-source AI model. Provozovatel nese plnou odpov\u011bdnost za nasazen\u00ed dle AI Act.",
    },
}


# ════════════════════════════════════════════════════════════════════
# 2. ALIAS MAPPING — Bubble labels → KB key
# ════════════════════════════════════════════════════════════════════

_ALIASES: dict[str, str] = {
    # Content section  bubbles
    "ChatGPT/GPT-4o": "ChatGPT",
    # Deepfake section bubbles
    "ChatGPT (Sora)": "Sora",
    "Gemini/VEO3": "VEO3",
    # Chatbot section bubbles
    "ChatGPT API": "ChatGPT",
    "Claude API": "Claude",
    "Gemini API": "Gemini",
    # HR
    "LMC/Jobs.cz AI": "LMC/Jobs.cz AI",
    "Prace.cz AI": "Prace.cz AI",
    # Insurance
    "NESS/Allianz AI": None,  # interní systém — nelze mapovat na generický záznam
    "ČPP/ČSOB interní AI": None,  # interní systém — nelze mapovat na generický záznam
    # Credit
    "Bisnode/D&B": "Bisnode/D&B",
    # Backward compat aliases for renamed products
    "Amazon CodeWhisperer": "Amazon Q Developer",
    "Codeium": "Windsurf",
    # Monitoring types → no specific tool KB
    "Sledování obrazovky": None,
    "Měření produktivity": None,
    "GPS sledování": None,
    "Kamerový dohled s AI": None,
    "Analýza emailů": None,
    # Biometric
    "Kamerový systém": None,
    "Docházkový systém": None,
    "Přístupový systém": None,
    # Safety products (not specific tools)
    "Zdravotnický přístroj": None,
    "Průmyslový stroj": None,
    "Automobil": None,
    "Bezpečnostní systém": None,
    # Decision scopes
    "Reklamace": None,
    "Slevy/ceny": None,
    "Přístup ke službám": None,
    "Schvalování žádostí": None,
    # Children contexts
    "Vzdělávání": None,
    "Mobilní aplikace/hry": None,
    "Doporučování obsahu": None,
    "Chatbot": None,
    "Filtrování obsahu": None,
    # Call center emotion
    "Call centrum analýza": None,
    # -- Questionnaire bubble variants (with parenthetical info) --
    "ChatGPT / GPT-4o": "ChatGPT",
    "ChatGPT (OpenAI — USA)": "ChatGPT",
    "Claude (Anthropic — USA)": "Claude",
    "Claude (Anthropic)": "Claude",
    "Gemini (Google)": "Gemini",
    "Gemini / VEO3 (Google)": "VEO3",
    "Google Gemini (USA/EU)": "Gemini",
    "Google Gemini (USA)": "Gemini",
    "Google Gemini": "Gemini",
    "Google (Gemini)": "Gemini",
    "Anthropic (Claude)": "Claude",
    "OpenAI (GPT-4/4o)": "ChatGPT",
    "Microsoft Copilot": "Copilot",
    "Microsoft Copilot (EU i USA)": "Copilot",
    "Microsoft 365 Copilot": "Copilot",
    "Perplexity (USA)": "Perplexity",
    "Midjourney (USA)": "Midjourney",
    "Jasper AI (USA)": "Jasper",
    "Jasper AI": "Jasper",
    "CRIF – Czech Credit Bureau": "CRIF",
    "Bisnode / Dun & Bradstreet": "Bisnode/D&B",
    "NESS / Allianz AI": None,
    "ČPP / ČSOB interní AI": None,
    "Meta (Llama)": "Meta Llama",
    "Grammarly (USA)": "Grammarly",
    "Notion AI (USA)": "Notion AI",
    "DeepL (Německo/EU)": "DeepL",
    "Vlastní server v ČR/EU": None,
    "Vlastní model": None,
    "Chatbot / virtuální asistent": None,
}


# ════════════════════════════════════════════════════════════════════
# 3. USE-CASE / RISK CATEGORY KB — per-question_key text blocks
# ════════════════════════════════════════════════════════════════════
# Pre-written obligation and risk description for each questionnaire key.

USE_CASE_KB: dict[str, dict] = {
    "uses_chatgpt": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Čl. 50 odst. 1 AI Act ukládá povinnost informovat uživatele, že komunikují "
            "s AI systémem. Pokud je ChatGPT nasazen jako chatbot na webu, musí být viditelně "
            "označen. Čl. 4 vyžaduje zajištění AI gramotnosti zaměstnanců."
        ),
        "deployer_duties_cs": [
            "Zajistit transparenční oznámení dle čl. 50",
            "Proškolit zaměstnance v odpovědném používání LLM",
            "Zakázat vkládání osobních údajů do promptů (interní politika)",
            "Uzavřít DPA s poskytovatelem (OpenAI)",
        ],
    },
    "uses_copilot": {
        "risk_category": "minimální",
        "ai_act_obligations_cs": (
            "Kódovací asistenti jako GitHub Copilot spadají do kategorie minimálního rizika. "
            "Nejsou stanoveny povinnosti dle AI Act nad rámec čl. 4 (AI gramotnost). "
            "Doporučeno: code review AI-generovaného kódu, bezpečnostní skeny."
        ),
        "deployer_duties_cs": [
            "Proškolit vývojáře v bezpečném použití AI kodéru",
            "Zavést povinný code review AI kódu",
            "Aktivovat opt-out z trénování na firemním kódu",
        ],
    },
    "uses_ai_content": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Čl. 50 odst. 4 AI Act: AI-generovaný obsah (obrázky, texty, audio) musí být "
            "označen jako vytvořený umělou inteligencí. Toto platí pro veškerý obsah publikovaný "
            "veřejně. Interní dokumenty označení nevyžadují."
        ),
        "deployer_duties_cs": [
            "Označit všechen veřejně publikovaný AI obsah",
            "Redakční kontrola před publikací",
            "Školení zaměstnanců v označování AI obsahu",
        ],
    },
    "uses_deepfake": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Čl. 50 odst. 4 AI Act stanoví přísnou povinnost: AI-generovaná videa a syntetická "
            'média musí být zřetelně označena jako \u201edeep fake\u201c nebo jako vytvořená AI. '
            "To platí BEZ výjimky pro všechna veřejně sdílená média."
        ),
        "deployer_duties_cs": [
            "Vždy označit syntetické video/audio jako AI-generované",
            "Zákaz deepfake reálných osob bez výslovného souhlasu",
            "Zavést log generování: kdo, kdy, jaký obsah, účel",
            "Školení zaměstnanců o etice a právních rizicích deepfake",
        ],
    },
    "uses_ai_recruitment": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ SYSTÉM — čl. 6 odst. 2 + Příloha III bod 4(a): AI systémy "
            "pro nábor, screening a hodnocení uchazečů o zaměstnání. Povinnosti nasazovatele: "
            "lidský dohled (čl. 14), logging (čl. 12), FRIA (čl. 27), QMS (čl. 17), "
            "informování zaměstnanců (čl. 26 odst. 7)."
        ),
        "deployer_duties_cs": [
            "Implementovat POVINNÝ lidský dohled — AI nesmí rozhodovat samo",
            "Provést FRIA (posouzení dopadu na základní práva) dle čl. 27",
            "Dokumentovat použití AI v náborovém procesu dle čl. 26",
            "Informovat zaměstnaneckou radu a uchazeče o použití AI",
            "Uchovávat logy rozhodnutí min. 6 měsíců dle čl. 19",
            "Pravidelný audit nediskriminace (věk, pohlaví, etnicita)",
        ],
    },
    "uses_ai_employee_monitoring": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ SYSTÉM — Příloha III bod 4(b): AI monitoring zaměstnanců. "
            "Sledování produktivity, obrazovky, GPS nebo emailů pomocí AI podléhá přísným "
            "povinnostem. Zaměstnanci musí být prokazatelně informováni."
        ),
        "deployer_duties_cs": [
            "Informovat zaměstnance o AI monitoringu dle čl. 26 odst. 7",
            "Lidský dohled nad výstupy monitoringu",
            "FRIA + DPIA — monitoring zpracovává citlivá data",
            "Přiměřenost — monitorovat jen nezbytné aspekty",
        ],
    },
    "uses_emotion_recognition": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ — čl. 50 odst. 3: systémy rozpoznávání emocí podléhají povinnosti "
            "transparentnosti. Na pracovišti je rozpoznávání emocí zakázáno (čl. 5 odst. 1(f)), "
            "s omezenými výjimkami pro bezpečnost."
        ),
        "deployer_duties_cs": [
            "Ověřit, zda se na systém nevztahuje zákaz dle čl. 5",
            "Informovat dotčené osoby dle čl. 50 odst. 3",
            "Provést DPIA + FRIA",
        ],
    },
    "uses_ai_accounting": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "AI v účetnictví spadá převážně do kategorie omezeného nebo minimálního rizika. "
            "Čl. 4 AI Act vyžaduje AI gramotnost zaměstnanců pracujících s AI účetním softwarem. "
            "Pokud AI automaticky vytváří daňová přiznání, doporučen lidský přezkum."
        ),
        "deployer_duties_cs": [
            "Kontrola AI-navržených účetních zápisů kvalifikovaným účetním",
            "AI nesmí samostatně podávat daňová přiznání",
            "Školení účetních v práci s AI funkcemi",
        ],
    },
    "uses_ai_creditscoring": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ SYSTÉM — Příloha III bod 5(b): AI systémy pro hodnocení "
            "kreditní bonity fyzických osob. Povinný lidský přezkum, FRIA, logging, "
            "právo na vysvětlení rozhodnutí (čl. 86)."
        ),
        "deployer_duties_cs": [
            "Lidský přezkum každého negativního kreditního rozhodnutí",
            "Právo osoby na vysvětlení rozhodnutí dle čl. 86",
            "FRIA dle čl. 27",
            "Audit nediskriminace kreditního modelu",
            "Logging rozhodnutí min. 6 měsíců",
        ],
    },
    "uses_ai_insurance": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ SYSTÉM — Příloha III bod 5(c): AI v pojišťovnictví pro "
            "posuzování rizik, tarifikaci a likvidaci pojistných událostí."
        ),
        "deployer_duties_cs": [
            "Lidský přezkum zamítnutí pojistného plnění",
            "Transparentnost vůči klientům",
            "FRIA + audit nediskriminace",
        ],
    },
    "uses_ai_chatbot": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Čl. 50 odst. 1 AI Act: uživatelé chatbotu MUSÍ být informováni, že komunikují "
            "s AI systémem. Oznámení musí být zřejmé PŘED zahájením nebo na začátku interakce. "
            "Výjimka pouze pokud je to zřejmé z kontextu (čl. 50 odst. 1)."
        ),
        "deployer_duties_cs": [
            'Zobrazit jasné oznámení: \u201eKomunikujete s AI asistentem.\u201c',
            "Nabídnout možnost přepojení na lidského operátora",
            "Logovat konverzace pro kvalitu a compliance",
            "Uzavřít DPA s poskytovatelem chatbotu",
        ],
    },
    "uses_ai_email_auto": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "AI automatizace emailové komunikace spadá do omezeného rizika dle čl. 50. "
            "Pokud je AI obsah neodlišitelný od lidského, je vhodné informovat příjemce."
        ),
        "deployer_duties_cs": [
            "Zvážit informování zákazníků o AI asistenci v emailech",
            "Kontrola automatických odpovědí před odesláním (nebo sampling)",
            "DPA s poskytovatelem emailového AI",
        ],
    },
    "uses_ai_decision": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ — AI rozhodující o přístupu ke službám, reklamacích nebo "
            "schvalování žádostí může spadat pod Přílohu III bod 5(b). Povinný lidský přezkum."
        ),
        "deployer_duties_cs": [
            "Lidský přezkum každého zamítnutí žádosti zákazníka",
            "Právo zákazníka na vysvětlení AI rozhodnutí",
            "Logging rozhodnutí",
        ],
    },
    "uses_dynamic_pricing": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Dynamická cenotvorba spadá do omezeného rizika. Pozor na potenciální cenovou "
            "diskriminaci a algoritmickou kolůzzi. Doporučena transparentní cenová politika."
        ),
        "deployer_duties_cs": [
            "Lidský dohled nad extrémními cenovými změnami",
            "Audit na cenovou diskriminaci",
            "Transparentní cenová politika",
        ],
    },
    "uses_ai_for_children": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ — AI systémy cílené na děti podléhají zvýšené ochraně. "
            "Požadavky na bezpečnost, srozumitelnost a ochranu osobních údajů dětí (GDPR + AI Act)."
        ),
        "deployer_duties_cs": [
            "Zvýšená ochrana osobních údajů dětí",
            "Rodičovský souhlas pro zpracování dat",
            "Content moderation vhodný pro děti",
            "FRIA se zaměřením na dopady na nezletilé",
        ],
    },
    "uses_ai_critical_infra": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ SYSTÉM — Příloha III bod 2: AI v kritické infrastruktuře. "
            "Přísné požadavky na bezpečnost, redundanci, lidský dohled a QMS. "
            "Povinný FRIA, pravidelné audity, incident management."
        ),
        "deployer_duties_cs": [
            "Fail-safe mechanismy nezávislé na AI",
            "24/7 lidský dohled nad AI řízením",
            "Redundantní systémy",
            "QMS dle čl. 17, bezpečnostní audity",
            "Incident plán specifický pro AI v kritické infrastruktuře",
        ],
    },
    "uses_ai_safety_component": {
        "risk_category": "vysoké",
        "ai_act_obligations_cs": (
            "VYSOCE RIZIKOVÝ — čl. 6 odst. 1: AI jako bezpečnostní komponenta produktu "
            "podléhající harmonizační legislativě EU (zdravotnické prostředky, stroje, atd.)."
        ),
        "deployer_duties_cs": [
            "Compliance s příslušnou harmonizační legislativou",
            "CE označení a posouzení shody",
            "Bezpečnostní testy AI komponenty",
        ],
    },
    "develops_own_ai": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Jako vývojář AI má firma roli poskytovatele (provider) dle čl. 3(2) AI Act. "
            "Povinnosti závisí na rizikovém profilu vyvíjeného systému."
        ),
        "deployer_duties_cs": [
            "Provést klasifikaci rizika vyvíjeného AI systému",
            "Implementovat vhodná opatření dle rizikové kategorie",
            "Dokumentace technická dle čl. 11 (high-risk)",
        ],
    },
    "modifies_ai_purpose": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Čl. 25 AI Act: pokud firma změní zamýšlený účel AI systému, stává se poskytovatelem "
            "(provider) tohoto pozměněného systému se VŠEMI povinnostmi poskytovatele."
        ),
        "deployer_duties_cs": [
            "Ověřit nový účel vs. originální zamýšlený účel poskytovatele",
            "Přivzít odpovědnost poskytovatele při změně účelu",
        ],
    },
    "uses_gpai_api": {
        "risk_category": "omezené",
        "ai_act_obligations_cs": (
            "Čl. 51-56 AI Act (GPAI): při použití API k general-purpose AI modelu firma přebírá "
            "povinnosti nasazovatele. Musí zajistit transparentnost a AI gramotnost."
        ),
        "deployer_duties_cs": [
            "Transparentní oznámení o použití AI",
            "Uzavřít DPA s poskytovatelem GPAI",
            "Zajistit AI gramotnost dle čl. 4",
        ],
    },
}


# ════════════════════════════════════════════════════════════════════
# 4. PUBLIC API — funkce pro rest systému
# ════════════════════════════════════════════════════════════════════

def lookup_tool(name: str) -> Optional[dict]:
    """Najde nástroj v KB podle jména (přesný match nebo alias)."""
    if not name:
        return None
    name = name.strip()
    # Direct lookup
    if name in TOOL_KB:
        return TOOL_KB[name]
    # Alias lookup (None value = known non-tool)
    if name in _ALIASES:
        alias = _ALIASES[name]
        if alias is not None and alias in TOOL_KB:
            return TOOL_KB[alias]
        return None  # explicitly mapped to None
    # Case-insensitive fuzzy match on TOOL_KB
    name_lower = name.lower()
    for kb_name, kb_data in TOOL_KB.items():
        if kb_name.lower() == name_lower:
            return kb_data
    # Case-insensitive alias match
    for alias_name, alias_target in _ALIASES.items():
        if alias_name.lower() == name_lower:
            if alias_target and alias_target in TOOL_KB:
                return TOOL_KB[alias_target]
            return None
    return None


def lookup_tools_multi(name: str) -> list:
    """Rozloží čárkové/spojkové tool names a vrátí seznam KB lookupů.
    Např. 'ChatGPT, Claude' -> [<ChatGPT KB>, <Claude KB>].
    Vrací alespoň 1-prvkový seznam. None = NOT in KB.
    """
    if not name:
        return [None]
    parts = [p.strip() for p in name.replace(" a ", ", ").split(",") if p.strip()]
    if not parts:
        return [None]
    return [lookup_tool(p) for p in parts]


def is_known_tool(name: str) -> bool:
    """Vrací True pokud nástroj je v KB."""
    return lookup_tool(name) is not None


def enrich_systems_with_kb(ai_systems: list) -> list:
    """
    Obohatí ai_systems_declared o KB data.
    Přidá pole: kb_provider, kb_data_regions, kb_dpa, kb_gdpr, kb_certifications,
    kb_description, kb_risks, kb_measures, kb_known.
    """
    enriched = []
    for sys in ai_systems:
        sys = dict(sys)  # copy
        tool_name = sys.get("tool_name", "")
        kb = lookup_tool(tool_name)
        key = sys.get("key", "")
        use_case = USE_CASE_KB.get(key, {})

        if kb:
            sys["kb_known"] = True
            sys["kb_provider"] = kb.get("provider", "")
            sys["kb_provider_hq"] = kb.get("provider_hq", "")
            sys["kb_website"] = kb.get("website", "")
            sys["kb_data_regions"] = kb.get("data_regions", [])
            sys["kb_eu_based"] = kb.get("eu_based", False)
            sys["kb_dpa_available"] = kb.get("dpa_available", False)
            sys["kb_dpa_note"] = kb.get("dpa_note", "")
            sys["kb_gdpr_mechanisms"] = kb.get("gdpr_mechanisms", [])
            sys["kb_certifications"] = kb.get("certifications", [])
            sys["kb_description"] = kb.get("description_cs", "")
            sys["kb_risks"] = kb.get("key_risks_cs", [])
            sys["kb_measures"] = kb.get("measures_cs", [])
            sys["kb_monitoring_kpis"] = kb.get("monitoring_kpis_cs", [])
            sys["kb_training_focus"] = kb.get("training_focus_cs", [])
            sys["kb_transparency"] = kb.get("transparency_cs", "")
        else:
            sys["kb_known"] = False
            logger.info(f"[KB] Nástroj '{tool_name}' není v KB — bude použit LLM fallback")

        # Use-case data (always available regardless of tool)
        if use_case:
            sys["kb_obligations"] = use_case.get("ai_act_obligations_cs", "")
            sys["kb_deployer_duties"] = use_case.get("deployer_duties_cs", [])

        enriched.append(sys)
    return enriched


def all_tools_known(ai_systems: list) -> bool:
    """Vrací True pokud VŠECHNY deklarované nástroje jsou v KB.
    Prázdný seznam -> False (nemá smysl generovat KB pre-content bez systémů)."""
    if not ai_systems:
        return False
    return all(s.get("kb_known", False) for s in ai_systems)


# ════════════════════════════════════════════════════════════════════
# 5. KB CONTEXT BLOCK — pro injektáž faktů do LLM promptů
# ════════════════════════════════════════════════════════════════════

def build_kb_context_for_llm(ai_systems: list, findings: list = None) -> str:
    """
    Sestaví blok KB faktů pro vložení do LLM company contextu.
    LLM tak dostane správná fakta a nebude hallucinate.
    """
    if not ai_systems and not findings:
        return ""

    lines = [
        f"\n════ OVĚŘENÁ FAKTA Z KNOWLEDGE BASE (použij PŘESNĚ, nehallucinate) ════",
        f"Stav dat: {KB_VERSION_DATE}. Zdroj: veřejně dostupné informace z webů poskytovatelů.",
        f"DŮLEŽITÉ: Do každé sekce vlož zmínku, že údaje o dodavatelích jsou ke dni {KB_VERSION_DATE}.",
        ""
    ]

    # Web scan findings → lookup KB
    for f in (findings or []):
        name = f.get("name", "")
        kb = lookup_tool(name)
        if kb:
            lines.append(f"[Web] {name}:")
            lines.append(f"  Poskytovatel: {kb['provider']} ({kb['provider_hq']})")
            regions = ", ".join(kb.get("data_regions", []))
            lines.append(f"  Data: {regions}")
            gdpr = ", ".join(kb.get("gdpr_mechanisms", []))
            lines.append(f"  GDPR: {gdpr}")
            if kb.get("certifications"):
                lines.append(f"  Certifikace: {', '.join(kb['certifications'])}")
            if kb.get("dpa_available"):
                lines.append(f"  DPA: ✅ {kb.get('dpa_note', 'dostupná')}")
            else:
                lines.append(f"  DPA: ⚠️ {kb.get('dpa_note', 'není k dispozici')}")
            lines.append("")

    # Declared AI systems → lookup KB + use case
    for s in ai_systems:
        if not s.get("kb_known"):
            lines.append(f"[Dotazník] {s.get('tool_name', '?')}: NEZNÁMÝ NÁSTROJ — vygeneruj vlastní analýzu.")
            lines.append("")
            continue

        tool_name = s.get("tool_name", "?")
        lines.append(f"[Dotazník] {tool_name}:")
        lines.append(f"  Poskytovatel: {s.get('kb_provider', '?')} ({s.get('kb_provider_hq', '?')})")
        if s.get("kb_data_regions"):
            lines.append(f"  Uložení dat: {', '.join(s['kb_data_regions'])}")
        if s.get("kb_gdpr_mechanisms"):
            lines.append(f"  GDPR: {', '.join(s['kb_gdpr_mechanisms'])}")
        if s.get("kb_certifications"):
            lines.append(f"  Certifikace: {', '.join(s['kb_certifications'])}")
        if s.get("kb_dpa_available"):
            lines.append(f"  DPA: ✅ {s.get('kb_dpa_note', 'dostupná')}")
        if s.get("kb_description"):
            lines.append(f"  Popis: {s['kb_description']}")
        if s.get("kb_obligations"):
            lines.append(f"  AI Act povinnosti: {s['kb_obligations']}")
        if s.get("kb_risks"):
            for r in s["kb_risks"]:
                lines.append(f"  ⚠️ Riziko: {r}")
        if s.get("kb_measures"):
            for m in s["kb_measures"]:
                lines.append(f"  ✅ Opatření: {m}")
        lines.append("")

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# 6. PRE-WRITTEN SECTION GENERATORS — statický obsah z KB dat
# ════════════════════════════════════════════════════════════════════

def _vendor_paragraph(tool_name: str, info: dict) -> str:
    """Generuje HTML odstavec hodnocení jednoho dodavatele z KB dat."""
    generic_warning = ""
    if info.get("is_generic_entry"):
        generic_warning = (
            "<p style='color:#c0392b;font-weight:bold'>"
            "\u26a0\ufe0f Toto je generický záznam — klient neuvedl konkrétního poskytovatele. "
            "Všechny údaje níže jsou obecné a musí být ověřeny u konkrétního dodavatele.</p>"
        )
    regions = ", ".join(info.get("data_regions", ["nespecifikováno"]))
    gdpr = ", ".join(info.get("gdpr_mechanisms", [])) or "nespecifikováno"
    certs = ", ".join(info.get("certifications", [])) or "neuvedeny"
    eu_badge = "🟢 EU poskytovatel" if info.get("eu_based") else "🟡 Mimounijní poskytovatel"

    if info.get("dpa_available"):
        dpa_html = f"Poskytovatel nabízí DPA (Data Processing Agreement) — <em>{info.get('dpa_note', 'dostupná na vyžádání')}</em>."
    else:
        dpa_html = ("<strong style='color:#c0392b'>Poskytovatel nemá veřejně dostupnou DPA</strong> — "
                    "doporučujeme vyžádat smluvní zajištění před dalším používáním.")

    risks_html = ""
    if info.get("key_risks_cs"):
        items = "".join(f"<li>{r}</li>" for r in info["key_risks_cs"])
        risks_html = f"<ul>{items}</ul>"

    measures_html = ""
    if info.get("measures_cs"):
        items = "".join(f"<li>{m}</li>" for m in info["measures_cs"])
        measures_html = f"<p><strong>Doporučená opatření:</strong></p><ul>{items}</ul>"

    # Adequacy note for non-EU but adequate jurisdictions (UK, Switzerland)
    adequacy_note = ""
    if info.get("gdpr_adequate") and not info.get("eu_based"):
        adequacy_note = f" ({info.get('gdpr_adequate_note', 'země má rozhodnutí o přiměřenosti od EU')})"

    former = ""
    if info.get("former_name"):
        former = f" <em>(dříve: {info['former_name']})</em>"

    return (
        f"<h4>{tool_name}{former} — {info.get('provider', 'neznámý poskytovatel')}</h4>"
        f"{generic_warning}"
        f"<p>{eu_badge}{adequacy_note} | Sídlo: {info.get('provider_hq', '?')} | "
        f"Zpracování dat: {regions}</p>"
        f"<p>{dpa_html}</p>"
        f"<p>GDPR mechanismy: {gdpr}. Certifikace: {certs}.</p>"
        f"{risks_html}"
        f"{measures_html}"
    )


def generate_vendor_assessment_kb(ai_systems: list, findings: list = None) -> Optional[str]:
    """
    Generuje kompletní vendor assessment HTML z KB dat.
    Vrací None pokud některý nástroj NENÍ v KB (= nutný LLM).
    """
    paragraphs = []

    # Web findings → vendor info
    seen_providers = set()
    for f in (findings or []):
        name = f.get("name", "")
        kb = lookup_tool(name)
        if kb:
            provider = kb.get("provider", "")
            if provider not in seen_providers:
                seen_providers.add(provider)
                paragraphs.append(_vendor_paragraph(name, kb))

    # Declared systems → vendor info
    unknown_tools = []
    for s in ai_systems:
        tool_name = s.get("tool_name", "")
        kb = lookup_tool(tool_name)
        if kb:
            provider = kb.get("provider", "")
            if provider not in seen_providers:
                seen_providers.add(provider)
                paragraphs.append(_vendor_paragraph(tool_name, kb))
        else:
            unknown_tools.append(tool_name)

    if unknown_tools:
        # Some tools not in KB → can't fully generate, return None for LLM fallback
        return None

    if not paragraphs:
        return None

    header = (
        "<p>Následuje hodnocení dodavatelů AI nástrojů detekovaných v rámci analýzy. "
        "Pro každého poskytovatele uvádíme klíčové informace o zpracování dat, GDPR souladu "
        "a doporučená opatření. K hodnocení dodavatelů využijte <strong>Dodavatelský checklist</strong>, "
        "který jste obdrželi v Compliance Kitu — obsahuje konkrétní otázky pro každého dodavatele.</p>"
    )

    footer = (
        "<p><strong>Doporučení:</strong> U každého dodavatele si ověřte: (1) kde se zpracovávají data, "
        "(2) zda se model trénuje na vašich datech, (3) jaké certifikace dodavatel má, "
        "(4) zda má platnou DPA dle GDPR. Tyto informace získáte přímo od dodavatele — "
        "AIshield nemůže vstupovat do smluvních vztahů klienta s třetími stranami.</p>"
    )

    return header + "\n".join(paragraphs) + footer + get_vendor_footer()


def generate_chatbot_notices_kb(ai_systems: list, findings: list = None) -> Optional[str]:
    """
    Generuje HTML sekci transparenčních oznámení z KB dat.
    Vrací None pokud některý nástroj NENÍ v KB.
    """
    notices = []
    seen = set()

    all_tools = []
    for f in (findings or []):
        all_tools.append((f.get("name", ""), f.get("category", "")))
    for s in ai_systems:
        all_tools.append((s.get("tool_name", ""), s.get("key", "")))

    for tool_name, cat_or_key in all_tools:
        kb = lookup_tool(tool_name)
        if not kb:
            return None  # Unknown tool → LLM fallback
        if tool_name in seen:
            continue
        seen.add(tool_name)

        note = kb.get("transparency_cs", "")
        if note:
            notices.append(f'<li><strong>{tool_name}</strong>: \u201e{note}\u201c</li>')

    if not notices:
        return None

    return (
        "<p>Na základě analýzy vašich AI systémů uvádíme doporučené transparenční texty "
        "dle čl. 50 AI Act. Texty oznámení i HTML kód transparenční stránky jste obdrželi "
        "v Compliance Kitu — stačí je nasadit na váš web.</p>"
        "<h4>Povinná oznámení dle čl. 50 odst. 1 (chatboty):</h4>"
        '<p>Každý AI chatbot musí zobrazit oznámení: \u201eKomunikujete s AI asistentem.\u201c '
        "Toto oznámení musí být viditelné PŘED nebo na začátku interakce.</p>"
        "<h4>Doporučené transparenční texty pro vaše AI systémy:</h4>"
        f"<ul>{''.join(notices)}</ul>"
        "<p>Tyto texty umístěte na viditelné místo na webových stránkách, v chatbot oknech, "
        "v emailových patičkách a na transparenční stránce, jejíž HTML kód jste obdrželi.</p>"
        + get_vendor_footer()
    )


def generate_monitoring_kpis_kb(ai_systems: list) -> Optional[str]:
    """
    Generuje HTML sekci monitorovacích KPIs z KB dat.
    Vrací None pokud některý nástroj NENÍ v KB.
    """
    kpi_sections = []

    for s in ai_systems:
        tool_name = s.get("tool_name", "")
        kb = lookup_tool(tool_name)
        if not kb:
            return None
        kpis = kb.get("monitoring_kpis_cs", [])
        if kpis:
            items = "".join(f"<li>{k}</li>" for k in kpis)
            risk = s.get("risk_level", "minimal")
            freq = "týdně" if risk == "high" else ("měsíčně" if risk == "limited" else "kvartálně")
            kpi_sections.append(
                f"<h4>{tool_name}</h4>"
                f"<p>Doporučená frekvence monitoringu: <strong>{freq}</strong></p>"
                f"<ul>{items}</ul>"
            )

    if not kpi_sections:
        return None

    return (
        "<p>Monitoring plán jste obdrželi v Compliance Kitu. "
        "Implementujte ho do svých IT procesů — např. přidejte kontrolu AI výstupů "
        "do týdenního IT review meetingu. Následují konkrétní KPI metriky pro vaše AI systémy:</p>"
        + "\n".join(kpi_sections)
        + get_vendor_footer()
    )


def generate_risk_analysis_kb(ai_systems: list, findings: list = None) -> Optional[str]:
    """
    Generuje HTML sekci analýzy rizik z KB + USE_CASE_KB dat.
    Vrací None pokud některý nástroj NENÍ v KB.
    """
    sections = []

    # Web findings
    for f in (findings or []):
        name = f.get("name", "")
        kb = lookup_tool(name)
        rl = f.get("risk_level", "minimal")
        article = f.get("ai_act_article", "")
        badge = _risk_badge_text(rl)

        paragraph = (
            f"<h4>{name} — {badge}</h4>"
            f"<p>Detekováno na webových stránkách firmy. "
            f"Kategorie: {f.get('category', '?')}. "
            f"Relevantní článek AI Act: {article or 'neurčen'}.</p>"
        )
        if kb:
            if kb.get("key_risks_cs"):
                items = "".join(f"<li>{r}</li>" for r in kb["key_risks_cs"])
                paragraph += f"<p><strong>Identifikovaná rizika:</strong></p><ul>{items}</ul>"
        sections.append(paragraph)

    # Declared systems
    for s in ai_systems:
        tool_name = s.get("tool_name", "")
        kb = lookup_tool(tool_name)
        if not kb:
            return None  # Unknown → LLM fallback

        key = s.get("key", "")
        use_case = USE_CASE_KB.get(key, {})
        rl = s.get("risk_level", "minimal")
        article = s.get("ai_act_article", "")
        badge = _risk_badge_text(rl)

        paragraph = (
            f"<h4>{tool_name} — {badge}</h4>"
            f"<p>{kb.get('description_cs', '')} "
            f"Poskytovatel: {kb.get('provider', '?')} ({kb.get('provider_hq', '?')}). "
            f"Relevantní článek AI Act: {article or 'neurčen'}.</p>"
        )
        if use_case.get("ai_act_obligations_cs"):
            paragraph += f"<p>{use_case['ai_act_obligations_cs']}</p>"
        if kb.get("key_risks_cs"):
            items = "".join(f"<li>{r}</li>" for r in kb["key_risks_cs"])
            paragraph += f"<p><strong>Identifikovaná rizika:</strong></p><ul>{items}</ul>"
        if use_case.get("deployer_duties_cs"):
            items = "".join(f"<li>{d}</li>" for d in use_case["deployer_duties_cs"])
            paragraph += f"<p><strong>Povinnosti nasazovatele:</strong></p><ul>{items}</ul>"

        sections.append(paragraph)

    if not sections:
        return None

    return "\n".join(sections) + get_vendor_footer()


def _risk_badge_text(rl: str) -> str:
    """Vrátí textový badge rizikové kategorie."""
    return {
        "high": "🔴 VYSOKÉ RIZIKO",
        "limited": "🟡 Omezené riziko",
        "minimal": "🟢 Minimální riziko",
        "prohibited": "⛔ ZAKÁZÁNO",
    }.get(rl, rl)




def generate_transparency_oversight_kb(
    ai_systems: list,
    findings: list = None,
    human_oversight: dict = None,
    incident: dict = None,
) -> Optional[str]:
    """
    Generuje HTML sekci Transparentnost a lidský dohled z KB dat.
    Kombinuje:
      1) Univerzální poučky o čl. 13, 14, 50 AI Act (stejné pro všechny)
      2) Per-tool transparenční texty z TOOL_KB
      3) Per-use-case povinnosti dohledu z USE_CASE_KB
      4) Dynamický stav opatření z dotazníku
    Vrací None pokud některý nástroj NENÍ v KB (= nutný LLM fallback).
    """
    human_oversight = human_oversight or {}
    incident = incident or {}

    # ── Univerzální právní základ (čl. 13, 14, 50) ──
    html_parts = [
        "<h4>Právní rámec transparentnosti a lidského dohledu</h4>",
        "<p>Nařízení EU 2024/1689 (AI Act) stanoví tři klíčové povinnosti:</p>",
        "<ul>",
        "<li><strong>Čl. 13 — Transparentnost:</strong> Vysoce rizikové AI systémy "
        "musí být navrženy tak, aby jejich provoz byl dostatečně transparentní — "
        "uživatelé musí rozumět výstupům a omezením systému.</li>",
        "<li><strong>Čl. 14 — Lidský dohled:</strong> Vysoce rizikové AI systémy musí "
        "umožňovat účinný lidský dohled — včetně možnosti přerušit provoz (kill switch), "
        "přepsat rozhodnutí AI (override) a průběžně monitorovat výstupy.</li>",
        "<li><strong>Čl. 50 — Povinnosti transparentnosti pro všechny AI systémy:</strong> "
        "Uživatelé musí být informováni, že komunikují s AI (odst. 1). AI-generovaný "
        "obsah musí být označen (odst. 4). Systémy rozpoznávání emocí musí informovat "
        "dotčené osoby (odst. 3).</li>",
        "</ul>",
    ]

    # ── Stav opatření z dotazníku ──
    can_override = human_oversight.get("can_override", False)
    has_logging = human_oversight.get("has_logging", False)
    monitors_outputs = incident.get("monitors_outputs", False)

    _yes = "✅ Zavedeno"
    _no_override = "⚠️ Nezavedeno — nutné implementovat dle čl. 14 odst. 4 písm. d)"
    _no_logging = "⚠️ Nezavedeno — čl. 26 odst. 1 písm. f) vyžaduje uchovávání logů min. 6 měsíců"
    _no_monitor = "⚠️ Nezavedeno — čl. 9 vyžaduje průběžné řízení rizik včetně monitoringu"
    html_parts.append("<h4>Aktuální stav opatření ve vaší firmě</h4>")
    html_parts.append("<ul>")
    html_parts.append(f'<li><strong>Možnost přerušení/přepsání AI:</strong> {_yes if can_override else _no_override}</li>')
    html_parts.append(f'<li><strong>Logování AI rozhodnutí:</strong> {_yes if has_logging else _no_logging}</li>')
    html_parts.append(f'<li><strong>Monitoring výstupů AI:</strong> {_yes if monitors_outputs else _no_monitor}</li>')
    html_parts.append("</ul>")

    # ── Per-tool transparenční texty ──
    tool_notices = []
    seen = set()

    all_tools = []
    for f in (findings or []):
        all_tools.append((f.get("name", ""), f.get("risk_level", "minimal"), f.get("category", "")))
    for s in ai_systems:
        tn = s.get("tool_name") or s.get("key") or ""
        rl = (s.get("details") or {}).get("risk_level") or s.get("risk_level", "minimal")
        all_tools.append((tn, rl, s.get("key", "")))

    for tool_name, risk_level, cat_or_key in all_tools:
        if not tool_name or tool_name in seen:
            continue
        seen.add(tool_name)

        kb = lookup_tool(tool_name)
        if not kb:
            return None  # Neznámý nástroj → LLM fallback

        transparency_text = kb.get("transparency_cs", "")
        badge = _risk_badge_text(risk_level)

        notice = f"<li><strong>{tool_name}</strong> ({badge})"
        if transparency_text:
            notice += f": \u201e{transparency_text}\u201c"

        # Per-use-case povinnosti dohledu
        use_case = USE_CASE_KB.get(cat_or_key, {})
        duties = use_case.get("deployer_duties_cs", [])
        if duties:
            notice += "<br><em>Povinnosti dohledu:</em> " + "; ".join(duties)

        notice += "</li>"
        tool_notices.append(notice)

    if tool_notices:
        html_parts.append("<h4>Transparentnost a dohled pro vaše AI systémy</h4>")
        html_parts.append(f'<ul>{"".join(tool_notices)}</ul>')

    # ── Doporučení k implementaci ──
    html_parts.append("<h4>Doporučení k implementaci</h4>")
    html_parts.append("<ul>")
    html_parts.append(
        "<li><strong>Kill switch:</strong> Každý AI systém musí být možné kdykoli "
        "zastavit. Testujte kill switch minimálně kvartálně.</li>"
    )
    html_parts.append(
        "<li><strong>Override:</strong> Zaměstnanci musí mít možnost AI rozhodnutí "
        "přepsat nebo zrušit (čl. 14 odst. 4 písm. d). Nastavte eskalační procesy.</li>"
    )
    html_parts.append(
        "<li><strong>Monitoring:</strong> Pravidelně kontrolujte kvalitu výstupů AI. "
        "Doporučená frekvence: vysoce rizikové = týdně, omezené riziko = měsíčně, "
        "minimální riziko = kvartálně.</li>"
    )
    html_parts.append(
        "<li><strong>Kompetence:</strong> Odpovědná osoba za AI dohled musí být "
        "proškolena (AI literacy dle čl. 4 AI Act).</li>"
    )
    html_parts.append(
        "<li><strong>Archivace:</strong> Záznamy o transparentnosti a dohledu "
        "uchovávejte po dobu provozu AI systému + 10 let (čl. 18 AI Act).</li>"
    )
    html_parts.append("</ul>")

    html_parts.append(
        "<p><em>Záznamový list pro čtvrtletní kontrolu transparentnosti a dohledu "
        "jste obdrželi v Compliance Kitu — vyplňujte ho pravidelně a archivujte.</em></p>"
    )
    html_parts.append(get_vendor_footer())

    return "\n".join(html_parts)




def kb_coverage_report(ai_systems: list, findings: list = None) -> dict:
    """Vrací statistiku pokrytí KB."""
    total_declared = len(ai_systems)
    known_declared = sum(1 for s in ai_systems if s.get("kb_known"))
    total_findings = len(findings or [])
    known_findings = sum(1 for f in (findings or []) if lookup_tool(f.get("name", "")))

    return {
        "declared_total": total_declared,
        "declared_known": known_declared,
        "declared_unknown": total_declared - known_declared,
        "findings_total": total_findings,
        "findings_known": known_findings,
        "full_coverage": (known_declared == total_declared) and (known_findings == total_findings),
        "coverage_pct": round(
            (known_declared + known_findings) / max(total_declared + total_findings, 1) * 100
        ),
    }
