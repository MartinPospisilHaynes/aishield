"""
AIshield.cz — Questionnaire API
Backend pro interaktivní dotazník o interních AI systémech.

Dotazník pokrývá oblasti, které skener webu nevidí:
- Odvětví firmy (přizpůsobení dotazníku)
- Zakázané AI praktiky (čl. 5)
- Interní AI nástroje (ChatGPT, Copilot, generování obsahu)
- HR (AI pro nábor, monitoring zaměstnanců)
- Finance (AI účetnictví, credit scoring, pojišťovnictví)
- Zákaznický servis (AI emaily, automatická rozhodnutí)
- Kritická infrastruktura a bezpečnost
- Ochrana dat a GDPR
- AI gramotnost (čl. 4)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Definice dotazníku ──

QUESTIONNAIRE_SECTIONS = [
    # ──────────────────────────────────────────────
    # Section 0: O vaší firmě
    # ──────────────────────────────────────────────
    {
        "id": "industry",
        "title": "O vaší firmě",
        "description": "Řeknete nám, čím se zabýváte, a my přizpůsobíme otázky.",
        "questions": [
            {
                "key": "company_industry",
                "text": "Čím se vaše firma zabývá?",
                "type": "multi_select",
                "options": [
                    "E-shop / Online obchod",
                    "Účetnictví / Finance",
                    "Zdravotnictví",
                    "Vzdělávání / Školství",
                    "Výroba / Průmysl",
                    "IT / Technologie",
                    "Stavebnictví",
                    "Doprava / Logistika",
                    "Restaurace / Gastronomie",
                    "Kadeřnictví / Kosmetika",
                    "Právní služby",
                    "Nemovitosti / Reality",
                    "Zemědělství",
                    "Jiné",
                ],
                "help_text": "Vyberte všechna odvětví, která se vás týkají.",
                "risk_hint": "none",
                "ai_act_article": None,
            },
            {
                "key": "company_size",
                "text": "Kolik má vaše firma zaměstnanců?",
                "type": "single_select",
                "options": [
                    "Jen já (OSVČ)",
                    "2–9 zaměstnanců",
                    "10–49 zaměstnanců",
                    "50–249 zaměstnanců",
                    "250+ zaměstnanců",
                ],
                "help_text": "Malé a střední podniky mají dle AI Act některé úlevy.",
                "risk_hint": "none",
                "ai_act_article": "čl. 62 — povinnosti MSP a start-upů",
            },
            {
                "key": "develops_own_ai",
                "text": "Vyvíjíte vlastní AI systémy nebo modely?",
                "type": "yes_no_unknown",
                "help_text": "Trénujete vlastní modely, vyvíjíte AI software pro zákazníky, nebo AI integrujete do svých produktů?",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "ai_role", "label": "Jaká je vaše role?", "type": "multi_select",
                         "options": ["Vyvíjíme AI (provider)", "Nasazujeme AI od jiných (deployer)", "Importujeme AI do EU (importer)", "Distribuujeme AI (distributor)"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 3 (definice rolí) + čl. 16–29 — povinnosti dle role v řetězci AI",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 1: Zakázané praktiky
    # ──────────────────────────────────────────────
    {
        "id": "prohibited_systems",
        "title": "Zakázané praktiky",
        "description": "Systémy, které AI Act výslovně zakazuje (čl. 5). Většina firem žádný nepoužívá — ověřte si to.",
        "questions": [
            {
                "key": "uses_social_scoring",
                "text": "Hodnotíte lidi komplexním skóre chování, které ovlivňuje jejich přístup ke službám?",
                "type": "yes_no_unknown",
                "help_text": "Například: zákazník má horší podmínky kvůli ‚skóre' z nesouvisející oblasti. Nepatří sem věrnostní programy. Zakázané je hodnocení na základě širokého profilu vedoucí k omezení služeb v nesouvisejícím kontextu.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "scoring_tool_name", "label": "Název systému", "type": "select",
                         "options": ["Vlastní systém", "Salesforce", "HubSpot", "Jiný CRM", "Nevím název"]},
                        {"key": "scoring_scope", "label": "Kdo je hodnocen?", "type": "multi_select",
                         "options": ["Zaměstnanci", "Zákazníci"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. c) — zákaz sociálního scoringu",
            },
            {
                "key": "uses_subliminal_manipulation",
                "text": "Používáte AI k ovlivňování lidí bez jejich vědomí?",
                "type": "yes_no_unknown",
                "help_text": "Například: AI mění ceny podle nálady zákazníka. Jde o podprahové techniky nebo cílení na zranitelné osoby (věk, zdravotní stav, finanční tíseň). Nepatří sem běžná personalizace nabídek.",
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. a) — zákaz podprahové manipulace",
            },
            {
                "key": "uses_realtime_biometric",
                "text": "Používáte biometrickou identifikaci (obličej, otisk prstu, hlas)?",
                "help_text": "Například: docházkový systém, kamera rozpoznávající konkrétní osoby nebo přístupový systém na otisk prstu.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "biometric_tool_name", "label": "Název systému", "type": "select",
                         "options": ["Kamerový systém", "Docházkový systém", "Přístupový systém", "Nevím název"]},
                        {"key": "biometric_purpose", "label": "Účel (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Docházka zaměstnanců", "Kontrola přístupu", "Identifikace zákazníků", "Bezpečnost"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. h) — ve veřejném prostoru zakázáno; jinde vysoce riziková (Příloha III)",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 2: AI nástroje ve firmě
    # ──────────────────────────────────────────────
    {
        "id": "internal_ai",
        "title": "AI nástroje ve firmě",
        "description": "Běžné AI nástroje, které zaměstnanci používají v práci.",
        "questions": [
            {
                "key": "uses_chatgpt",
                "text": "Používá někdo ve firmě ChatGPT, Claude nebo podobný AI chat?",
                "type": "yes_no_unknown",
                "help_text": "Patří sem i bezplatné verze. Pokud si nejste jistí, zeptejte se zaměstnanců.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "chatgpt_tool_name", "label": "Které nástroje používáte?", "type": "multi_select",
                         "options": ["ChatGPT", "Claude", "Gemini", "Copilot", "Perplexity", "Jiný"]},
                        {"key": "chatgpt_purpose", "label": "K čemu je používáte?", "type": "multi_select",
                         "options": ["Psaní textů", "Překlady", "Emaily", "Analýza dat", "Programování", "Zákaznický servis", "Jiné"]},
                        {"key": "chatgpt_data_type", "label": "Jaká data do něj vkládáte?", "type": "multi_select",
                         "options": ["Pouze veřejná data", "Interní dokumenty", "Osobní údaje zákazníků", "Finanční data", "Zdrojový kód / obchodní tajemství"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost transparentnosti",
            },
            {
                "key": "uses_copilot",
                "text": "Používáte AI pro psaní kódu nebo programování?",
                "type": "yes_no_unknown",
                "help_text": "GitHub Copilot, Cursor, Codeium, Amazon CodeWhisperer...",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "copilot_tool_name", "label": "Které nástroje používáte?", "type": "multi_select",
                         "options": ["GitHub Copilot", "Cursor", "Codeium", "Amazon CodeWhisperer", "Jiný"]},
                        {"key": "copilot_code_type", "label": "Typ vyvíjeného software", "type": "multi_select",
                         "options": ["Webové aplikace", "Mobilní aplikace", "Backend/API", "Data/ML", "Automatizace", "Jiné"]},
                    ]
                },
                "risk_hint": "minimal",
                "ai_act_article": None,
            },
            {
                "key": "uses_ai_content",
                "text": "Generujete obrázky, videa nebo texty pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "DALL-E, Midjourney, Stable Diffusion, Canva AI, Jasper, Copy.ai a podobné nástroje.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "content_tool_name", "label": "Které nástroje používáte?", "type": "multi_select",
                         "options": ["DALL-E", "Midjourney", "Stable Diffusion", "Canva AI", "Jasper", "Copy.ai", "Jiný"]},
                        {"key": "content_published", "label": "Kde AI obsah používáte?", "type": "multi_select",
                         "options": ["Web / sociální sítě", "Interní materiály", "E-maily zákazníkům", "Reklamní kampaně"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 4 — označení AI generovaného obsahu",
            },
            {
                "key": "uses_deepfake",
                "text": "Vytváříte syntetická videa, klonujete hlas nebo používáte AI avatary?",
                "type": "yes_no_unknown",
                "help_text": "Například: HeyGen, Synthesia, ElevenLabs nebo vlastní nástroje na generování videa/hlasu.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "deepfake_tool_name", "label": "Název nástroje", "type": "text"},
                        {"key": "deepfake_disclosed", "label": "Označujete tento obsah jako AI generovaný?", "type": "select",
                         "options": ["Ano, vždy", "Někdy", "Ne"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 4 — povinnost označit deepfake obsah",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 3: Lidské zdroje a zaměstnanci
    # ──────────────────────────────────────────────
    {
        "id": "hr",
        "title": "Lidské zdroje a zaměstnanci",
        "description": "AI v personalistice patří mezi vysoce rizikové systémy dle Přílohy III.",
        "questions": [
            {
                "key": "uses_ai_recruitment",
                "text": "Používáte AI při náboru zaměstnanců?",
                "help_text": "Například: třídění životopisů, automatické hodnocení kandidátů, AI pohovory.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "recruitment_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["LinkedIn Recruiter", "Teamio", "LMC/Jobs.cz AI", "Sloneek", "Prace.cz AI", "Vlastní systém", "Jiné"]},
                        {"key": "recruitment_tool_other", "label": "Upřesněte (volitelné)", "type": "text"},
                        {"key": "recruitment_autonomous", "label": "Rozhoduje AI samostatně o kandidátech?", "type": "select",
                         "options": ["Ano, automaticky filtruje", "Ne, pouze doporučuje", "Částečně"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 4a — nábor zaměstnanců",
            },
            {
                "key": "uses_ai_employee_monitoring",
                "text": "Sledujete zaměstnance pomocí AI?",
                "help_text": "Například: měření produktivity, GPS sledování, analýza chování, kamerový dohled s AI.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "monitoring_type", "label": "Co sledujete?", "type": "multi_select",
                         "options": ["Sledování obrazovky", "Měření produktivity", "GPS sledování", "Kamerový dohled s AI", "Analýza emailů", "Jiné"]},
                        {"key": "monitoring_informed", "label": "Jsou zaměstnanci informováni?", "type": "select",
                         "options": ["Ano, písemně", "Ano, ústně", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 4b — monitorování zaměstnanců",
            },
            {
                "key": "uses_emotion_recognition",
                "text": "Rozpoznáváte emoce zaměstnanců nebo zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "Například: analýza výrazu obličeje, tónu hlasu v call centru, sledování nálady zaměstnanců.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "emotion_tool_name", "label": "Název systému", "type": "select",
                         "options": ["Kamerový systém", "Call centrum analýza", "Vlastní systém", "Nevím název"]},
                        {"key": "emotion_context", "label": "V jakém kontextu? (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Pracovní prostředí", "Zákaznický servis", "Vzdělávání", "Bezpečnost"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. f) — omezení rozpoznávání emocí na pracovišti",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 4: Finance a rozhodování
    # ──────────────────────────────────────────────
    {
        "id": "finance",
        "title": "Finance a rozhodování",
        "description": "AI ve financích a rozhodovacích procesech s dopadem na jednotlivce.",
        "questions": [
            {
                "key": "uses_ai_accounting",
                "text": "Používáte AI v účetnictví nebo fakturaci?",
                "type": "yes_no_unknown",
                "help_text": "Například Money S5 s AI, Fakturoid, ABRA...",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "accounting_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Fakturoid", "Money S5", "ABRA", "Pohoda", "iDoklad", "Helios", "Vlastní/jiný"]},
                        {"key": "accounting_tool_other", "label": "Upřesněte (volitelné)", "type": "text"},
                        {"key": "accounting_decisions", "label": "Dělá AI autonomní finanční rozhodnutí?", "type": "select",
                         "options": ["Ne, pouze asistuje", "Ano, schvaluje platby", "Ano, hodnotí kreditní riziko"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 — transparentnost",
            },
            {
                "key": "uses_ai_creditscoring",
                "text": "Hodnotíte bonitu zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "Scoring, automatické schvalování úvěrů, hodnocení platební morálky...",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "credit_tool", "label": "Název systému", "type": "text"},
                        {"key": "credit_impact", "label": "Ovlivňuje AI rozhodnutí o úvěrech/smlouvách?", "type": "select",
                         "options": ["Ano, přímo rozhoduje", "Pouze doporučuje", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 5b — kreditní scoring",
            },
            {
                "key": "uses_ai_insurance",
                "text": "Používáte AI v pojišťovnictví?",
                "help_text": "Například: stanovení pojistného, automatická likvidace škod, hodnocení rizik.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "insurance_tool", "label": "Název systému", "type": "text"},
                        {"key": "insurance_impact", "label": "Ovlivňuje AI cenu nebo dostupnost pojištění?", "type": "select",
                         "options": ["Ano, přímo", "Pouze doporučuje", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 5a — pojišťovnictví",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 5: Zákazníci a komunikace
    # ──────────────────────────────────────────────
    {
        "id": "customer_service",
        "title": "Zákazníci a komunikace",
        "description": "AI systémy v kontaktu se zákazníky vyžadují transparentnost.",
        "questions": [
            {
                "key": "uses_ai_chatbot",
                "text": "Máte na webu chatbota nebo virtuálního asistenta?",
                "type": "yes_no_unknown",
                "help_text": "Tidio, Smartsupp, Intercom, vlastní AI chat na webu...",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "chatbot_tool_name", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Smartsupp", "Tidio", "Intercom", "Drift", "Chatbot.cz", "Vlastní řešení", "Jiné"]},
                        {"key": "chatbot_tool_other", "label": "Upřesněte (volitelné)", "type": "text"},
                        {"key": "chatbot_disclosed", "label": "Ví návštěvník, že komunikuje s AI?", "type": "select",
                         "options": ["Ano, je to označeno", "Ne", "Částečně"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost informovat o interakci s AI",
            },
            {
                "key": "uses_ai_email_auto",
                "text": "Automaticky odpovídáte na emaily zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "Například: Freshdesk AI, Zendesk AI, Intercom nebo vlastní AI auto-reply.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "email_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Freshdesk AI", "Zendesk AI", "Intercom", "Vlastní řešení", "Jiné"]},
                        {"key": "email_tool_other", "label": "Upřesněte (volitelné)", "type": "text"},
                        {"key": "email_disclosed", "label": "Ví zákazník, že odpovídá AI?", "type": "select",
                         "options": ["Ano, je to označeno", "Ne", "Někdy"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost informovat o AI",
            },
            {
                "key": "uses_ai_decision",
                "text": "Rozhoduje AI o reklamacích, slevách nebo přístupu ke službám?",
                "type": "yes_no_unknown",
                "help_text": "Například: automatické zamítnutí reklamace, AI určuje výši slevy, blokace přístupu ke službě.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "decision_scope", "label": "O čem AI rozhoduje?", "type": "text"},
                        {"key": "decision_human_review", "label": "Je k dispozici lidský přezkum?", "type": "select",
                         "options": ["Ano, lidský dohled u každého rozhodnutí", "Částečně — AI doporučuje, člověk schvaluje", "Ne, AI rozhoduje autonomně"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 14 — lidský dohled nad vysoce rizikovými systémy",
            },
            {
                "key": "uses_dynamic_pricing",
                "text": "Používáte AI k automatickému nastavování cen podle chování zákazníka?",
                "type": "yes_no_unknown",
                "help_text": "Například: ceny na e-shopu se mění podle historie nákupů, lokace nebo profilu zákazníka. Dynamické ceny dle sezóny nebo poptávky jsou běžné — problém je personalizace cílící na zranitelné skupiny.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "pricing_tool", "label": "Název nástroje", "type": "text"},
                        {"key": "pricing_basis", "label": "Na základě čeho se ceny mění?", "type": "multi_select",
                         "options": ["Historie nákupů", "Lokace zákazníka", "Čas / sezóna", "Profil zákazníka", "Poptávka", "Jiné"]},
                        {"key": "pricing_disclosed", "label": "Ví zákazník o personalizaci cen?", "type": "select",
                         "options": ["Ano", "Ne", "Částečně"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 5 odst. 1 písm. a/b) — potenciálně manipulativní, pokud cílí na zranitelné osoby",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 6: Bezpečnost a infrastruktura
    # ──────────────────────────────────────────────
    {
        "id": "infrastructure_safety",
        "title": "Bezpečnost a infrastruktura",
        "description": "AI v kritické infrastruktuře spadá do kategorie vysokého rizika.",
        "questions": [
            {
                "key": "uses_ai_critical_infra",
                "text": "Řídí AI něco kritického ve vaší firmě?",
                "help_text": "Například: řízení energetiky, vodohospodářství, dopravy, telekomunikační sítě.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "infra_tool_name", "label": "Název systému", "type": "text"},
                        {"key": "infra_sector", "label": "Sektor (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Energetika", "Doprava", "Vodohospodářství", "Telekomunikace", "Zdravotnictví", "Jiný"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 2 — kritická infrastruktura",
            },
            {
                "key": "uses_ai_safety_component",
                "text": "Je AI součástí bezpečnostní komponenty vašeho produktu?",
                "type": "yes_no_unknown",
                "help_text": "Například: AI řídí brzdy, monitoruje bezpečnost výroby nebo je součástí zdravotnického přístroje. CE označení znamená, že výrobce prohlašuje shodu s požadavky EU.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "safety_product", "label": "O jaký produkt jde?", "type": "text"},
                        {"key": "safety_ce_mark", "label": "Má produkt CE označení?", "type": "select",
                         "options": ["Ano", "Ne", "V procesu", "Nevím co je CE označení"]},
                        {"key": "safety_ce_mark_info", "label": "ℹ️ CE označení = prohlášení výrobce, že produkt splňuje požadavky EU legislativy. AI Act rozšiřuje CE požadavky na vysoce rizikové AI systémy.", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 odst. 1 — AI jako bezpečnostní komponenta",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 7: Ochrana dat
    # ──────────────────────────────────────────────
    {
        "id": "data_protection",
        "title": "Ochrana dat",
        "description": "AI Act doplňuje GDPR — obě nařízení platí současně.",
        "questions": [
            {
                "key": "ai_processes_personal_data",
                "text": "Zpracovávají vaše AI systémy osobní údaje?",
                "type": "yes_no_unknown",
                "help_text": "Jména, emaily, rodná čísla, fotografie, zdravotní údaje... U vysoce rizikových AI systémů doporučujeme DPIA (GDPR čl. 35) i FRIA — posouzení dopadů na základní práva (AI Act čl. 27).",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "personal_data_types", "label": "Jaké osobní údaje?", "type": "multi_select",
                         "options": ["Jména a kontakty", "Rodná čísla / OP", "Zdravotní údaje", "Finanční údaje", "Fotografie / video", "Lokační data", "Jiné"]},
                        {"key": "dpia_done", "label": "Provedli jste DPIA (posouzení vlivu na ochranu dat)?", "type": "select",
                         "options": ["Ano", "Ne", "Nevím co to je"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "GDPR čl. 35 (DPIA) + AI Act čl. 10/27 — správa dat a posouzení dopadů",
            },
            {
                "key": "ai_data_stored_eu",
                "text": "Jsou data vašich AI systémů uložena v EU?",
                "type": "yes_no_unknown",
                "help_text": "Pokud nevíte, pravděpodobně jsou na serverech v USA (ChatGPT, Google).",
                "risk_hint": "limited",
                "ai_act_article": "Nařízení GDPR čl. 44+ — přenos dat do třetích zemí",
            },
            {
                "key": "ai_transparency_docs",
                "text": "Máte přehled o tom, jaké AI ve firmě používáte?",
                "type": "yes_no_unknown",
                "help_text": "Nemusí být nic formálního — stačí seznam nástrojů.",
                "risk_hint": "limited",
                "ai_act_article": "čl. 49 — registrace vysoce rizikových AI systémů v EU databázi",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 8: AI gramotnost (čl. 4)
    # ──────────────────────────────────────────────
    {
        "id": "ai_literacy",
        "title": "AI gramotnost (čl. 4)",
        "description": "Od února 2025 musí firmy zajistit ‚dostatečnou úroveň AI gramotnosti' svých zaměstnanců.",
        "questions": [
            {
                "key": "has_ai_training",
                "text": "Proškolili jste zaměstnance o tom, jak bezpečně používat AI nástroje?",
                "type": "yes_no_unknown",
                "help_text": "AI Act vyžaduje, aby zaměstnanci rozuměli AI nástrojům, které používají.",
                "risk_hint": "limited",
                "ai_act_article": "čl. 4",
            },
            {
                "key": "has_ai_guidelines",
                "text": "Máte ve firmě pravidla pro používání AI?",
                "type": "yes_no_unknown",
                "help_text": "Například: co se smí do ChatGPT psát, jaká data se nesmí sdílet...",
                "risk_hint": "limited",
                "ai_act_article": "čl. 4",
            },
        ],
    },
]

# Pořadí sekcí: od jednoduchých k náročným, zakázané praktiky až ke konci
_SECTION_ORDER = [
    "industry", "internal_ai", "customer_service", "hr", "finance",
    "prohibited_systems", "infrastructure_safety", "data_protection", "ai_literacy",
]
QUESTIONNAIRE_SECTIONS.sort(key=lambda s: _SECTION_ORDER.index(s["id"]))


# ── Pydantic modely ──

class QuestionnaireAnswer(BaseModel):
    """Jedna odpověď z dotazníku."""
    question_key: str
    section: str
    answer: str = Field(..., pattern="^(yes|no|unknown|.+)$")
    details: Optional[dict] = None
    tool_name: Optional[str] = None


class QuestionnaireSubmission(BaseModel):
    """Kompletní odeslání dotazníku."""
    company_id: str
    scan_id: Optional[str] = None
    answers: list[QuestionnaireAnswer]


class QuestionnaireAnalysis(BaseModel):
    """Výsledek analýzy dotazníku."""
    company_id: str
    total_answers: int
    ai_systems_declared: int
    risk_breakdown: dict
    recommendations: list[dict]


# ── Endpointy ──

@router.get("/questionnaire/structure")
async def get_questionnaire_structure():
    """Vrátí strukturu dotazníku — sekce a otázky."""
    return {
        "sections": QUESTIONNAIRE_SECTIONS,
        "total_questions": sum(len(s["questions"]) for s in QUESTIONNAIRE_SECTIONS),
        "estimated_time_minutes": 5,  # 26 otázek × ~12s = cca 5 min
    }


@router.post("/questionnaire/submit")
async def submit_questionnaire(submission: QuestionnaireSubmission):
    """
    Uloží odpovědi z dotazníku do DB.
    Vrátí analýzu rizik + doporučení.
    """
    supabase = get_supabase()

    if not submission.answers:
        raise HTTPException(status_code=400, detail="Dotazník je prázdný.")

    # Najít nebo vytvořit anonymního clienta pro tuto firmu
    client_id = await _get_or_create_client(supabase, submission.company_id)

    # Smazat staré odpovědi pokud existují (umožňuje editaci)
    try:
        supabase.table("questionnaire_responses") \
            .delete() \
            .eq("client_id", client_id) \
            .execute()
        logger.info(f"[Questionnaire] Smazány staré odpovědi pro client {client_id}")
    except Exception as e:
        logger.warning(f"[Questionnaire] Nepodařilo se smazat staré odpovědi: {e}")

    # Uložit každou odpověď
    saved_count = 0
    for ans in submission.answers:
        try:
            row = {
                "client_id": client_id,
                "section": ans.section,
                "question_key": ans.question_key,
                "answer": ans.answer,
                "details": ans.details,
                "tool_name": ans.tool_name,
            }
            supabase.table("questionnaire_responses").insert(row).execute()
            saved_count += 1
        except Exception as e:
            logger.error(f"[Questionnaire] Chyba při ukládání odpovědi {ans.question_key}: {e}")

    logger.info(f"[Questionnaire] Uloženo {saved_count}/{len(submission.answers)} odpovědí pro company {submission.company_id}")

    # Analyzovat odpovědi
    analysis = _analyze_responses(submission.answers)

    # Pokud máme scan_id, propojit s nálezem
    if submission.scan_id:
        analysis["scan_id"] = submission.scan_id

    return {
        "status": "saved",
        "saved_count": saved_count,
        "analysis": analysis,
    }


@router.get("/questionnaire/{company_id}/results")
async def get_questionnaire_results(company_id: str):
    """Vrátí uložené odpovědi a analýzu pro firmu."""
    supabase = get_supabase()

    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        raise HTTPException(status_code=404, detail="Dotazník nebyl vyplněn.")

    result = supabase.table("questionnaire_responses") \
        .select("*") \
        .eq("client_id", client_id) \
        .order("submitted_at", desc=True) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Dotazník nebyl vyplněn.")

    # Sestavit odpovědi do QuestionnaireAnswer formátu
    answers = []
    for row in result.data:
        answers.append(QuestionnaireAnswer(
            question_key=row["question_key"],
            section=row["section"],
            answer=row["answer"],
            details=row.get("details"),
            tool_name=row.get("tool_name"),
        ))

    analysis = _analyze_responses(answers)

    return {
        "company_id": company_id,
        "answers": [a.model_dump() for a in answers],
        "analysis": analysis,
        "submitted_at": result.data[0].get("submitted_at"),
    }


@router.get("/questionnaire/{company_id}/combined-report")
async def get_combined_report(company_id: str, scan_id: Optional[str] = None):
    """
    Kombinovaný report: výsledky skenu + dotazníku.
    Úkol 16: propojení dotazníku se skenem.
    """
    supabase = get_supabase()

    # 1. Načíst odpovědi z dotazníku
    client_id = await _get_client_id_for_company(supabase, company_id)

    q_result = None
    if client_id:
        q_result = supabase.table("questionnaire_responses") \
            .select("*") \
            .eq("client_id", client_id) \
            .execute()

    questionnaire_answers = []
    for row in (q_result.data or []):
        questionnaire_answers.append(QuestionnaireAnswer(
            question_key=row["question_key"],
            section=row["section"],
            answer=row["answer"],
            details=row.get("details"),
            tool_name=row.get("tool_name"),
        ))

    # 2. Načíst findings ze skenu
    scan_findings = []
    scan_info = None
    if scan_id:
        s_result = supabase.table("scans").select("*").eq("id", scan_id).single().execute()
        scan_info = s_result.data

        f_result = supabase.table("findings") \
            .select("*") \
            .eq("scan_id", scan_id) \
            .neq("source", "ai_classified_fp") \
            .execute()
        scan_findings = f_result.data or []

    # 3. Analýza dotazníku
    q_analysis = _analyze_responses(questionnaire_answers) if questionnaire_answers else None

    # 4. Celkové rizikové skóre
    all_risks = []
    for f in scan_findings:
        all_risks.append(f.get("risk_level", "minimal"))
    if q_analysis:
        for lvl, count in q_analysis["risk_breakdown"].items():
            all_risks.extend([lvl] * count)

    risk_counts = {"high": 0, "limited": 0, "minimal": 0}
    for r in all_risks:
        if r in risk_counts:
            risk_counts[r] += 1

    # Celkový risk rating
    if risk_counts["high"] > 0:
        overall_risk = "high"
        overall_emoji = "🔴"
        overall_text = "VYSOKÉ RIZIKO — Vyžaduje okamžitou akci"
    elif risk_counts["limited"] > 0:
        overall_risk = "limited"
        overall_emoji = "🟡"
        overall_text = "OMEZENÉ RIZIKO — Transparentnost nutná"
    else:
        overall_risk = "minimal"
        overall_emoji = "🟢"
        overall_text = "MINIMÁLNÍ RIZIKO — Dobrý stav"

    return {
        "company_id": company_id,
        "scan_id": scan_id,
        "overall_risk": overall_risk,
        "overall_risk_text": f"{overall_emoji} {overall_text}",
        "risk_breakdown": risk_counts,
        "scan_summary": {
            "url": scan_info.get("url") if scan_info else None,
            "status": scan_info.get("status") if scan_info else None,
            "findings_count": len(scan_findings),
            "findings": [
                {
                    "name": f["name"],
                    "category": f["category"],
                    "risk_level": f["risk_level"],
                    "ai_act_article": f.get("ai_act_article", ""),
                    "action_required": f.get("action_required", ""),
                }
                for f in scan_findings
            ],
        },
        "questionnaire_summary": {
            "completed": bool(questionnaire_answers),
            "answers_count": len(questionnaire_answers),
            "ai_systems_declared": q_analysis["ai_systems_declared"] if q_analysis else 0,
            "recommendations": q_analysis["recommendations"] if q_analysis else [],
        },
        "total_ai_systems": len(scan_findings) + (q_analysis["ai_systems_declared"] if q_analysis else 0),
        "action_items": _generate_action_items(scan_findings, q_analysis),
    }


# ── Pomocné funkce ──

def _analyze_responses(answers: list[QuestionnaireAnswer]) -> dict:
    """Analyzuje odpovědi a vrátí rizikový profil + doporučení."""

    # Najít definice otázek
    question_map = {}
    for section in QUESTIONNAIRE_SECTIONS:
        for q in section["questions"]:
            question_map[q["key"]] = q

    yes_answers = [a for a in answers if a.answer == "yes"]
    unknown_answers = [a for a in answers if a.answer == "unknown"]
    risk_breakdown = {"high": 0, "limited": 0, "minimal": 0}
    recommendations = []

    for ans in yes_answers:
        q_def = question_map.get(ans.question_key)
        if not q_def:
            continue

        risk = q_def.get("risk_hint", "minimal")
        if risk in risk_breakdown:
            risk_breakdown[risk] += 1

        # Generovat doporučení
        tool_name = ans.tool_name or "AI systém"
        recommendations.append({
            "question_key": ans.question_key,
            "tool_name": tool_name,
            "risk_level": risk,
            "ai_act_article": q_def.get("ai_act_article", ""),
            "recommendation": _get_recommendation(ans.question_key, risk, tool_name, ans.details),
            "priority": "vysoká" if risk == "high" else "střední" if risk == "limited" else "nízká",
        })

    # Doporučení pro "Nevím" odpovědi — uživatel si není jist, může to znamenat riziko
    for ans in unknown_answers:
        q_def = question_map.get(ans.question_key)
        if not q_def:
            continue

        risk = q_def.get("risk_hint", "minimal")
        severity_info = _NEVIM_SEVERITY.get(ans.question_key, {
            "severity": "minimal", "color": "gray", "label": "Nízká priorita"
        })
        checklist = UNKNOWN_CHECKLISTS.get(ans.question_key, [])

        # "Nevím" u vysoce rizikových oblastí je samo o sobě riziko
        if risk in ("high", "limited"):
            recommendations.append({
                "question_key": ans.question_key,
                "tool_name": "",
                "risk_level": "limited",  # "Nevím" = nejisté, ale potenciální riziko
                "ai_act_article": q_def.get("ai_act_article", ""),
                "recommendation": (
                    f'U otázky "{q_def["text"]}" jste odpověděli "Nevím". '
                    f'Doporučujeme to ověřit — pokud se tato oblast týká vaší firmy, '
                    f'může jít o {"vysoce rizikový" if risk == "high" else "středně rizikový"} '
                    f'AI systém dle AI Act.'
                ),
                "priority": "střední",
                "severity": severity_info["severity"],
                "severity_color": severity_info["color"],
                "severity_label": severity_info["label"],
                "checklist": checklist,
            })

    # Seřadit doporučení: high → limited → minimal
    risk_order = {"high": 0, "limited": 1, "minimal": 2}
    recommendations.sort(key=lambda r: risk_order.get(r["risk_level"], 3))

    return {
        "total_answers": len(answers),
        "ai_systems_declared": len(yes_answers),
        "unknown_count": len(unknown_answers),
        "risk_breakdown": risk_breakdown,
        "recommendations": recommendations,
    }


# ── Checklisty pro odpovědi Nevim — konkrétní kroky co má klient udělat ──

UNKNOWN_CHECKLISTS: dict[str, list[str]] = {
    # Zakázané praktiky
    'uses_social_scoring': [
        'Zeptejte se vedení: Hodnotíme zákazníky nějakým bodovým systémem?',
        'Zkontrolujte CRM systém — má funkci skóre zákazníka?',
        'Ověřte, zda výsledky scoringu neomezují přístup ke službám.',
    ],
    'uses_subliminal_manipulation': [
        'Zeptejte se marketingu: Používáme AI k personalizaci cen podle chování?',
        'Zkontrolujte reklamní nástroje — mají funkce dynamického cílení?',
        'Ověřte, zda AI neovlivňuje zákazníky bez jejich vědomí.',
    ],
    'uses_realtime_biometric': [
        'Zeptejte se správce budovy: Máme kamery s rozpoznáváním obličejů?',
        'Zkontrolujte docházkový systém — používá otisk prstu nebo obličej?',
        'Ověřte přístupové systémy do budovy a serverovny.',
    ],
    # Interní AI
    'uses_chatgpt': [
        'Zeptejte se zaměstnanců: Používá někdo ChatGPT, Claude nebo podobný AI chat?',
        'Zkontrolujte firemní předplatné — máte ChatGPT Plus, Copilot Pro?',
        'Podívejte se na historii prohlížečů na firemních počítačích.',
    ],
    'uses_copilot': [
        'Zeptejte se vývojářů: Používáte GitHub Copilot nebo podobný AI nástroj?',
        'Zkontrolujte předplatné vývojářských nástrojů.',
    ],
    'uses_ai_content': [
        'Zeptejte se marketingu: Generujete obrázky nebo texty pomocí AI?',
        'Zkontrolujte, zda se na sociálních sítích nepoužívá Canva AI, Midjourney apod.',
    ],
    'uses_deepfake': [
        'Zeptejte se marketingu: Vytváříme videa s AI avatary nebo klonovaným hlasem?',
        'Zkontrolujte faktury — platíme za HeyGen, Synthesia, ElevenLabs?',
    ],
    # HR
    'uses_ai_recruitment': [
        'Zeptejte se HR: Používáme nějaký software na třídění životopisů?',
        'Zkontrolujte, zda Jobs.cz, LinkedIn Recruiter nebo jiný portál nefiltruje kandidáty automaticky.',
        'Zeptejte se: Rozhoduje o kandidátech člověk, nebo software?',
    ],
    'uses_ai_employee_monitoring': [
        'Zeptejte se IT: Máme nainstalovaný software na sledování produktivity?',
        'Zkontrolujte, zda firemní počítače nemají monitoring (Hubstaff, Time Doctor apod.).',
        'Ověřte, zda GPS sledování firemních aut nepoužívá AI analýzu.',
    ],
    'uses_emotion_recognition': [
        'Zeptejte se HR: Analyzujeme náladu zaměstnanců pomocí AI?',
        'Zkontrolujte call centrum — má AI analýzu tónu hlasu?',
        'Ověřte kamerové systémy — rozpoznávají výrazy obličeje?',
    ],
    # Finance
    'uses_ai_accounting': [
        'Zeptejte se účetní: Používá účetní software AI funkce?',
        'Zkontrolujte Fakturoid, Money, Pohodu — mají zapnuté AI doporučení?',
    ],
    'uses_ai_creditscoring': [
        'Zeptejte se obchodního oddělení: Hodnotíme bonitu zákazníků automaticky?',
        'Zkontrolujte, zda e-shop nebo ERP nepoužívá AI scoring platební morálky.',
    ],
    'uses_ai_insurance': [
        'Zeptejte se vedení: Používáme AI při stanovení cen pojištění?',
        'Zkontrolujte pojišťovací software — má AI funkce?',
    ],
    # Zákaznický servis
    'uses_ai_chatbot': [
        'Podívejte se na svůj web — vyskočí tam chatovací okno?',
        'Zkontrolujte faktury: Platíme za Smartsupp, Tidio, Intercom?',
        'Zeptejte se správce webu: Máme na webu AI chatbota?',
    ],
    'uses_ai_email_auto': [
        'Zeptejte se zákaznické podpory: Odpovídá na emaily automat?',
        'Zkontrolujte helpdesk systém — má zapnuté AI auto-reply?',
    ],
    'uses_ai_decision': [
        'Zeptejte se vedení: Rozhoduje někde ve firmě AI místo člověka?',
        'Zkontrolujte reklamační proces — zamítá reklamace automat?',
        'Ověřte, zda slevy nebo přístup ke službám neurčuje AI.',
    ],
    'uses_dynamic_pricing': [
        'Zeptejte se e-shop manažera: Mění se ceny automaticky podle zákazníka?',
        'Zkontrolujte cenotvorbu — používáme AI pricing nástroj?',
    ],
    # Kritická infrastruktura
    'uses_ai_critical_infra': [
        'Zeptejte se technického ředitele: Řídí AI něco kritického (energie, doprava)?',
        'Zkontrolujte SCADA / řídicí systémy — mají AI komponenty?',
    ],
    'uses_ai_safety_component': [
        'Zeptejte se produktového manažera: Je AI součástí bezpečnostní funkce produktu?',
        'Zkontrolujte CE dokumentaci — zmiňuje AI?',
    ],
    # Ochrana dat
    'ai_processes_personal_data': [
        'Zeptejte se DPO / právníka: Zpracováváme osobní údaje v AI nástrojích?',
        'Zkontrolujte, jaká data zaměstnanci vkládají do ChatGPT a podobných nástrojů.',
    ],
    'ai_data_stored_eu': [
        'Zkontrolujte smlouvy s AI poskytovateli — kde jsou data uložena?',
        'ChatGPT, Google AI = data pravděpodobně v USA.',
    ],
    'ai_transparency_docs': [
        'Spočítejte, kolik AI nástrojů firma používá (stačí jednoduchý seznam).',
        'Zeptejte se každého oddělení: Jaké AI nástroje používáte?',
    ],
    # AI gramotnost
    'has_ai_training': [
        'Zeptejte se HR: Proběhlo školení o bezpečném používání AI?',
        'Zkontrolujte, zda existuje záznam o proškolení zaměstnanců.',
    ],
    'has_ai_guidelines': [
        'Zeptejte se vedení: Máme pravidla pro používání AI ve firmě?',
        'Zkontrolujte interní dokumenty — existuje AI politika nebo směrnice?',
    ],
    # Provider
    'develops_own_ai': [
        'Zeptejte se CTO: Vyvíjíme vlastní AI modely nebo integrujeme AI do produktů?',
        'Zkontrolujte, zda produkty firmy obsahují AI funkce.',
    ],
}

# ── Mapování severity pro odpovědi Nevim ──

_NEVIM_SEVERITY: dict[str, dict] = {
    # Čl. 5 — zakázané praktiky
    'uses_social_scoring':          {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    'uses_subliminal_manipulation': {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    'uses_realtime_biometric':      {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    'uses_emotion_recognition':     {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    # Příloha III — high-risk
    'uses_ai_recruitment':          {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_employee_monitoring':  {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_creditscoring':        {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_insurance':            {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_decision':             {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_critical_infra':       {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_safety_component':     {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'develops_own_ai':              {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    # Čl. 50 — omezené riziko
    'uses_chatgpt':                 {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'uses_ai_content':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'uses_deepfake':                {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'uses_ai_chatbot':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'uses_ai_email_auto':           {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'uses_dynamic_pricing':         {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'uses_ai_accounting':           {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'ai_processes_personal_data':   {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'ai_data_stored_eu':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'ai_transparency_docs':         {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'has_ai_training':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'has_ai_guidelines':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    # Minimální
    'uses_copilot':                 {'severity': 'minimal',  'color': 'gray',   'label': 'Nízká priorita'},
}


def _get_recommendation(question_key: str, risk: str, tool_name: str, details: Optional[dict]) -> str:
    """Vrátí specifické doporučení na základě odpovědi."""
    recs = {
        # Zakázané praktiky
        "uses_social_scoring": f"ZAKÁZANÝ SYSTÉM! Sociální scoring je dle čl. 5 AI Act zakázán. Okamžitě ukončete provoz {tool_name}. Pokuta až 35 mil. EUR nebo 7 % obratu.",
        "uses_subliminal_manipulation": "ZAKÁZANÝ SYSTÉM! Podprahová manipulace je dle čl. 5 AI Act zakázána. Proveďte audit všech AI systémů ovlivňujících rozhodování uživatelů.",
        "uses_realtime_biometric": f"ZAKÁZANÝ/VYSOCE RIZIKOVÝ systém! Biometrická identifikace v reálném čase je dle čl. 5 AI Act silně omezena. Proveďte okamžitý audit {tool_name}.",
        # Interní AI
        "uses_chatgpt": f"Zavedete interní směrnici pro používání {tool_name}. Zakažte vkládání osobních údajů zákazníků. Proškolte zaměstnance o AI Act.",
        "uses_copilot": f"Zajistěte, aby AI generovaný kód prošel code review. Dokumentujte použití {tool_name} v development procesu.",
        "uses_ai_content": f"Označujte AI generovaný obsah dle čl. 50 odst. 4 AI Act. Přidejte metadata o AI původu.",
        "uses_deepfake": f"Povinnost označit syntetický obsah dle čl. 50 odst. 4. Přidejte viditelné označení ke všem AI generovaným médiím z {tool_name}.",
        # HR
        "uses_ai_recruitment": f"VYSOCE RIZIKOVÝ systém! {tool_name} spadá pod čl. 6 AI Act. Proveďte posouzení shody (conformity assessment), zajistěte lidský dohled a transparentnost vůči kandidátům.",
        "uses_ai_employee_monitoring": f"VYSOCE RIZIKOVÝ systém! Monitorování zaměstnanců AI vyžaduje souhlas, DPIA a transparentnost. Zajistěte soulad s GDPR čl. 22 a AI Act čl. 6.",
        "uses_emotion_recognition": f"ZAKÁZÁNO na pracovišti a ve vzdělávání! Rozpoznávání emocí je dle čl. 5 odst. 1 písm. f) omezeno. Proveďte audit {tool_name} a konzultujte s právníkem.",
        # Finance
        "uses_ai_accounting": f"Dokumentujte použití {tool_name} a zajistěte audit trail pro finanční rozhodnutí AI.",
        "uses_ai_creditscoring": f"VYSOCE RIZIKOVÝ systém! Kreditní scoring je regulován přílohou III AI Act. Proveďte conformity assessment a zajistěte právo na vysvětlení rozhodnutí.",
        "uses_ai_insurance": f"VYSOCE RIZIKOVÝ systém! AI v pojišťovnictví spadá pod Přílohu III bod 5a. Zajistěte posouzení shody a právo pojistníka na vysvětlení.",
        # Zákaznický servis
        "uses_ai_chatbot": f"Informujte návštěvníky, že komunikují s AI (čl. 50 odst. 1 AI Act). Přidejte jasné označení k {tool_name}.",
        "uses_ai_email_auto": f"Informujte zákazníky, že komunikují s AI (čl. 50 odst. 1). Přidejte jasné označení do automatických odpovědí.",
        "uses_ai_decision": f"AI rozhodující o právech zákazníků vyžaduje lidský dohled (čl. 14 AI Act). Zajistěte právo na přezkum člověkem.",
        "uses_dynamic_pricing": "Dynamické ceny řízené AI mohou být problematické, pokud cílí na zranitelné skupiny (čl. 5 AI Act). Zajistěte transparentnost cenotvorby a nediskriminaci zákazníků.",
        # Kritická infrastruktura
        "uses_ai_critical_infra": f"VYSOCE RIZIKOVÝ systém! AI v kritické infrastruktuře spadá pod Přílohu III bod 2. Proveďte conformity assessment a zajistěte systém řízení rizik dle čl. 9.",
        "uses_ai_safety_component": f"VYSOCE RIZIKOVÝ systém! AI jako bezpečnostní komponenta spadá pod čl. 6 odst. 1. Zajistěte CE označení a conformity assessment.",
        # Ochrana dat
        "ai_processes_personal_data": f"Proveďte DPIA dle GDPR. Zajistěte právní základ pro zpracování a minimalizaci dat v AI systémech.",
        "ai_data_stored_eu": "Ověřte, kde jsou data AI systémů fyzicky uložena. Pro přenos mimo EU zajistěte adekvátní záruky (SCC, adequacy decision).",
        "ai_transparency_docs": "Vytvořte registr všech AI systémů ve firmě. Pro vysoce rizikové systémy je registrace v EU databázi povinná (čl. 49).",
        # Provider / deployer
        "develops_own_ai": "Jako vývojář (provider) AI systémů máte povinnosti dle čl. 16 AI Act — dokumentace, posouzení shody, registrace. Identifikujte risk kategorii každého vašeho AI produktu.",
        # AI gramotnost
        "has_ai_training": "Zajistěte proškolení zaměstnanců o bezpečném používání AI nástrojů. Článek 4 AI Act vyžaduje ‚dostatečnou úroveň AI gramotnosti'.",
        "has_ai_guidelines": "Vytvořte interní pravidla pro používání AI — co se smí sdílet, jaká data nesmí do AI nástrojů, a kdo je zodpovědný za dodržování.",
    }
    return recs.get(question_key, f"Zkontrolujte soulad {tool_name} s AI Act a dokumentujte jeho použití.")


def _generate_action_items(scan_findings: list, q_analysis: Optional[dict]) -> list[dict]:
    """Generuje prioritizovaný seznam kroků ke compliance."""
    items = []

    # Z findings ze skenu
    for f in scan_findings:
        if f.get("risk_level") == "high":
            items.append({
                "priority": "🔴 VYSOKÁ",
                "action": f"Proveďte conformity assessment pro {f['name']}",
                "source": "scan",
                "risk_level": "high",
            })
        elif f.get("risk_level") == "limited":
            items.append({
                "priority": "🟡 STŘEDNÍ",
                "action": f.get("action_required", f"Zajistěte transparentnost pro {f['name']}"),
                "source": "scan",
                "risk_level": "limited",
            })

    # Z dotazníku
    if q_analysis:
        for rec in q_analysis.get("recommendations", []):
            if rec["risk_level"] == "high":
                items.append({
                    "priority": "🔴 VYSOKÁ",
                    "action": rec["recommendation"],
                    "source": "questionnaire",
                    "risk_level": "high",
                })
            elif rec["risk_level"] == "limited":
                items.append({
                    "priority": "🟡 STŘEDNÍ",
                    "action": rec["recommendation"],
                    "source": "questionnaire",
                    "risk_level": "limited",
                })

    # Obecná doporučení
    items.append({
        "priority": "📋 OBECNÉ",
        "action": "Jmenujte odpovědnou osobu za AI compliance ve firmě.",
        "source": "general",
        "risk_level": "info",
    })
    items.append({
        "priority": "📋 OBECNÉ",
        "action": "Vytvořte registr všech AI systémů používaných ve firmě.",
        "source": "general",
        "risk_level": "info",
    })

    # Seřadit: high → limited → info
    risk_order = {"high": 0, "limited": 1, "minimal": 2, "info": 3}
    items.sort(key=lambda x: risk_order.get(x["risk_level"], 4))

    return items


async def _get_or_create_client(supabase, company_id: str) -> str:
    """
    Najde nebo vytvoří anonymního clienta pro company.
    Vrátí client_id (UUID).
    Zatím nemáme auth, tak vytvoříme 'anonymous' clienta.
    """
    # Zkusit najít existujícího clienta pro tuto firmu
    result = supabase.table("clients") \
        .select("id") \
        .eq("company_id", company_id) \
        .limit(1) \
        .execute()

    if result.data:
        return result.data[0]["id"]

    # Ujistit se, že firma existuje v tabulce companies
    comp_check = supabase.table("companies") \
        .select("id") \
        .eq("id", company_id) \
        .limit(1) \
        .execute()

    if not comp_check.data:
        # Firma neexistuje → vytvořit ji
        supabase.table("companies").insert({
            "id": company_id,
            "name": f"Firma (dotazník)",
            "ico": "",
        }).execute()
        logger.info(f"[Questionnaire] Vytvořena firma {company_id} z dotazníku")

    # Vytvořit nového anonymního clienta
    new_client = supabase.table("clients").insert({
        "company_id": company_id,
        "contact_name": "Anonymní uživatel",
        "email": f"anonymous-{company_id[:8]}@aishield.cz",
        "contact_role": "questionnaire",
    }).execute()

    client_id = new_client.data[0]["id"]
    logger.info(f"[Questionnaire] Vytvořen anonymní client {client_id} pro company {company_id}")
    return client_id


async def _get_client_id_for_company(supabase, company_id: str) -> str | None:
    """Najde client_id pro company_id."""
    result = supabase.table("clients") \
        .select("id") \
        .eq("company_id", company_id) \
        .limit(1) \
        .execute()
    return result.data[0]["id"] if result.data else None
