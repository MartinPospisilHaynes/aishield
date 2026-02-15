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

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.database import get_supabase
from backend.api.auth import AuthUser, get_optional_user

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
                "help_text": "Vyberte všechna odvětví, která se vás týkají. Příklady: e-shop prodávající oblečení, účetní kancelář zpracovávající daňová přiznání, autoservis s online objednávkami.",
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
                "help_text": "Malé a střední podniky (do 250 zaměstnanců) mají dle AI Act některé úlevy. Příklady: OSVČ grafik, restaurace s 5 zaměstnanci, výrobní firma se 120 lidmi.",
                "risk_hint": "none",
                "ai_act_article": "čl. 62 — povinnosti MSP a start-upů",
            },
            {
                "key": "develops_own_ai",
                "text": "Vyvíjíte vlastní AI systémy nebo modely?",
                "type": "yes_no_unknown",
                "help_text": "Příklady: IT firma trénuje vlastní ML model pro predikci poptávky. Startup vyvíjí AI chatbota pro klienty. E-shop integruje AI doporučovací engine do svého webu.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "ai_role", "label": "Jaká je vaše role?", "type": "multi_select",
                         "options": ["Vyvíjíme AI (provider)", "Nasazujeme AI od jiných (deployer)", "Importujeme AI do EU (importer)", "Distribuujeme AI (distributor)", "Jiné"]},
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
                "help_text": "Příklady:\n1) Banka odmítne úvěr kvůli špatnému skóre z jiné oblasti (pozdní platby za telefon).\n2) E-shop nabízí horší ceny zákazníkům s nízkým ‚interním skóre'.\n3) Pojišťovna zvýší pojistné na základě sociálního profilu klienta. Nepatří sem běžné věrnostní programy.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "scoring_tool_name", "label": "Které systémy používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Salesforce", "HubSpot", "Jiný CRM", "Jiný"]},
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
                "help_text": "Příklady:\n1) E-shop zvyšuje ceny, když AI detekuje frustraci zákazníka.\n2) Reklama cílí AI algoritmy na seniory v tísni s nabídkou předražených produktů.\n3) Aplikace používá skryté manipulativní designové vzory řízené AI. Nepatří sem běžná personalizace nabídek.",
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. a) — zákaz podprahové manipulace",
            },
            {
                "key": "uses_realtime_biometric",
                "text": "Používáte biometrickou identifikaci (obličej, otisk prstu, hlas)?",
                "help_text": "Příklady:\n1) Docházkový systém na otisk prstu (HR oddělení).\n2) Kamerový systém na recepci identifikující zaměstnance obličejem (bezpečnostní oddělení).\n3) Vstupní brána na rozpoznání hlasu (IT oddělení).",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "biometric_tool_name", "label": "Které systémy používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Kamerový systém", "Docházkový systém", "Přístupový systém", "Jiný"]},
                        {"key": "biometric_purpose", "label": "Účel (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Docházka zaměstnanců", "Kontrola přístupu", "Identifikace zákazníků", "Bezpečnost", "Jiné"]},
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
                "help_text": "Příklady:\n1) Marketingové oddělení píše newslettery v ChatGPT.\n2) Účetní se ptá Claude na daňové předpisy.\n3) Obchodník připravuje nabídky pomocí Copilota. Patří sem i bezplatné verze.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "chatgpt_tool_name", "label": "Které nástroje používáte?", "type": "multi_select",
                         "options": ["ChatGPT", "Claude", "Gemini", "Copilot", "Perplexity", "Jiný"]},
                        {"key": "chatgpt_purpose", "label": "K čemu je používáte?", "type": "multi_select",
                         "options": ["Psaní textů", "Překlady", "Emaily", "Analýza dat", "Programování", "Zákaznický servis", "Jiné"]},
                        {"key": "chatgpt_data_type", "label": "Jaká data do něj vkládáte?", "type": "multi_select",
                         "options": ["Pouze veřejná data", "Interní dokumenty", "Osobní údaje zákazníků", "Finanční data", "Zdrojový kód / obchodní tajemství", "Jiné"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost transparentnosti",
            },
            {
                "key": "uses_copilot",
                "text": "Používáte AI pro psaní kódu nebo programování?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Vývojář používá GitHub Copilot k doplňování kódu (IT oddělení).\n2) Data analyst vytváří SQL dotazy v Cursoru.\n3) DevOps inženýr generuje skripty pomocí Amazon CodeWhisperer.",
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
                "help_text": "Příklady:\n1) Marketing generuje obrázky produktů v Midjourney pro sociální sítě.\n2) Grafik vytváří bannery v Canva AI (kreativní oddělení).\n3) Copywriter píše popisky produktů v Jasper / Copy.ai.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "content_tool_name", "label": "Které nástroje používáte?", "type": "multi_select",
                         "options": ["DALL-E", "Midjourney", "Stable Diffusion", "Canva AI", "Jasper", "Copy.ai", "Jiný"]},
                        {"key": "content_published", "label": "Kde AI obsah používáte?", "type": "multi_select",
                         "options": ["Web / sociální sítě", "Interní materiály", "E-maily zákazníkům", "Reklamní kampaně", "Jiné"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 4 — označení AI generovaného obsahu",
            },
            {
                "key": "uses_deepfake",
                "text": "Vytváříte syntetická videa, klonujete hlas nebo používáte AI avatary?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Marketing vytváří promo videa s AI avatarem v Synthesia.\n2) E-learningové oddělení klonuje hlas lektora pomocí ElevenLabs.\n3) HR natáčí onboarding videa s virtuálním mluvčím v HeyGen.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "deepfake_tool_name", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["HeyGen", "Synthesia", "ElevenLabs", "D-ID", "Murf AI", "Jiný"]},
                        {"key": "deepfake_disclosed", "label": "Označujete tento obsah jako AI generovaný?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Od 2. srpna 2025 je podle čl. 50 AI Act povinné označit veškerý deep-fake obsah (syntetická videa, klonovaný hlas, AI avatary) jako uměle vytvořený. Nesplnění může vést k pokutě."}},
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
                "help_text": "Příklady:\n1) HR používá LinkedIn Recruiter k automatickému třídění životopisů.\n2) Teamio filtruje kandidáty podle klíčových slov v CV.\n3) Jobs.cz AI automaticky řadí uchazeče podle shody s popisem pozice.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "recruitment_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["LinkedIn Recruiter", "Teamio", "LMC/Jobs.cz AI", "Sloneek", "Prace.cz AI", "Jiné"]},
                        {"key": "recruitment_autonomous", "label": "Rozhoduje AI samostatně o kandidátech?", "type": "select",
                         "options": ["Ano, automaticky filtruje", "Ne, pouze doporučuje"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 4a — nábor zaměstnanců",
            },
            {
                "key": "uses_ai_employee_monitoring",
                "text": "Sledujete zaměstnance pomocí AI?",
                "help_text": "Příklady:\n1) IT oddělení má Hubstaff / Time Doctor na sledování aktivity obrazovky.\n2) Logistika používá GPS tracking kurjérů.\n3) Výroba má kamery s AI detekcí bezpečnostních pravidel.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "monitoring_type", "label": "Co sledujete?", "type": "multi_select",
                         "options": ["Sledování obrazovky", "Měření produktivity", "GPS sledování", "Kamerový dohled s AI", "Analýza emailů", "Jiné"]},
                        {"key": "monitoring_informed", "label": "Jsou zaměstnanci informováni?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Zaměstnanci mají právo být informováni o sledování. Neinformování může porušit GDPR i AI Act (čl. 26 odst. 7)."}},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 4b — monitorování zaměstnanců",
            },
            {
                "key": "uses_emotion_recognition",
                "text": "Rozpoznáváte emoce zaměstnanců nebo zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Call centrum analyzuje tón hlasu operátorů pro hodnocení kvality (zákaznický servis).\n2) Kamera v kanceláři sleduje výraz obličeje pro ‚měření spokojenosti‘ (HR).\n3) Školicí systém detekuje nudu studentů pomocí webkamery (vzdělávání).",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "emotion_tool_name", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Kamerový systém", "Call centrum analýza", "Jiný"]},
                        {"key": "emotion_context", "label": "V jakém kontextu? (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Pracovní prostředí", "Zákaznický servis", "Vzdělávání", "Bezpečnost", "Jiné"]},
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
                "help_text": "Příklady:\n1) Účetní kancelář používá Pohodu s AI kategorizací faktur.\n2) Fakturoid automaticky páruje přijaté platby.\n3) Money S5 navrhuje účetní políčky pomocí AI.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "accounting_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Fakturoid", "Money S5", "ABRA", "Pohoda", "iDoklad", "Helios", "Jiné"]},
                        {"key": "accounting_decisions", "label": "Dělá AI autonomní finanční rozhodnutí?", "type": "select",
                         "options": ["Ne, pouze asistuje", "Ano, schvaluje platby"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 — transparentnost",
            },
            {
                "key": "uses_ai_creditscoring",
                "text": "Hodnotíte bonitu zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Finanční oddělení používá CRIF scoring k hodnocení bonity klientů.\n2) E-shop automaticky schvaluje / zamítá nákup na splátky podle AI skóre.\n3) Leasingová společnost používá Bisnode k ověření platební morálky.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "credit_tool", "label": "Které systémy používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["CRIF – Czech Credit Bureau", "Bisnode / Dun & Bradstreet", "Scoring Solutions", "Jiný"]},
                        {"key": "credit_impact", "label": "Ovlivňuje AI rozhodnutí o úvěrech/smlouvách?", "type": "select",
                         "options": ["Ano, přímo rozhoduje", "Ne"],
                         "warning": {"Ano, přímo rozhoduje": "Automatické rozhodování o úvěrech bez lidského dohledu spadá do kategorie vysoce rizikových AI systémů (Příloha III, bod 5b). Vyžaduje registraci v EU databázi a průběžné monitorování."}},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 5b — kreditní scoring",
            },
            {
                "key": "uses_ai_insurance",
                "text": "Používáte AI v pojišťovnictví?",
                "help_text": "Příklady:\n1) Pojišťovna stanovuje výši pojistného pomocí AI modelu (aktuárské oddělení).\n2) Likvidace škod probíhá automaticky — AI posoudí fotky nehody.\n3) AI hodnocení rizika klienta při sjednávání životního pojištění.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "insurance_tool", "label": "Které systémy používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Guidewire", "NESS / Allianz AI", "ČPP / ČSOB interní AI", "Jiný"]},
                        {"key": "insurance_impact", "label": "Ovlivňuje AI cenu nebo dostupnost pojištění?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ano": "AI systém, který ovlivňuje cenu nebo dostupnost pojištění, je vysoce rizikový dle Přílohy III, bod 5a. Musíte zajistit posouzení shody, registraci v EU databázi, průběžné monitorování a právo pojistníka na vysvětlení rozhodnutí."}},
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
                "help_text": "Příklady:\n1) E-shop má Smartsupp chatbota, který odpovídá na dotazy o dostupnosti zboží.\n2) SaaS firma používá Intercom k automatickému řešení podpory.\n3) Restaurace má na webu Tidio bota pro rezervace.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "chatbot_tool_name", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Smartsupp", "Tidio", "Intercom", "Drift", "Chatbot.cz", "Jiné"]},
                        {"key": "chatbot_disclosed", "label": "Ví návštěvník, že komunikuje s AI?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Podle čl. 50 AI Act musí být zákazníci informováni, že komunikují s AI systémem. Tato povinnost platí od 2. srpna 2025."}},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost informovat o interakci s AI",
            },
            {
                "key": "uses_ai_email_auto",
                "text": "Automaticky odpovídáte na emaily zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Zákaznický servis e-shopu automaticky odpovídá na dotazy o doručení přes Freshdesk AI.\n2) IT podpora používá Zendesk AI k třídění a odpovídání na tickety.\n3) Obchodní oddělení má nastavené auto-reply v Intercomu.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "email_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Freshdesk AI", "Zendesk AI", "Intercom", "Jiné"]},
                        {"key": "email_disclosed", "label": "Ví zákazník, že odpovídá AI?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Podle čl. 50 AI Act musí být zákazníci informováni, že komunikují s AI systémem. Tato povinnost platí od 2. srpna 2025."}},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost informovat o AI",
            },
            {
                "key": "uses_ai_decision",
                "text": "Rozhoduje AI o reklamacích, slevách nebo přístupu ke službám?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) E-shop automaticky zamítá reklamace mimo lhůtu pomocí AI pravidel (zákaznický servis).\n2) AI určuje výši slevy podle historie nákupů zákazníka (obchodní oddělení).\n3) Poskytovatel služeb blokuje přístup k účtu na základě AI hodnocení rizika.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "decision_scope", "label": "O čem AI rozhoduje?", "type": "multi_select",
                         "options": ["Reklamace", "Slevy / ceny", "Přístup ke službám", "Schvalování žádostí", "Jiné"]},
                        {"key": "decision_human_review", "label": "Je k dispozici lidský přezkum?", "type": "select",
                         "options": ["Ano", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 14 — lidský dohled nad vysoce rizikovými systémy",
            },
            {
                "key": "uses_dynamic_pricing",
                "text": "Používáte AI k automatickému nastavování cen podle chování zákazníka?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) E-shop zvyšuje ceny víkendům podle AI predikce poptávky.\n2) Letěnky zdražují, když AI detekuje vyšší zájem z určité lokace.\n3) AI nabízí různé ceny vracíce se vs. novemu zákazníkovi. Dynamické ceny dle sezóny jsou běžné — problém je cílená personalizace.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "pricing_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Prisync", "Competera", "Dynamic Yield", "Jiný"]},
                        {"key": "pricing_basis", "label": "Na základě čeho se ceny mění?", "type": "multi_select",
                         "options": ["Historie nákupů", "Lokace zákazníka", "Čas / sezóna", "Profil zákazníka", "Poptávka", "Jiné"]},
                        {"key": "pricing_disclosed", "label": "Ví zákazník o personalizaci cen?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Personalizace cen bez informování zákazníka může představovat nekalou obchodní praktiku a porušení transparentnosti dle AI Act."}},
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
                "help_text": "Příklady:\n1) Energetická firma řídí AI distribuční síť elektřiny (provozní oddělení).\n2) Vodní dílo používá AI k optimalizaci čištění vody.\n3) Dopravní firma má AI předikci údržby vozového parku.",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "infra_tool_name", "label": "Které systémy používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Siemens MindSphere", "ABB Ability", "Honeywell Forge", "Jiný"]},
                        {"key": "infra_sector", "label": "Sektor (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Energetika", "Doprava", "Vodohospodářství", "Telekomunikace", "Zdravotnictví", "Jiné"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 2 — kritická infrastruktura",
            },
            {
                "key": "uses_ai_safety_component",
                "text": "Je AI součástí bezpečnostní komponenty vašeho produktu?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) AI řídí brzdný systém v automobilu (výrobní oddělení).\n2) AI monitoruje bezpečnost výrobní linky a vypíná stroj při detekci nebezpečí.\n3) AI je součástí zdravotnického přístroje (diagnostika). CE označení = prohlášení výrobce o shodě s EU legislativou.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "safety_product", "label": "O jaký produkt jde? (vyberte vše)", "type": "multi_select",
                         "options": ["Zdravotnický přístroj", "Průmyslový stroj", "Automobil / dopravní prostředek", "Bezpečnostní systém", "Jiný"]},
                        {"key": "safety_ce_mark", "label": "Má produkt CE označení?", "type": "select",
                         "options": ["Ano", "Ne"]},
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
                "help_text": "Příklady:\n1) Do ChatGPT vkládáte jména a emaily zákazníků (obchodní oddělení).\n2) HR nahrává životopisy kandidátů do AI nástroje.\n3) Účetní zpracovává rodná čísla v AI systému. U vysoce rizikových AI systémů se doporučuje DPIA (posouzení vlivu na ochranu dat).",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "personal_data_types", "label": "Jaké osobní údaje?", "type": "multi_select",
                         "options": ["Jména a kontakty", "Rodná čísla / OP", "Zdravotní údaje", "Finanční údaje", "Fotografie / video", "Lokační data", "Jiné"]},
                        {"key": "dpia_done", "label": "Provedli jste DPIA (posouzení vlivu na ochranu dat)?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "U AI systémů zpracovávajících osobní údaje se důrazně doporučuje provedení DPIA (posouzení vlivu na ochranu dat) dle GDPR čl. 35."}},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "GDPR čl. 35 (DPIA) + AI Act čl. 10/27 — správa dat a posouzení dopadů",
            },
            {
                "key": "ai_data_stored_eu",
                "text": "Jsou data vašich AI systémů uložena v EU?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) ChatGPT ukládá data na serverech v USA (OpenAI).\n2) Google Gemini — servery v USA i EU.\n3) Vlastní AI hostovaná na českém VPS (CZ.NIC).\nPokud nevíte, pravděpodobně jsou data mimo EU.",
                "followup": {
                    "condition": "unknown",
                    "fields": [
                        {"key": "data_location_hint", "label": "Pomůžeme vám to zjistit — které AI nástroje používáte?", "type": "multi_select",
                         "options": ["ChatGPT (OpenAI — USA)", "Google Gemini (USA/EU)", "Microsoft Copilot (EU i USA)", "Claude (Anthropic — USA)", "Vlastní server v ČR/EU", "Jiný"]},
                        {"key": "data_location_info", "label": "ℹ️ Většina velkých AI poskytovatelů (OpenAI, Google, Anthropic) ukládá data primárně v USA. Pro GDPR soulad zvažte EU hosting nebo smluvní záruky (SCC).", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "Nařízení GDPR čl. 44+ — přenos dat do třetích zemí",
            },
            {
                "key": "ai_transparency_docs",
                "text": "Máte přehled o tom, jaké AI ve firmě používáte?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Interní tabulka se seznamem AI nástrojů a jejich účelem (IT oddělení).\n2) Přehled SaaS služeb včetně AI v portálu dodavatelů.\n3) Jednoduchý dokument ‚Které AI používáme‘ pro management.",
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
                "help_text": "Příklady:\n1) Firemní workshop ‚Bezpečné používání ChatGPT‘ pro všechny zaměstnance.\n2) Online kurz AI gramotnosti od Seduo / Coursera.\n3) Interní prezentace o rizicích AI a pravidlech GDPR.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "training_attendance", "label": "Máte prezenční listinu (podpisy účastníků školení)?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Pro doložení splnění povinnosti čl. 4 AI Act je vhodné mít prezenční listinu s podpisy účastníků. AIshield.cz vám v rámci služeb dodá kompletní školící prezentaci + šablonu prezenční listiny."}},
                        {"key": "training_info", "label": "ℹ️ Součástí všech AIshield balíčků je profesionální školící prezentace (PowerPoint) a kompletní dokumentace včetně šablony prezenční listiny.", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 4",
            },
            {
                "key": "has_ai_guidelines",
                "text": "Máte ve firmě pravidla pro používání AI?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Interní směrnice ‚Co se smí a nesmí do ChatGPT‘ (IT oddělení).\n2) Etický kodex pro používání AI v marketingu.\n3) Pravidla pro sdílení firemních dat s AI nástroji.",
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


@router.get("/questionnaire/my-status")
async def get_my_questionnaire_status(user: AuthUser = Depends(get_optional_user)):
    """
    Zjistí stav dotazníku přihlášeného uživatele.
    Vrátí is_complete, has_unknowns, total_answers.
    """
    if not user:
        return {"is_complete": False, "has_unknowns": False, "total_answers": 0}

    supabase = get_supabase()

    # Najít company_id přes scan_results (nejčastější cesta)
    company_id = None
    try:
        scans = supabase.table("scan_results") \
            .select("company_id") \
            .eq("user_email", user.email) \
            .limit(1) \
            .execute()
        if scans.data:
            company_id = scans.data[0]["company_id"]
    except Exception:
        pass

    if not company_id:
        # Zkusit najít přes clients tabulku
        try:
            clients = supabase.table("clients") \
                .select("id") \
                .eq("email", user.email) \
                .limit(1) \
                .execute()
            if clients.data:
                company_id = clients.data[0]["id"]
        except Exception:
            pass

    if not company_id:
        return {"is_complete": False, "has_unknowns": False, "total_answers": 0}

    # Najít odpovědi
    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        return {"is_complete": False, "has_unknowns": False, "total_answers": 0}

    result = supabase.table("questionnaire_responses") \
        .select("question_key, answer") \
        .eq("client_id", client_id) \
        .execute()

    if not result.data:
        return {"is_complete": False, "has_unknowns": False, "total_answers": 0}

    total = len(result.data)
    unknowns = sum(1 for r in result.data if r.get("answer") == "nevim")
    # 27 questions total in the questionnaire
    is_complete = total >= 27 and unknowns == 0

    return {
        "is_complete": is_complete,
        "has_unknowns": unknowns > 0,
        "total_answers": total,
        "unknown_count": unknowns,
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
        'Koho se zeptat: vedení firmy, obchodní oddělení, CRM administrátor.',
        'Příklad: Zákazníci dostávají bodové hodnocení v CRM (např. "VIP skóre") a na základě toho mají rozdílné podmínky, ceny nebo přístup ke službám.',
        'Zkontrolujte CRM systém (Salesforce, HubSpot, vlastní) — má funkci zákaznického skóre nebo segmentace?',
        'Ověřte, zda výsledky jakéhokoliv hodnocení neomezují zákazníkům přístup ke službám v nesouvisející oblasti.',
    ],
    'uses_subliminal_manipulation': [
        'Koho se zeptat: marketingové oddělení, e-shop manažer, správce reklam.',
        'Příklad: AI mění obsah webu, ceny nebo nabídky podle detekované nálady, stresu nebo zranitelnosti návštěvníka — například vyšší cena pro spěchajícího zákazníka.',
        'Zkontrolujte marketingové nástroje — používají AI k dynamickému přizpůsobování obsahu?',
        'Ověřte, zda AI automaticky nemění nabídky pro skupiny lidí na základě věku, zdravotního stavu nebo finanční situace.',
    ],
    'uses_realtime_biometric': [
        'Koho se zeptat: správce budovy, IT oddělení, bezpečnostní služba.',
        'Příklad: Docházkový systém na otisk prstu, kamerový systém s rozpoznáváním obličejů na vstupu do budovy, hlasová identifikace v call centru.',
        'Zkontrolujte docházkový systém — používá otisk prstu, sken obličeje nebo duhovky?',
        'Ověřte přístupové systémy do budovy, serverovny a zabezpečených prostor.',
        'Zkontrolujte kamerový systém — rozpoznává konkrétní osoby automaticky?',
    ],
    # Interní AI
    'uses_chatgpt': [
        'Koho se zeptat: všechna oddělení — marketing, obchod, zákaznická podpora, vedení.',
        'Příklad: Zaměstnanec používá ChatGPT k psaní emailů, shrnutí dokumentů, přípravě prezentací nebo generování textů na sociální sítě.',
        'Zkontrolujte firemní předplatné — máte ChatGPT Plus, Claude Pro, Gemini Advanced?',
        'Zeptejte se zaměstnanců přímo — i bezplatné verze se počítají.',
        'Podívejte se na historii prohlížečů a nainstalované aplikace na firemních počítačích.',
    ],
    'uses_copilot': [
        'Koho se zeptat: IT oddělení, vývojáři, správce infrastruktury.',
        'Příklad: Programátor používá GitHub Copilot, Cursor nebo Amazon CodeWhisperer k psaní kódu.',
        'Zkontrolujte předplatné vývojářských nástrojů a IDE pluginy.',
    ],
    'uses_ai_content': [
        'Koho se zeptat: marketing, grafické oddělení, social media manažer, copywriter.',
        'Příklad: Marketingové oddělení generuje obrázky v Midjourney, texty přes Jasper AI, prezentace v Canva AI.',
        'Zkontrolujte, zda se na sociálních sítích nepoužívají AI-generované obrázky nebo texty.',
        'Ověřte, zda webdesignér nebo grafik nepoužívá AI nástroje pro tvorbu vizuálů.',
    ],
    'uses_deepfake': [
        'Koho se zeptat: marketing, PR oddělení, video produkce.',
        'Příklad: Firma vytváří marketingová videa s AI avatary (Synthesia, HeyGen), klonuje hlas pro podcasty (ElevenLabs) nebo generuje syntetické fotografie pro prezentace.',
        'Zkontrolujte faktury — platíme za HeyGen, Synthesia, ElevenLabs, D-ID?',
    ],
    # HR
    'uses_ai_recruitment': [
        'Koho se zeptat: HR oddělení, personální agentura, vedoucí náboru.',
        'Příklad: Software automaticky třídí životopisy podle klíčových slov, AI hodnotí video pohovory, LinkedIn Recruiter filtruje kandidáty pomocí AI.',
        'Zkontrolujte inzerční portály (Jobs.cz, LinkedIn) — mají zapnuté AI filtrování?',
        'Zeptejte se: Rozhoduje o pozvání kandidáta na pohovor člověk, nebo software?',
    ],
    'uses_ai_employee_monitoring': [
        'Koho se zeptat: IT oddělení, HR, vedení firmy.',
        'Příklad: Software sleduje aktivitu zaměstnanců na počítači (Hubstaff, Time Doctor), GPS sledování firemních vozidel s AI analýzou tras, kamerový systém měřící přítomnost na pracovišti.',
        'Zkontrolujte, zda firemní počítače nemají monitoring klávesnice nebo snímky obrazovky.',
        'Ověřte flotilový management — používá AI k analýze jízd?',
    ],
    'uses_emotion_recognition': [
        'Koho se zeptat: HR oddělení, vedoucí call centra, IT oddělení.',
        'Příklad: Call centrum analyzuje tón hlasu zákazníků i operátorů pro hodnocení spokojenosti, kamerový systém detekuje únavu zaměstnanců, software měří "náladu týmu".',
        'Zkontrolujte call centrum — má AI analýzu sentimentu nebo tónu hlasu?',
        'Ověřte kamerové systémy — rozpoznávají výrazy obličeje nebo emoce?',
    ],
    # Finance
    'uses_ai_accounting': [
        'Koho se zeptat: účetní, finanční oddělení, správce ERP systému.',
        'Příklad: Účetní software (Money S5, Pohoda, ABRA) automaticky kategorizuje faktury pomocí AI, Fakturoid navrhuje účetní zápisy, AI předpovídá cash flow.',
        'Zkontrolujte účetní software — má zapnuté AI doporučení nebo automatické párování?',
    ],
    'uses_ai_creditscoring': [
        'Koho se zeptat: obchodní oddělení, finanční oddělení, e-shop manažer.',
        'Příklad: E-shop automaticky schvaluje nebo zamítá platbu na fakturu podle "skóre" zákazníka, ERP hodnotí platební morálku a doporučuje platební podmínky.',
        'Zkontrolujte, zda e-shop nebo ERP nepoužívá automatický scoring platební morálky zákazníků.',
    ],
    'uses_ai_insurance': [
        'Koho se zeptat: vedení, pojistný matematik, IT oddělení.',
        'Příklad: Software automaticky stanovuje výši pojistného na základě AI analýzy rizik, AI likviduje menší škody bez lidského dohledu.',
        'Zkontrolujte pojišťovací software — má AI funkce pro oceňování rizik nebo likvidaci?',
    ],
    # Zákaznický servis
    'uses_ai_chatbot': [
        'Koho se zeptat: správce webu, webdesignér, marketing, zákaznická podpora.',
        'Příklad: Na webu vyskočí chatovací okno (Smartsupp, Tidio, Intercom), které odpovídá na dotazy návštěvníků automaticky pomocí AI.',
        'Podívejte se na svůj web — vyskočí tam chatovací okno? Zkuste mu položit otázku.',
        'Zkontrolujte faktury: Platíme za Smartsupp, Tidio, Intercom, Drift nebo jiný chatbot?',
    ],
    'uses_ai_email_auto': [
        'Koho se zeptat: zákaznická podpora, marketing, IT oddělení.',
        'Příklad: Helpdesk systém (Freshdesk, Zendesk) automaticky generuje odpovědi na zákaznické emaily pomocí AI, auto-reply navrhuje řešení tiketu.',
        'Zkontrolujte helpdesk nebo ticket systém — má zapnuté AI auto-reply nebo návrhy odpovědí?',
    ],
    'uses_ai_decision': [
        'Koho se zeptat: vedení, obchodní oddělení, zákaznická podpora, právní oddělení.',
        'Příklad: AI automaticky zamítá reklamace podle pravidel bez lidské kontroly, software rozhoduje o výši slevy podle profilu zákazníka, systém blokuje přístup ke službě na základě AI hodnocení.',
        'Zkontrolujte reklamační proces — rozhoduje o výsledku člověk, nebo software?',
        'Ověřte, zda slevy, bonusy nebo přístup ke službám neurčuje AI bez lidského dohledu.',
    ],
    'uses_dynamic_pricing': [
        'Koho se zeptat: e-shop manažer, obchodní oddělení, marketing.',
        'Příklad: Ceny na e-shopu se automaticky mění podle chování zákazníka — opakovaná návštěva = vyšší cena, mobilní telefon = jiná cena než desktop. AI pricing nástroj (Prisync, Competera).',
        'Zkontrolujte cenotvorbu — jsou ceny pro všechny zákazníky stejné, nebo se mění dynamicky?',
    ],
    # Kritická infrastruktura
    'uses_ai_critical_infra': [
        'Koho se zeptat: technický ředitel (CTO), vedoucí výroby, správce infrastruktury.',
        'Příklad: AI řídí distribuci energie v budově, optimalizuje logistiku a dopravu, monitoruje telekomunikační síť, řídí vodohospodářský systém.',
        'Zkontrolujte SCADA / řídicí systémy — mají AI komponenty nebo prediktivní údržbu?',
        'Ověřte s dodavateli technologií, zda jejich řešení obsahují AI prvky.',
    ],
    'uses_ai_safety_component': [
        'Koho se zeptat: produktový manažer, technický ředitel, oddělení kvality.',
        'Příklad: AI řídí brzdy ve vozidle, monitoruje bezpečnost výrobní linky, je součástí zdravotnického přístroje nebo bezpečnostního systému budovy.',
        'Zkontrolujte CE dokumentaci vašich produktů — zmiňuje AI nebo strojové učení?',
        'Ověřte s vývojovým týmem, zda je AI součástí bezpečnostní funkce produktu.',
    ],
    # Ochrana dat
    'ai_processes_personal_data': [
        'Koho se zeptat: DPO (pověřenec pro ochranu osobních údajů), právní oddělení, IT oddělení.',
        'Příklad: Zaměstnanci kopírují emaily zákazníků do ChatGPT, AI analyzuje životopisy kandidátů, chatbot pracuje s osobními údaji návštěvníků webu.',
        'Zkontrolujte, jaká data zaměstnanci vkládají do AI nástrojů (jména, emaily, rodná čísla, zdravotní údaje).',
        'Ověřte s DPO, zda máte zpracování osobních údajů v AI nástrojích pokryté ve GDPR dokumentaci.',
    ],
    'ai_data_stored_eu': [
        'Koho se zeptat: IT oddělení, DPO, správce infrastruktury.',
        'Příklad: ChatGPT ukládá data v USA, Google AI v USA, většina AI služeb nemá servery v EU.',
        'Zkontrolujte smlouvy s AI poskytovateli — kde jsou data uložena? Mají Data Processing Agreement?',
        'Ověřte, zda používáte EU verze služeb (např. Azure EU, AWS Frankfurt).',
    ],
    'ai_transparency_docs': [
        'Koho se zeptat: všechna oddělení — každé oddělení zvlášť.',
        'Příklad: Firma nemá přehled o tom, kolik AI nástrojů zaměstnanci používají. Stačí jednoduchý Excel seznam: název nástroje, kdo ho používá, k čemu.',
        'Požádejte každého vedoucího oddělení o seznam AI nástrojů, které jeho tým používá.',
        'Spočítejte, kolik AI nástrojů firma celkem používá — stačí neformální přehled.',
    ],
    # AI gramotnost
    'has_ai_training': [
        'Koho se zeptat: HR oddělení, vedení firmy, školící manažer.',
        'Příklad: Zaměstnanci nebyli proškoleni o tom, co smí a nesmí do AI nástrojů vkládat, jak rozpoznat chybný výstup AI, jaká jsou jejich práva a povinnosti.',
        'Zkontrolujte, zda proběhlo jakékoliv školení o AI — i neformální informační schůzka se počítá.',
        'Ověřte, zda existuje záznam (prezenční listina, email) o proškolení.',
    ],
    'has_ai_guidelines': [
        'Koho se zeptat: vedení firmy, právní oddělení, HR.',
        'Příklad: Firma nemá žádná pravidla pro používání AI — zaměstnanci nevědí, jaká data smí do ChatGPT zadávat, zda mohou AI výstupy publikovat bez kontroly.',
        'Zkontrolujte interní dokumenty — existuje AI politika, směrnice nebo alespoň emailové pokyny?',
        'Stačí i jednoduchý dokument "5 pravidel pro používání AI ve firmě".',
    ],
    # Provider
    'develops_own_ai': [
        'Koho se zeptat: CTO, vedení firmy, produktový manažer, vývojový tým.',
        'Příklad: Firma vyvíjí vlastní ML model pro doporučování produktů, integruje AI do svého SaaS produktu, trénuje vlastní jazykový model.',
        'Zkontrolujte, zda produkty nebo služby firmy obsahují AI/ML funkce.',
        'Ověřte s vývojovým týmem, zda firma trénuje vlastní modely nebo fine-tunuje existující.',
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
