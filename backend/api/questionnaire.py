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
from backend.api.auth import AuthUser, get_optional_user, get_current_user

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
        "description": "Řeknete nám, čím se zabýváte, a my přizpůsobíme otázky a dokumentaci přímo na míru.",
        "questions": [
                        {
                "key": "company_legal_name",
                "text": "Obchodní firma (název společnosti nebo jméno OSVČ):",
                "type": "text",
                "help_text": "Přesný název tak, jak je zapsán v obchodním rejstříku nebo živnostenském rejstříku.\nPříklady:\n1) ACME Solutions s.r.o.\n2) Jan Novák — grafický design\n3) TechStart a.s.",
                "risk_hint": None,
                "ai_act_article": None,
            },
            {
                "key": "company_ico",
                "text": "IČO (identifikační číslo osoby):",
                "type": "text",
                "help_text": "8místné číslo z obchodního nebo živnostenského rejstříku. Slouží k identifikaci vaší firmy v oficiální dokumentaci.\nPříklady: 12345678, 05123456.",
                "risk_hint": None,
                "ai_act_article": None,
            },
            {
                "key": "company_address",
                "text": "Sídlo firmy (adresa):",
                "type": "address",
                "help_text": "Adresa sídla dle rejstříku — použijeme ji v Compliance Reportu, na transparenční stránce a v oficiální dokumentaci.",
                "risk_hint": None,
                "ai_act_article": None,
            },
            {
                "key": "company_contact_email",
                "text": "Kontaktní e-mail pro AI záležitosti:",
                "type": "text",
                "help_text": "E-mail, na který se mohou obracet zákazníci, zaměstnanci nebo dozorové orgány ohledně vašeho používání AI. Zobrazí se na transparěnční stránce.\nPříklad: ai@vase-firma.cz nebo info@vase-firma.cz",
                "risk_hint": None,
                "ai_act_article": "čl. 50 — transparentnost a informování",
            },
            {
                "key": "company_phone",
                "text": "Kontaktní telefon:",
                "type": "text",
                "help_text": "Telefonní číslo pro kontakt ohledně AI záležitostí. Zobrazí se v dokumentaci a na transparenční stránce.\nPříklad: +420 123 456 789",
                "risk_hint": None,
                "ai_act_article": None,
            },
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
                "help_text": "Vyberte všechna odvětví, která se vás týkají.\nPříklady:\n1) E-shop prodávající oblečení.\n2) Účetní kancelář zpracovávající daňová přiznání.\n3) Autoservis s online objednávkami.",
                "risk_hint": None,
                "ai_act_article": None,
            },
            {
                "key": "eshop_platform",
                "text": "Na jaké platformě provozujete svůj e-shop / web?",
                "type": "multi_select",
                "options": [
                    "Shoptet",
                    "WooCommerce (WordPress)",
                    "Shopify",
                    "PrestaShop",
                    "Magento / Adobe Commerce",
                    "Upgates",
                    "Shopsys",
                    "OpenCart",
                    "Nemám e-shop",
                    "Jiné",
                ],
                "help_text": "Tato informace je zásadní pro implementaci transparenční stránky AI Act — každá platforma vyžaduje jiný způsob nasazení.\n\nPříklady:\n1) Shoptet — nejrozšířenější český e-shop systém.\n2) WooCommerce — plugin pro WordPress.\n3) Shopify — cloudová platforma.\n\nPokud máte vlastní řešení, web na míru nebo statický web, vyberte 'Jiné' a napište nám jaký systém používáte.",
                "followup": {
                    "condition": "Jiné",
                    "fields": [
                        {"key": "eshop_platform_other", "label": "Jakou platformu používáte?", "type": "text"},
                    ]
                },
                "risk_hint": None,
                "ai_act_article": "čl. 50 — transparentnost a informování (implementace transparenční stránky)",
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
                "help_text": "Malé a střední podniky (do 250 zaměstnanců) mají dle AI Act některé úlevy.\nPříklady:\n1) OSVČ grafik.\n2) Restaurace s 5 zaměstnanci.\n3) Výrobní firma se 120 lidmi.",
                "risk_hint": None,
                "ai_act_article": "čl. 62 — povinnosti MSP a start-upů",
            },
                        {
                "key": "company_annual_revenue",
                "text": "Jaký je přibližný roční obrat vaší firmy?",
                "type": "single_select",
                "options": [
                    "Do 2 mil. Kč",
                    "2–10 mil. Kč",
                    "10–50 mil. Kč",
                    "50–250 mil. Kč",
                    "250 mil. – 1 mld. Kč",
                    "Nad 1 mld. Kč",
                ],
                "help_text": "Potřebujeme pro výpočet maximální výše pokut dle AI Act (pokuty se počítají jako % z celosvětového obratu). Údaj je důvěrný a slouží pouze pro vaši compliance dokumentaci.\n\n💡 Nemusíte odpovídat přesně — stačí přibližný rozsah.",
                "risk_hint": None,
                "ai_act_article": "čl. 99 — správní pokuty (% z obratu)",
            },
{
                "key": "develops_own_ai",
                "text": "Vyvíjíte vlastní AI systémy nebo modely?",
                "type": "yes_no_unknown",
                "help_text": "Myslíme tím, že jste primární autoři AI systému — navrhli jste architekturu, trénujete vlastní model, nebo vyrábíte AI produkt.\n\nPříklady ANO:\n1) IT firma trénuje vlastní ML model pro predikci poptávky.\n2) Startup vyvíjí AI chatbota pro klienty.\n3) E-shop vytváří vlastní AI doporučovací engine.\n\nPříklady NE (to je Q36):\n1) Používáte ChatGPT API a přizpůsobujete si prompty.\n2) Fine-tunujete cizí model na svých datech.\n3) Přebudováváte zakoupený nástroj na jiný účel.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "ai_role", "label": "Jaká je vaše role?", "type": "multi_select",
                         "options": ["Vyvíjíme AI (provider)", "Nasazujeme AI od jiných (deployer)", "Importujeme AI do EU (importer)", "Distribuujeme AI (distributor)", "Jiné"]},
                        {"key": "ai_provider_warning", "label": "⚠️ Jako poskytovatel AI systému (čl. 3 bod 3) máte rozsáhlejší povinnosti: technická dokumentace (příloha IV), posouzení shody (čl. 16), označení CE, systém řízení kvality. **AIshield vám pomůže s kompletní dokumentací.**", "type": "info"},
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
                         "options": ["Salesforce", "HubSpot", "ChatGPT", "Claude", "Gemini", "Jiný CRM", "Jiný"]},
                        {"key": "scoring_scope", "label": "Kdo je hodnocen?", "type": "multi_select",
                         "options": ["Zaměstnanci", "Zákazníci"]},
                        {"key": "scoring_banned_warning", "label": "🚫 ZAKÁZANÝ SYSTÉM — Sociální scoring je výslovně zakázán čl. 5 odst. 1 písm. c) AI Act. Pokuta až 35 milionů EUR nebo 7 % celosvětového obratu. Okamžitě ukončete provoz tohoto systému a konzultujte s právníkem. Na toto nemáme kapacity ani kompetence — jedná se o protiprávní jednání, které vyžaduje právní řešení.", "type": "info"},
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
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "manipulation_warning", "label": "🚫 ZAKÁZANÝ SYSTÉM — Podprahová manipulace pomocí AI je výslovně zakázána čl. 5 odst. 1 písm. a) AI Act. Pokuta až 35 milionů EUR nebo 7 % celosvětového obratu. Okamžitě ukončete provoz tohoto systému a konzultujte s právníkem. V této oblasti nemáme kapacity ani kompetence vám pomoci — jedná se o protiprávní jednání. Připravíme vám kompletní podklady pro právní konzultaci, aby právník mohl ihned řešit vaši situaci.", "type": "info"},
                    ]
                },
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
                        {"key": "biometric_info", "label": "ℹ️ Biometrická identifikace v reálném čase ve veřejném prostoru je zakázána (čl. 5 odst. 1 písm. h). V soukromých prostorách (kanceláře, sklady) jde o vysoce rizikový systém (Příloha III) — není zakázaný, ale vyžaduje rozšířenou dokumentaci, posouzení dopadů (FRIA) a registraci. AIshield vám připraví veškerou potřebnou dokumentaci.", "type": "info"},
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
                         "options": ["Pouze veřejná data", "Interní dokumenty", "Osobní údaje zákazníků", "Finanční data", "Zdrojový kód / obchodní tajemství", "Jiné"],
                         "warning": {"Osobní údaje zákazníků": "⚠️ Pozor — vkládání osobních údajů do AI nástrojů může znamenat předání dat třetí straně mimo EU (čl. 44 GDPR). Zkontrolujte DPA s poskytovatelem AI a zvažte anonymizaci dat.", "Finanční data": "⚠️ Finanční data mohou podléhat regulaci (zákon o účetnictví, AML). Zvažte, zda AI nástroj splňuje požadavky na zabezpečení a zda nemůže dojít k úniku citlivých informací."}},
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
                         "options": ["GitHub Copilot", "Cursor", "ChatGPT", "Claude", "Gemini", "Codeium", "Amazon CodeWhisperer", "Jiný"]},
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
                "help_text": "Příklady:\n1) Marketing generuje obrázky produktů v Midjourney pro sociální sítě.\n2) Grafik vytváří bannery v Canva AI (kreativní oddělení).\n3) Copywriter píše popisky produktů v Jasper / Copy.ai.\n4) ChatGPT generuje texty, obrázky (DALL-E) i kód.\n5) Gemini (Google) generuje obrázky, texty i videa.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "content_tool_name", "label": "Které nástroje používáte?", "type": "multi_select",
                         "options": ["ChatGPT / GPT-4o", "Gemini (Google)", "Claude (Anthropic)", "DALL-E", "Midjourney", "Stable Diffusion", "Canva AI", "Adobe Firefly", "Jasper", "Copy.ai", "Suno AI", "Jiný"]},
                        {"key": "content_published", "label": "Kde AI obsah používáte?", "type": "multi_select",
                         "options": ["Web / sociální sítě", "Interní materiály", "E-maily zákazníkům", "Reklamní kampaně", "Jiné"]},
                        {"key": "content_transparency_info", "label": "ℹ️ Podle čl. 50 odst. 4 AI Act musí být AI-generovaný obsah zveřejněný pro veřejnost označen jako uměle vytvořený (platí od 2. srpna 2026). Týká se to textů, obrázků i videí na webu, sociálních sítích a v reklamních kampaních. V rámci služby AIshield vám dodáme pokyny pro správné označování AI obsahu.", "type": "info"},
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
                         "options": ["ChatGPT (Sora)", "Gemini / VEO3 (Google)", "HeyGen", "Synthesia", "ElevenLabs", "D-ID", "Murf AI", "Jiný"]},
                        {"key": "deepfake_disclosure_info", "label": "ℹ️ Od 2. srpna 2026 je podle čl. 50 AI Act povinné označit veškerý deep-fake obsah jako uměle vytvořený. V rámci služby AIshield vám dodáme profesionálně zpracovanou dokumentaci včetně pokynů pro správné označování AI obsahu.", "type": "info"},
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
                         "options": ["LinkedIn Recruiter", "Teamio", "LMC/Jobs.cz AI", "Sloneek", "Prace.cz AI", "ChatGPT", "Claude", "Gemini", "Jiné"]},
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
                        {"key": "monitoring_compliance_info", "label": "ℹ️ Zaměstnanci musí být informováni o sledování dle GDPR i AI Act (čl. 26 odst. 7). V rámci služby AIshield vám dodáme profesionálně zpracovanou prezentaci (PowerPoint), kterou zaměstnancům představíte, a dokumentaci informování zaměstnanců.", "type": "info"},
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
                         "options": ["Kamerový systém", "Call centrum analýza", "ChatGPT", "Claude", "Gemini", "Jiný"]},
                        {"key": "emotion_context", "label": "V jakém kontextu? (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Pracovní prostředí", "Zákaznický servis", "Vzdělávání", "Bezpečnost", "Jiné"],
                         "warning": {"Pracovní prostředí": "🚫 ZAKÁZANÁ PRAKTIKA — Rozpoznávání emocí zaměstnanců na pracovišti je výslovně zakázáno čl. 5 odst. 1 písm. f) AI Act. Výjimky existují pouze pro zdravotní a bezpečnostní účely. Pokuta až 35 milionů EUR nebo 7 % celosvětového obratu. Doporučujeme okamžitě konzultovat s právníkem."}},
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
                         "options": ["Fakturoid", "Money S5", "ABRA", "Pohoda", "iDoklad", "Helios", "ChatGPT", "Claude", "Gemini", "Jiné"]},
                        {"key": "accounting_decisions", "label": "Dělá AI autonomní finanční rozhodnutí?", "type": "select",
                         "options": ["Ne, pouze asistuje", "Ano, schvaluje platby"],
                         "warning": {"Ano, schvaluje platby": "AI systém autonomně schvalující platby bez lidského dohledu může spadat do kategorie vysoce rizikových AI systémů. Dle AI Act je nutné zajistit lidský dohled nad finančními rozhodnutími (čl. 14) a transparentnost vůči dotčeným osobám."}},
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
                         "options": ["CRIF – Czech Credit Bureau", "Bisnode / Dun & Bradstreet", "Scoring Solutions", "ChatGPT", "Claude", "Gemini", "Jiný"]},
                        {"key": "credit_impact", "label": "Ovlivňuje AI rozhodnutí o úvěrech/smlouvách?", "type": "select",
                         "options": ["Ano, přímo rozhoduje", "Ne"],
                         "warning": {"Ano, přímo rozhoduje": "⚠️ Automatické rozhodování o úvěrech bez lidského dohledu spadá do kategorie vysoce rizikových AI systémů (Příloha III, bod 5b). Vaše firma musí provést registraci v EU databázi a zajistit průběžné monitorování — toto je zákonná povinnost, kterou musíte splnit interně. V rámci dokumentace vám poskytneme potřebné podklady a doporučení."}},
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
                         "options": ["Guidewire", "NESS / Allianz AI", "ČPP / ČSOB interní AI", "ChatGPT", "Claude", "Gemini", "Jiný"]},
                        {"key": "insurance_impact", "label": "Ovlivňuje AI cenu nebo dostupnost pojištění?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ano": "⚠️ AI systém ovlivňující cenu nebo dostupnost pojištění je vysoce rizikový dle Přílohy III, bod 5a. Vaše firma musí zajistit posouzení shody, registraci v EU databázi, průběžné monitorování a právo pojistníka na vysvětlení rozhodnutí — toto jsou zákonné povinnosti, které musíte splnit interně. V rámci dokumentace vám poskytneme podklady a doporučení."}},
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
                         "options": ["Smartsupp", "Tidio", "Intercom", "Drift", "ChatGPT API", "Claude API", "Gemini API", "Chatbot.cz", "Jiné"]},
                        {"key": "chatbot_compliance_info", "label": "ℹ️ Podle čl. 50 AI Act musí být zákazníci informováni, že komunikují s AI systémem (od 2. srpna 2026). V rámci služby AIshield vám dodáme profesionálně zpracovanou dokumentaci včetně textu oznámení pro chatbota.", "type": "info"},
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
                         "options": ["Freshdesk AI", "Zendesk AI", "Intercom", "ChatGPT", "Claude", "Gemini", "Jiné"]},
                        {"key": "email_compliance_info", "label": "ℹ️ Podle čl. 50 AI Act musí být zákazníci informováni, že komunikují s AI systémem (od 2. srpna 2026). Součástí vaší dokumentace bude text informování zákazníků.", "type": "info"},
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
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "⚠️ AI rozhodující o právech zákazníků bez možnosti lidského přezkumu porušuje čl. 14 AI Act. Zákazník má právo požadovat, aby rozhodnutí přezkoumal člověk. Musíte si nastavit interní postupy tak, aby rozhodování AI nebylo protiprávní — v rámci dokumentace vám dodáme doporučení, jak tyto procesy zavést."}},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 14 — lidský dohled nad vysoce rizikovými systémy",
            },
            {
                "key": "uses_dynamic_pricing",
                "text": "Používáte AI k automatickému nastavování cen podle chování zákazníka?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) E-shop zvyšuje ceny víkendům podle AI predikce poptávky.\n2) Letenky zdražují, když AI detekuje vyšší zájem z určité lokace.\n3) AI nabízí různé ceny vracejícímu se vs. novému zákazníkovi. Dynamické ceny dle sezóny jsou běžné — problém je cílená personalizace.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "pricing_tool", "label": "Které nástroje používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Prisync", "Competera", "Dynamic Yield", "ChatGPT", "Claude", "Gemini", "Jiný"]},
                        {"key": "pricing_basis", "label": "Na základě čeho se ceny mění?", "type": "multi_select",
                         "options": ["Historie nákupů", "Lokace zákazníka", "Čas / sezóna", "Profil zákazníka", "Poptávka", "Jiné"]},
                        {"key": "pricing_compliance_info", "label": "⚠️ Personalizace cen bez informování zákazníka může představovat nekalou obchodní praktiku a porušení transparentnosti dle AI Act. Musíte si nastavit interní postupy tak, abyste si nepočínali protiprávně — v rámci dokumentace vám dodáme doporučení.", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 5 odst. 1 písm. a/b) — potenciálně manipulativní, pokud cílí na zranitelné osoby",
            },
            {
                "key": "uses_ai_for_children",
                "text": "Používáte AI systémy, které přímo interagují s dětmi nebo nezletilými?",
                "type": "yes_no_unknown",
                "help_text": "Příklady ANO:\n1) AI chatbot/tutor pro žáky základních škol.\n2) AI doporučovací systém v dětské mobilní aplikaci.\n3) AI hra nebo edukační platforma pro děti.\n4) AI filtrování obsahu pro nezletilé.\n\nPříklady NE:\n1) AI nástroje používají pouze dospělí zaměstnanci.\n2) E-shop cílí na dospělé zákazníky.\n3) B2B produkt bez interakce s dětmi.\n\nTato otázka je relevantní pro vzdělávání, hry, dětské aplikace a služby cílené na nezletilé.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "children_ai_context", "label": "V jakém kontextu AI s dětmi interaguje?", "type": "multi_select",
                         "options": ["Vzdělávání / e-learning", "Mobilní aplikace / hry", "Doporučování obsahu", "Chatbot / virtuální asistent", "Filtrování / moderování obsahu", "Jiné"]},
                        {"key": "children_ai_warning", "label": "⚠️ AI systémy interagující s dětmi jsou dle Přílohy III AI Act považovány za vysoce rizikové. Musíte zajistit posouzení shody, technickou dokumentaci a zvýšenou ochranu. Čl. 5 zakazuje AI manipulaci zranitelných skupin, kam děti patří. **AIshield vám pomůže s compliance dokumentací pro AI cílené na děti.**", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "Příloha III bod 3 — vzdělávání + čl. 5 odst. 1 písm. a,b) — ochrana zranitelných skupin",
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
                         "options": ["Siemens MindSphere", "ABB Ability", "Honeywell Forge", "Schneider Electric EcoStruxure", "GE Digital Predix", "Jiný"]},
                        {"key": "infra_sector", "label": "Sektor (vyberte vše, co platí)", "type": "multi_select",
                         "options": ["Energetika", "Doprava", "Vodohospodářství", "Telekomunikace", "Zdravotnictví", "Jiné"]},
                        {"key": "infra_warning", "label": "⚠️ KRITICKÁ INFRASTRUKTURA — AI jako bezpečnostní komponenta v kritické infrastruktuře (Příloha III bod 2) podléhá přísnému režimu. Registrace probíhá u národního orgánu (v ČR pravděpodobně NÚKIB), nikoli ve veřejné EU databázi (čl. 49 odst. 4). Povinnosti: systém řízení rizik (čl. 9), technická dokumentace (Příloha IV), posouzení shody, CE označení, post-market monitoring. Navíc platí zákon o kybernetické bezpečnosti (181/2014 Sb.). **Doporučujeme konzultaci s právníkem specializovaným na AI Act — AIshield vám připraví veškeré podklady.**", "type": "info"},
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
                        {"key": "safety_component_warning", "label": "⚠️ AI JAKO BEZPEČNOSTNÍ KOMPONENTA — Plná účinnost od 2. 8. 2027 (Příloha I produkty). Musíte: (1) provést posouzení shody dle čl. 43, (2) vypracovat technickou dokumentaci dle Přílohy IV, (3) zajistit CE označení dle čl. 48, (4) zaregistrovat v EU databázi dle čl. 49, (5) nastavit post-market monitoring dle čl. 72. Interní posouzení shody (Příloha VI) je dostačující — notifikovaný subjekt NENÍ potřeba (kromě biometriky). **AIshield vám připraví pre-filled dokumentaci a checklist.**", "type": "info"},
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
                         "warning": {"Ne": "U AI systémů zpracovávajících osobní údaje se důrazně doporučuje provedení DPIA (posouzení vlivu na ochranu dat) dle GDPR čl. 35. V rámci Compliance Kitu vám vygenerujeme předvyplněnou DPIA šablonu s údaji z vašeho dotazníku — seznam AI systémů, rizikové úrovně a firemní data. Stačí doplnit specifika a nechat podepsat DPO nebo vedením firmy."}},
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
                    "condition": "yes",
                    "fields": [
                        {"key": "data_location_provider", "label": "Které AI nástroje / poskytovatele používáte?", "type": "multi_select",
                         "options": ["ChatGPT (OpenAI)", "Google Gemini", "Microsoft Copilot", "Claude (Anthropic)", "Perplexity", "Midjourney", "DeepL", "Vlastní server v ČR/EU", "Jiný"]},
                        {"key": "data_location_eu_detail", "label": "Kde přesně jsou data uložena?", "type": "multi_select",
                         "options": ["Azure EU (západní Evropa)", "AWS Frankfurt / Irsko", "GCP EU", "Vlastní server v ČR/EU", "Hetzner / OVH / jiný EU hosting", "Nevím přesně", "Jiné"]},
                        {"key": "data_location_eu_ok", "label": "✅ Uložení dat v EU je z pohledu GDPR ideální stav. Do dokumentace zaznamenáme konkrétní lokaci.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "data_location_provider", "label": "Které AI nástroje / poskytovatele používáte?", "type": "multi_select",
                         "options": ["ChatGPT (OpenAI)", "Google Gemini", "Microsoft Copilot", "Claude (Anthropic)", "Perplexity", "Midjourney", "DeepL", "Vlastní server v ČR/EU", "Jiný"]},
                        {"key": "data_outside_eu_warning", "label": "⚠️ Data mimo EU vyžadují právní základ dle GDPR čl. 44+ (standardní smluvní doložky SCC nebo rozhodnutí o adekvaci). Ověřte, zda máte s poskytovatelem uzavřenou DPA (Data Processing Agreement). **V rámci dokumentace vám pomůžeme identifikovat rizika a doporučíme kroky k nápravě.**", "type": "info"},
                    ]
                },
                "followup": {
                    "condition": "unknown",
                    "fields": [
                        {"key": "data_location_provider", "label": "Pomůžeme vám to zjistit — které AI nástroje používáte?", "type": "multi_select",
                         "options": ["ChatGPT (OpenAI)", "Google Gemini", "Microsoft Copilot", "Claude (Anthropic)", "Perplexity", "Midjourney", "DeepL", "Vlastní server v ČR/EU", "Jiný"]},
                        {"key": "data_location_info", "label": "ℹ️ Většina velkých AI poskytovatelů (OpenAI, Google, Anthropic) ukládá data primárně v USA. Na základě vámi vybraných nástrojů zjistíme lokaci dat a zahrneme ji do dokumentace.", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "Nařízení GDPR čl. 44+ — přenos dat do třetích zemí",
            },
            {
                "key": "has_ai_vendor_contracts",
                "text": "Máte s dodavateli AI systémů uzavřeny smlouvy pokrývající zpracování dat a odpovědnost?",
                "type": "yes_no_unknown",
                "help_text": "Příklady ANO:\n1) S OpenAI máte podepsanou DPA (Data Processing Agreement).\n2) S dodavatelem chatbotu máte SLA s definovanou dostupností.\n3) Ve smlouvě je jasně uvedeno, kdo odpovídá za chyby AI.\n\nPříklady NE:\n1) Používáte ChatGPT přes free/personal účet bez firemní smlouvy.\n2) AI nástroj jste si jen stáhli a nainstalovali bez jakékoliv smlouvy.\n3) S dodavatelem AI nemáte řešenou odpovědnost za škody.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "vendor_contract_scope", "label": "Co vaše smlouvy pokrývají? (vyberte vše)", "type": "multi_select",
                         "options": ["DPA (zpracování osobních údajů)", "SLA (dostupnost a kvalita služby)", "Odpovědnost za škody způsobené AI", "Práva k datům a výstupům", "Podmínky ukončení spolupráce", "Audit / kontrola dodavatele"]},
                        {"key": "vendor_contract_ok_info", "label": "✅ Výborně! Smluvní pokrytí s dodavateli AI je důležité pro GDPR i AI Act compliance. Do dokumentace zaznamenáme rozsah vašich smluv.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "vendor_contract_warning", "label": "⚠️ Bez smlouvy s dodavatelem AI systému riskujete porušení GDPR čl. 28 (zpracovatel bez smlouvy) a nemáte právně ošetřenou odpovědnost za chyby AI. Doporučujeme uzavřít alespoň DPA s každým poskytovatelem AI, kterému předáváte firemní nebo osobní data. **V rámci Compliance Kitu vám vygenerujeme **Dodavatelský checklist** — kontrolní seznam všech náležitostí, které musí vaše smlouvy s dodavateli AI pokrývat (DPA, SLA, GDPR záruky, opt-out z trénování a další).**", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "GDPR čl. 28 — zpracovatel, AI Act čl. 25-26 — povinnosti v hodnotovém řetězci",
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
                         "warning": {"Ne": "Pro doložení splnění povinnosti čl. 4 AI Act je vhodné mít prezenční listinu s podpisy účastníků. **AIshield.cz vám v rámci služeb dodá kompletní školící prezentaci + profesionálně zpracovanou prezenční listinu.**"}},
                        {"key": "training_audience_size", "label": "Kolik lidí potřebuje proškolit?", "type": "select",
                         "options": ["1–5 osob", "6–20 osob", "21–50 osob", "51–100 osob", "100+ osob"]},
                        {"key": "training_audience_level", "label": "Jaká je technická úroveň školených osob?", "type": "select",
                         "options": [
                             "Netechničtí (administrativa, obchod, marketing)",
                             "Středně technicky zdatní (manažeři, analytici)",
                             "Techničtí (IT, vývojáři, data analytici)",
                             "Mix — různé úrovně",
                         ]},
                        {"key": "training_info", "label": "ℹ️ Součástí všech AIshield balíčků je profesionální školící prezentace (PowerPoint) a kompletní dokumentace včetně prezenční listiny.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "training_no_warning", "label": "⚠️ Článek 4 AI Act vyžaduje „dostatečnou úroveň AI gramotnosti“ zaměstnanců — tato povinnost platí již od 2. února 2025. Nesplnění může vést k pokutě až 15 milionů EUR. **Součástí všech AIshield balíčků je kompletní školící prezentace (PowerPoint) + profesionálně zpracovaná prezenční listina, kterou zaměstnanci podepíšou.**", "type": "info"},
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
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "guidelines_scope", "label": "Co vaše pravidla pokrývají? (vyberte vše)", "type": "multi_select",
                         "options": [
                             "Které AI nástroje smí zaměstnanci používat",
                             "Jaká data se smí do AI vkládat",
                             "Kdo schvaluje nové AI nástroje",
                             "Pravidla pro AI generovaný obsah",
                             "Ochrana osobních údajů při práci s AI",
                             "Postup při AI incidentu",
                         ]},
                        {"key": "guidelines_format", "label": "V jakém formátu pravidla máte?", "type": "select",
                         "options": [
                             "Písemná směrnice / interní předpis",
                             "Součást jiného dokumentu (IT politika, GDPR apod.)",
                             "Ústní pravidla / nepsaná dohoda",
                         ]},
                        {"key": "guidelines_ok_info", "label": "✅ Výborně! Vaši stávající směrnici rozšíříme o požadavky AI Act a dodáme kompletní AI politiku firmy na míru.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "guidelines_no_warning", "label": "⚠️ Bez interní směrnice zaměstnanci nevědí, jaká data smí vkládat do AI, zda mohou AI výstupy publikovat, ani kdo je zodpovědný za dodržování předpisů. Dle čl. 4 AI Act musí organizace zajistit odpovědné používání AI. **Nebojte se — v rámci služby AIshield vám dodáme profesionálně zpracovanou směrnici „Pravidla pro používání AI ve firmě“, kterou si snadno přizpůsobíte.**", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 4",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 9: Lidský dohled (čl. 14, čl. 26)
    # ──────────────────────────────────────────────
    {
        "id": "human_oversight",
        "title": "Lidský dohled nad AI",
        "description": "AI Act vyžaduje, aby nad vysoce rizikovými AI systémy dohlížely kompetentní osoby.",
        "questions": [
            {
                "key": "has_oversight_person",
                "text": "Máte určenou osobu/tým zodpovědný za dohled nad AI systémy?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) IT manažer pověřený dohledem nad AI chatbotem.\n2) Compliance officer monitorující automatizované rozhodovací procesy.\n3) Tým 'AI governance' schvalující nové AI nástroje.",
                "followup": {
                    "condition": "any",
                    "fields": [
                        {"key": "oversight_warning", "label": "⚠️ Článek 14 AI Act vyžaduje lidský dohled nad AI systémy. Musíte určit odpovědnou osobu. Vyplňte prosím kontakt níže — použijeme ho v compliance dokumentaci.", "type": "info"},
                        {"key": "oversight_role", "label": "Jakou roli má osoba, která na AI dohlíží?", "type": "select",
                         "options": [
                             "Jednatel / majitel (dohlížím osobně)",
                             "IT manažer / vedoucí IT",
                             "Compliance officer",
                             "DPO (pověřenec pro ochranu osobních údajů)",
                             "Tým / komise AI governance",
                             "Jiná role"
                         ]},
                        {"key": "oversight_person_name", "label": "Jméno odpovědné osoby:", "type": "text"},
                        {"key": "oversight_person_email", "label": "E-mail odpovědné osoby:", "type": "text"},
                        {"key": "oversight_person_phone", "label": "Telefon odpovědné osoby:", "type": "text"},
                        {"key": "oversight_scope", "label": "Na co konkrétně dohlíží?", "type": "multi_select",
                         "options": [
                             "Chatbot na webu",
                             "Interní AI nástroje (ChatGPT, Copilot apod.)",
                             "AI analytiku a doporučovací systémy",
                             "AI v zákaznickém servisu",
                             "AI v HR / náboru",
                             "AI v účetnictví / financích",
                             "Vše — zastřešuje kompletní AI governance"
                         ]},
                    ]
                },

                "risk_hint": "high",
                "ai_act_article": "čl. 14 — lidský dohled",
            },
            {
                "key": "can_override_ai",
                "text": "Mohou vaši zaměstnanci přepsat nebo zrušit rozhodnutí AI systému?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) HR manažer může přepsat doporučení AI při výběru kandidátů.\n2) Operátor může ručně změnit automatické třídění zákaznických požadavků.\n3) Schvalovací proces vyžaduje lidský podpis po AI analýze.",
                                "scope_hint": "Tato otázka se vztahuje na VŠECHNY AI systémy ve firmě — nejen zákaznický servis, ale i HR, finance, interní procesy. Odpovězte ANO, pokud zaměstnanci mohou v jakémkoliv případě rozhodnutí AI přepsat nebo zrušit.",
"followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "override_scope", "label": "V jakých případech se override používá?", "type": "multi_select",
                         "options": ["Vždy — AI jen doporučuje, člověk rozhoduje", "Při reklamacích a stížnostech", "Při HR rozhodnutích", "Při finančních rozhodnutích", "Jen výjimečně / eskalace", "Jiné"]},
                        {"key": "override_ok_info", "label": "✅ Výborně! Možnost přepsat rozhodnutí AI je klíčový požadavek čl. 14 odst. 4 písm. d) AI Act. Do dokumentace zaznamenáme, v jakých případech override používáte.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "override_warning", "label": "⚠️ Článek 14 odst. 4 písm. d) AI Act vyžaduje, aby osoby pověřené lidským dohledem mohly rozhodnutí AI systému nepoužít, přepsat nebo zrušit. Bez této možnosti hrozí porušení nařízení. **AIshield vám pomůže nastavit procesy pro lidský dohled a přepisování AI rozhodnutí.**", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 14 odst. 4 písm. d) — možnost nepoužít systém nebo zrušit jeho výstup",
            },
            {
                "key": "ai_decision_logging",
                "text": "Zaznamenáváte rozhodnutí, která AI systémy dělají nebo doporučují?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Log chatbotových odpovědí pro zpětnou kontrolu.\n2) Archivace AI doporučení v CRM.\n3) Záznam automatizovaných rozhodnutí v interním systému.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "logging_method", "label": "Jakým způsobem logujete?", "type": "multi_select",
                         "options": ["Logy v aplikaci (automatické)", "Export do SIEM / centrálního logu", "Excel / tabulka", "Ticketovací systém (Jira, Freshdesk)", "Jiný"]},
                        {"key": "logging_retention", "label": "Jak dlouho logy uchováváte?", "type": "single_select",
                         "options": ["Méně než 6 měsíců", "6–12 měsíců", "1–3 roky", "Déle než 3 roky", "Nevím"],
                         "warning": {"Nevím": "⚠️ Doporučujeme zjistit dobu uchovávání logů — čl. 26 AI Act vyžaduje minimálně 6 měsíců. Ověřte u svého IT oddělení nebo správce systému."}},
                        {"key": "logging_ok_info", "label": "✅ Výborně! Čl. 26 odst. 1 písm. f) AI Act vyžaduje uchovávání logů minimálně 6 měsíců. Do dokumentace zaznamenáme váš systém logování.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "logging_warning", "label": "⚠️ Článek 26 odst. 1 písm. f) AI Act vyžaduje uchovávání automaticky generovaných protokolů po dobu nejméně 6 měsíců. Logování je klíčové pro audit a zpětnou kontrolu. AIshield vám poskytne profesionálně zpracovaný logovací protokol (co zaznamenávat, jak dlouho uchovávat, formát záznamů), ale samotné logování musíte nastavit ve svých interních systémech.", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 26 odst. 1 písm. f) — uchovávání protokolů",
            },
            {
                "key": "has_ai_register",
                "text": "Vedete interní registr/seznam všech AI systémů, které používáte?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Tabulka se seznamem AI nástrojů, jejich dodavatelů a účelů.\n2) Interní databáze AI systémů s kategorizací rizik.\n3) IT inventář, který zahrnuje i AI služby.\n\nRegistr AI systémů je základem pro compliance — bez něj nevíte, jaké povinnosti máte.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "register_contents", "label": "Co váš registr obsahuje? (vyberte vše)", "type": "multi_select",
                         "options": ["Název AI systému", "Dodavatel / poskytovatel", "Účel použití", "Kategorie rizika dle AI Act", "Odpovědná osoba", "Datum nasazení", "Typ zpracovávaných dat"]},
                        {"key": "register_ok_info", "label": "✅ Výborně! Registr AI systémů je základ compliance dle čl. 26 AI Act. Do dokumentace zaznamenáme strukturu vašeho registru a případně doporučíme rozšíření.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "register_warning", "label": "⚠️ Článek 26 AI Act vyžaduje, aby zavádějící (deployers) měli přehled o všech AI systémech, které používají. Bez registru nemůžete prokázat soulad s nařízením. **V rámci služby AIshield vám dodáme profesionálně zpracovaný registr AI systémů — jednoduchou tabulku, kterou si snadno vyplníte.**", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 26 — povinnosti zavádějícího (deployer)",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 10: Role v hodnotovém řetězci AI (poskytovatel vs. zavádějící)
    # ──────────────────────────────────────────────
    {
        "id": "ai_role",
        "title": "Vaše role v AI ekosystému",
        "description": "AI Act rozlišuje různé povinnosti pro poskytovatele (výrobce) a zavádějící (uživatele) AI systémů.",
        "questions": [
            {
                "key": "modifies_ai_purpose",
                "text": "Měníte účel nebo podstatně upravujete zakoupený AI systém?",
                "type": "yes_no_unknown",
                "help_text": "Sem patří případy, kdy podstatně měníte existující AI systém třetí strany — fine-tuning, změna účelu, přetrénování. Dle čl. 25 AI Act se tím můžete stát poskytovatelem.\n\nPříklady ANO:\n1) Fine-tunujete GPT/Claude na vlastních datech pro specifický účel.\n2) Přetrénováváte jazykový model pro úplně jiné použití.\n3) Měníte účel AI nástroje (např. z marketingu na HR screening).\n\nPříklady NE:\n1) Používáte ChatGPT/Claude tak, jak je, bez úprav.\n2) Jen píšete vlastní prompty (to není úprava systému).\n3) Používáte RAG bez změny základního modelu.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "modified_ai_warning", "label": "⚠️ Pokud podstatně měníte účel AI systému, můžete se stát jeho poskytovatelem (čl. 25) a přebíráte odpovídající povinnosti. Doporučujeme konzultaci.", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 25 — další zavádějící, kteří se považují za poskytovatele",
            },
            {
                "key": "uses_gpai_api",
                "text": "Integrujete API velkých jazykových modelů (LLM) do vlastních produktů nebo služeb?",
                "type": "yes_no_unknown",
                "help_text": "Příklady ANO:\n1) Voláte ChatGPT/Claude/Gemini API z vaší aplikace pro zákazníky.\n2) Chatbot na vašem webu je poháněn LLM přes API.\n3) Váš SaaS produkt generuje texty/analýzy pomocí LLM.\n\nPříklady NE:\n1) Zaměstnanci ručně používají ChatGPT (to patří do sekce interní AI).\n2) Pouze testujete API interně.\n3) Nepoužíváte žádné LLM API.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "gpai_provider", "label": "Které API používáte?", "type": "multi_select",
                         "options": ["OpenAI (GPT-4o / o3 / o4-mini)", "Anthropic (Claude)", "Google (Gemini)", "Meta (Llama)", "Mistral", "Vlastní model / Jiné"]},
                        {"key": "gpai_customer_facing", "label": "Jsou výstupy LLM viditelné přímo zákazníkům?", "type": "select",
                         "options": ["Ano, zákazníci vidí AI výstupy přímo", "Částečně — AI navrhuje, člověk kontroluje", "Ne — pouze interní použití"],
                         "warning": {"Ano, zákazníci vidí AI výstupy přímo": "⚠️ Od 2. srpna 2025 platí pravidla pro GPAI (čl. 51-54 AI Act). Jako deployer integrující LLM do zákaznického produktu máte povinnost transparentnosti — zákazníci musí vědět, že interagují s AI (čl. 50). **AIshield vám pomůže s GPAI compliance.**"}},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 51-54 — GPAI povinnosti, čl. 50 — transparentnost",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 11: Řízení incidentů a rizik
    # ──────────────────────────────────────────────
    {
        "id": "incident_management",
        "title": "Řízení AI incidentů",
        "description": "Připravenost na situace, kdy AI systém selže nebo způsobí újmu.",
        "questions": [
            {
                "key": "has_incident_plan",
                "text": "Máte plán pro případ, že AI systém udělá chybu nebo způsobí škodu?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Postup při chybné AI odpovědi zákazníkovi.\n2) Eskalační proces při diskriminačním výstupu AI.\n3) Plán okamžitého vypnutí AI systému.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "incident_plan_scope", "label": "Co váš plán pokrývá? (vyberte vše)", "type": "multi_select",
                         "options": [
                             "Postup při chybné AI odpovědi zákazníkovi",
                             "Eskalační proces (kdo rozhoduje o dalších krocích)",
                             "Okamžité odstavení AI systému",
                             "Hlášení incidentu dozorové autoritě",
                             "Informování dotčených osob",
                             "Záznamy a dokumentace incidentu",
                         ]},
                        {"key": "incident_escalation_chain", "label": "Kdo je v eskalačním řetězci? (vyberte vše, co platí)", "type": "multi_select",
                         "options": [
                             "Operátor / zaměstnanec, který incident zjistí",
                             "Vedoucí oddělení / manažer",
                             "IT oddělení / správce systému",
                             "Jednatel / vedení firmy",
                             "DPO / Compliance officer",
                             "Externí právní poradce",
                         ]},
                        {"key": "incident_communication", "label": "Jak komunikujete incidenty interně?", "type": "multi_select",
                         "options": [
                             "E-mail",
                             "Telefon / krizová linka",
                             "Interní chat (Teams, Slack apod.)",
                             "Ticketovací systém (Jira, Freshdesk apod.)",
                             "Nemáme definovaný kanál",
                         ],
                         "warning": {"Nemáme definovaný kanál": "⚠️ Důrazně doporučujeme stanovit jasný komunikační kanál pro AI incidenty. Bez něj hrozí zpomalená reakce a vyšší škody. AIshield vám navrhne vhodný komunikační postup."}},
                        {"key": "incident_existing_ok", "label": "✅ Výborně! Na základě těchto informací doplníme váš stávající plán o požadavky AI Act — zejména povinné hlášení závažných incidentů dle čl. 73 a komunikaci s dozorovou autoritou.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "incident_warning", "label": "⚠️ Nařízení vyžaduje sledování závažných incidentů a jejich hlášení (čl. 73). Mít připravený plán je nejen zákonná povinnost, ale i dobrá praxe. **V rámci služby AIshield vám dodáme profesionálně zpracovaný plán řízení AI incidentů.**", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 73 — hlášení závažných incidentů",
            },
            {
                "key": "monitors_ai_outputs",
                "text": "Pravidelně kontrolujete kvalitu a správnost výstupů vašich AI systémů?",
                "type": "yes_no_unknown",
                "help_text": "Táže se, jestli někdo ve vaší firmě pravidelně kontroluje, že AI dělá to, co má.\n\nPříklady ANO:\n1) Vedoucí čte náhodné odpovědi chatbota a ověřuje správnost.\n2) Tým jednou měsíčně kontroluje AI doporučení.\n3) Vývojář monitoruje přesnost ML modelu.\n\nPříklady NE:\n1) AI chatbot běží a nikdo jeho odpovědi nekontroluje.\n2) AI generuje reporty, které se posílají přímo zákazníkům.\n\nPokud AI používáte jen občas pro sebe (např. ChatGPT), odpovězte Ne.",
                "scope_hint": "Tato otázka se týká všech AI systémů, které ve firmě používáte. Odpovězte ANO, pokud někdo pravidelně kontroluje správnost výstupů AI (např. čte odpovědi chatbota, ověřuje AI doporučení). Odpovězte NE, pokud AI běží bez jakékoliv kontroly kvality výstupů.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "monitoring_frequency", "label": "Jak často kontrolujete výstupy AI?", "type": "single_select",
                         "options": ["Denně", "Týdně", "Měsíčně", "Nepřípravidělně / ad hoc"]},
                        {"key": "monitoring_ok_info", "label": "✅ Výborně! Pravidelný monitoring výstupů AI je základem čl. 9 AI Act (systém řízení rizik). Do dokumentace zaznamenáme váš monitoring proces.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "monitoring_warning", "label": "⚠️ Článek 9 AI Act vyžaduje průběžné řízení rizik po celou dobu životního cyklu AI systému, včetně monitoringu výstupů. Pravidelná kontrola kvality je základem pro splnění této povinnosti. **Monitoring AI výstupů je důležitou součástí vaší compliance strategie.**", "type": "info"},
                        {"key": "monitoring_internal_note", "label": "⚠️ Důležité: Monitoring kvality AI výstupů je interní záležitost vaší firmy. Vy nejlépe znáte své procesy a víte, co je „správná“ odpověď chatbota nebo „přesné“ doporučení. V rámci Compliance Kitu vám vygenerujeme **Monitoring plán AI** — konkrétní KPI, metriky a měsíční checklist, co a jak často kontrolovat — ale samotné kontroly musíte provádět vy ve svých systémech.", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 9 — systém řízení rizik",
            },
            {
                "key": "tracks_ai_changes",
                "text": "Dokumentujete změny ve vlastních AI systémech, které provozujete nebo vyvíjíte?",
                "type": "yes_no_unknown",
                "help_text": "Příklady:\n1) Záznam o aktualizaci chatbota na novou verzi.\n2) Poznámka v tabulce, že jste změnili poskytovatele AI analytiky.\n3) Dokumentace přechodu z jednoho AI nástroje na jiný.\n\nPozor: Nejedná se o sledování aktualizací nástrojů třetích stran (např. kdy OpenAI vydal novou verzi GPT). Jde o vaše vlastní rozhodnutí — kdy jste vy změnili, co používáte a jak.",
                "scope_hint": "Tato otázka se týká firem, které PROVOZUJÍ nebo VYVÍJEJÍ vlastní AI řešení (chatbot na webu, AI analytika, automatizace procesů). Pokud jste OSVČ nebo malá firma a pouze občas používáte ChatGPT či Copilot bez vlastních úprav, tato otázka se vás netýká — odpovězte \"Ne\".",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "changes_tracking_method", "label": "Jak změny dokumentujete?", "type": "multi_select",
                         "options": ["Verze v Git / repozitáři", "Interní tabulka / evidence", "Ticketovací systém (Jira)", "Changelog v dokumentaci", "Jiný"]},
                        {"key": "changes_ok_info", "label": "✅ Výborně! Dokumentace změn je požadavek Přílohy IV bod 6 AI Act. Do compliance dokumentace zaznamenáme váš systém evidence změn.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "changes_warning", "label": "⚠️ Příloha IV bod 6 AI Act vyžaduje popis všech změn provedených během životního cyklu AI systému. Bez dokumentace změn nebudete moci prokázat soulad s nařízením. **AIshield vám pomůže zavést jednoduché verzování a evidenci změn vašich AI systémů.**", "type": "info"},
                        {"key": "changes_internal_note", "label": "⚠️ Důležité: Evidenci změn AI systémů si musíte vést interně — stačí i jednoduchá tabulka s datem, názvem systému a popisem změny. AIshield vám dodá profesionálně zpracovanou dokumentaci pro tuto evidenci.", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "příloha IV bod 6 — popis změn během životního cyklu",
            },
            {
                "key": "has_ai_bias_check",
                "text": "Testujete své AI systémy na diskriminaci nebo zaujatost (bias)?",
                "type": "yes_no_unknown",
                "help_text": "Příklady ANO:\n1) Kontrolujete, zda AI nábor nezvýhodňuje/neznevýhodňuje kandidáty podle pohlaví nebo věku.\n2) Testujete, zda chatbot odpovídá stejně kvalitně česky i anglicky.\n3) Analyzujete, zda AI scoring nediskriminuje určité skupiny zákazníků.\n\nPříklady NE:\n1) AI běží bez jakékoliv kontroly férovosti.\n2) Nikdy jste netestovali, zda AI výstupy nejsou zaujaté.\n\nTato otázka je relevantní zejména pro firmy s vysoce rizikovými AI systémy (HR, finance, přístup ke službám).",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "bias_check_method", "label": "Jak testujete? (vyberte vše)", "type": "multi_select",
                         "options": ["Manuální kontrola výstupů na vzorku dat", "Automatizované testy férovosti", "Porovnání výstupů pro různé skupiny (pohlaví, věk, etnicita)", "Zpětná vazba od uživatelů / zákazníků", "Externí audit"]},
                        {"key": "bias_check_ok_info", "label": "✅ Výborně! Testování férovosti AI je požadavek čl. 9–10 AI Act. Do dokumentace zaznamenáme váš přístup k testování biasu.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "bias_check_warning", "label": "⚠️ Články 9 a 10 AI Act vyžadují, aby vysoce rizikové AI systémy byly testovány na bias a diskriminaci. I u systémů s nižším rizikem je testování férovosti dobrá praxe. **V rámci Compliance Kitu vám vygenerujeme **Monitoring plán AI**, který zahrnuje sekci testování férovosti (bias testing) — konkrétní postup, jak testovat genderový, etnický a věkový bias ve vašich AI systémech.**", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 9 — systém řízení rizik, čl. 10 — správa dat a tréninkových dat",
            },
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # SEKCE 13: Implementace transparenční stránky
    # ═══════════════════════════════════════════════════════════════
    {
        "id": "implementation",
        "title": "Implementace transparenční stránky",
        "description": "Poslední krok — jak chcete nasadit transparenční stránku na váš web? AI Act (čl. 50) přikazuje informovat uživatele o tom, že interagují s AI. Transparenční stránka je klíčový compliance dokument, který musí být veřejně dostupný na vašem webu.",
        "questions": [
            {
                "key": "transparency_page_implementation",
                "text": "Chcete, abychom transparenční stránku implementovali za vás, nebo si ji nasadíte sami?",
                "type": "single_select",
                "options": [
                    "Chci implementaci od AIshield",
                    "Implementuji si to sám / vlastními silami",
                ],
                "help_text": "Transparenční stránka je HTML stránka, kterou vygenerujeme jako součást Compliance Kitu. Potřebujete ji vložit na svůj web (typicky /ai-transparency nebo /ai-info).",
                "followup": {
                    "condition": "Implementuji si to sám / vlastními silami",
                    "fields": [
                        {"key": "implementation_self_info", "label": "✅ Rozumíme! Veškeré vypracované podklady včetně HTML kódu transparenční stránky vám zašleme e-mailem a poštou. Implementace je jednoduchá — stačí vložit HTML soubor na váš web.", "type": "info"},
                    ]
                },
                "risk_hint": None,
                "ai_act_article": "čl. 50 — transparentnost a informování",
            },
            {
                "key": "aishield_implementation_request",
                "text": "Implementace transparenční stránky službou AIshield",
                "type": "conditional_fields",
                "show_when": "transparency_page_implementation == 'Chci implementaci od AIshield'",
                "fields": [
                    {"key": "aishield_impl_note", "label": "✅ Výborně! Náš technik se vám ozve a domluví si s vámi detaily implementace.\n\n**Mezitím prosím připravte:**\n• Administrátorský účet (nebo návštěvnický s právem editovat) k vašemu webu / CMS\n• Zálohu webu (pro jistotu)\n\nPřístupové údaje si od vás bezpečně vyžádáme po objednávce. Implementace je součástí balíčků **Pro** a **Enterprise**.", "type": "info"},
                ],
                "help_text": "Nainstalujeme transparenční stránku přímo na váš web.",
                "risk_hint": None,
                "ai_act_article": "čl. 50 — transparentnost a informování",
            },
        ],
    },
]

# Pořadí sekcí: od jednoduchých k náročným, zakázané praktiky až ke konci
_SECTION_ORDER = [
    "industry", "internal_ai", "customer_service", "hr", "finance",
    "prohibited_systems", "infrastructure_safety", "data_protection", "ai_literacy",
    "human_oversight", "ai_role", "incident_management", "implementation",
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
    Pokud existují staré odpovědi (re-questionnaire), odešle notifikaci.
    """
    supabase = get_supabase()

    if not submission.answers:
        raise HTTPException(status_code=400, detail="Dotazník je prázdný.")

    # Najít nebo vytvořit anonymního clienta pro tuto firmu
    client_id = await _get_or_create_client(supabase, submission.company_id)

    # Načíst staré odpovědi pro detekci změn (re-questionnaire)
    old_answers_map: dict[str, str] = {}
    is_resubmission = False
    try:
        old_result = supabase.table("questionnaire_responses") \
            .select("question_key, answer") \
            .eq("client_id", client_id) \
            .neq("question_key", "__position__") \
            .execute()
        if old_result.data:
            is_resubmission = True
            old_answers_map = {r["question_key"]: r["answer"] for r in old_result.data}
    except Exception as e:
        logger.warning(f"[Questionnaire] Nepodařilo se načíst staré odpovědi: {e}")

    # Uložit odpovědi — UPSERT (update existující nebo vložit nové)
    # Díky UNIQUE(client_id, question_key) se odpovědi nikdy nezduplikují
    # a při editu jedné otázky zůstanou ostatní odpovědi zachované
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
            supabase.table("questionnaire_responses").upsert(
                row, on_conflict="client_id,question_key"
            ).execute()
            saved_count += 1
        except Exception as e:
            logger.error(f"[Questionnaire] Chyba při ukládání odpovědi {ans.question_key}: {e}")

    logger.info(f"[Questionnaire] Uloženo {saved_count}/{len(submission.answers)} odpovědí pro company {submission.company_id}")

    # Analyzovat odpovědi
    analysis = _analyze_responses(submission.answers)

    # Pokud máme scan_id, propojit s nálezem
    if submission.scan_id:
        analysis["scan_id"] = submission.scan_id

    # ── Re-questionnaire notifikace ──
    # Pokud uživatel změnil odpovědi, pošleme email s přehledem změn
    if is_resubmission and old_answers_map:
        try:
            new_answers_map = {a.question_key: a.answer for a in submission.answers}

            # Sestavit mapu question_key → přesný text otázky
            q_text_map: dict[str, str] = {}
            for s in QUESTIONNAIRE_SECTIONS:
                for q in s["questions"]:
                    q_text_map[q["key"]] = q["text"]

            changed = []
            for key, new_val in new_answers_map.items():
                old_val = old_answers_map.get(key)
                if old_val and old_val != new_val:
                    q_label = q_text_map.get(key, key.replace("_", " "))
                    changed.append({
                        "key": key,
                        "label": q_label,
                        "old": old_val,
                        "new": new_val,
                    })
            added = [k for k in new_answers_map if k not in old_answers_map]
            removed = [k for k in old_answers_map if k not in new_answers_map]

            if changed or added or removed:
                # Načíst kompletní info o firmě
                company_name = submission.company_id[:8]
                company_url = "neuvedeno"
                company_email = "neuvedeno"
                company_phone = "neuvedeno"
                company_ico = "neuvedeno"
                try:
                    comp = supabase.table("companies").select("name, url, email, phone, ico").eq("id", submission.company_id).limit(1).execute()
                    if comp.data:
                        cd = comp.data[0]
                        company_name = cd.get("name") or company_name
                        company_url = cd.get("url") or "neuvedeno"
                        company_email = cd.get("email") or "neuvedeno"
                        company_phone = cd.get("phone") or "neuvedeno"
                        company_ico = cd.get("ico") or "neuvedeno"
                except Exception:
                    pass

                # Doplnit kontakt z dotazníku pokud chybí v companies
                for a in submission.answers:
                    if a.question_key == "company_contact_email" and a.answer and company_email == "neuvedeno":
                        company_email = a.answer
                    if a.question_key == "company_contact_phone" and a.answer and company_phone == "neuvedeno":
                        company_phone = a.answer
                    if a.question_key == "company_ico" and a.answer and company_ico == "neuvedeno":
                        company_ico = a.answer

                # Změněné odpovědi - s přesným zněním otázky
                changes_html = ""
                if changed:
                    changes_html += "<h3>📝 Změněné odpovědi:</h3><table style='border-collapse:collapse; width:100%;'>"
                    changes_html += "<tr style='background:#f0f0f0;'><th style='padding:8px; text-align:left; border:1px solid #ddd;'>Otázka</th><th style='padding:8px; text-align:left; border:1px solid #ddd;'>Předchozí</th><th style='padding:8px; text-align:left; border:1px solid #ddd;'>Nová odpověď</th></tr>"
                    for c in changed:
                        changes_html += f"<tr><td style='padding:8px; border:1px solid #ddd;'>{c['label']}</td><td style='padding:8px; border:1px solid #ddd; color:#c00;'>{c['old']}</td><td style='padding:8px; border:1px solid #ddd; color:#090;'><b>{c['new']}</b></td></tr>"
                    changes_html += "</table>"
                if added:
                    changes_html += f"<p>➕ <b>Nově zodpovězené otázky:</b> {len(added)}</p>"

                # Vyhodnotit jestli změna vyžaduje přegenerování dokumentů
                # Klíčové otázky: vše kromě kontaktních údajů
                contact_keys = {"company_legal_name", "company_ico", "company_contact_email", "company_contact_phone"}
                substantive_changes = [c for c in changed if c["key"] not in contact_keys]
                needs_regen = len(substantive_changes) > 0 or len(added) > 0

                if needs_regen:
                    regen_html = '<div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:12px; margin:12px 0;"><b>⚠️ Vyžaduje nové vyhotovení dokumentů</b><br>Klient změnil odpovědi, které ovlivňují compliance hodnocení. Je třeba přegenerovat dokumenty.</div>'
                else:
                    regen_html = '<div style="background:#d4edda; border:1px solid #28a745; border-radius:8px; padding:12px; margin:12px 0;"><b>✅ Dokumenty zůstávají v platnosti</b><br>Změna se týká pouze kontaktních údajů a nemá vliv na compliance hodnocení.</div>'

                notification_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
                    <h2 style="color:#1a1a2e;">🔔 Změna dotazníku — {company_name}</h2>

                    <table style="width:100%; border-collapse:collapse; margin:16px 0; background:#f8f9fa; border-radius:8px;">
                        <tr><td style="padding:8px 12px; font-weight:bold; width:140px;">Firma / Klient:</td><td style="padding:8px 12px;">{company_name}</td></tr>
                        <tr><td style="padding:8px 12px; font-weight:bold;">IČO:</td><td style="padding:8px 12px;">{company_ico}</td></tr>
                        <tr><td style="padding:8px 12px; font-weight:bold;">Web:</td><td style="padding:8px 12px;"><a href="{company_url}">{company_url}</a></td></tr>
                        <tr><td style="padding:8px 12px; font-weight:bold;">E-mail:</td><td style="padding:8px 12px;"><a href="mailto:{company_email}">{company_email}</a></td></tr>
                        <tr><td style="padding:8px 12px; font-weight:bold;">Telefon:</td><td style="padding:8px 12px;">{company_phone}</td></tr>
                    </table>

                    <p><b>Počet změn:</b> {len(changed)} změněných, {len(added)} nových</p>

                    {changes_html}
                    {regen_html}

                    <hr style="margin:20px 0;">
                    <p><a href="https://aishield.cz/admin" style="display:inline-block; background:#6366f1; color:white; padding:10px 20px; border-radius:6px; text-decoration:none;">📋 Otevřít admin panel</a></p>
                </div>
                """

                from backend.outbound.email_engine import send_email
                await send_email(
                    to="info@desperados-design.cz",
                    subject=f"🔔 Změna dotazníku — {company_name}",
                    html=notification_html,
                )
                logger.info(f"[Questionnaire] Odeslána notifikace o změně dotazníku pro {company_name}")

                # TODO: Automatické přegenerování dokumentů
                # await regenerate_documents(submission.company_id)
        except Exception as e:
            logger.error(f"[Questionnaire] Chyba při odesílání notifikace: {e}")

    return {
        "status": "saved",
        "saved_count": saved_count,
        "analysis": analysis,
        "is_resubmission": is_resubmission,
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

    # Najít company_id přes companies.email (primární cesta)
    company_id = None
    try:
        companies = supabase.table("companies") \
            .select("id") \
            .eq("email", user.email) \
            .limit(1) \
            .execute()
        if companies.data:
            company_id = companies.data[0]["id"]
    except Exception:
        pass

    if not company_id:
        # Fallback: zkusit najít přes clients tabulku (company_id)
        try:
            clients = supabase.table("clients") \
                .select("company_id") \
                .eq("email", user.email) \
                .limit(1) \
                .execute()
            if clients.data:
                company_id = clients.data[0]["company_id"]
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
        .neq("question_key", "__position__") \
        .execute()

    if not result.data:
        return {"is_complete": False, "has_unknowns": False, "total_answers": 0}

    total = len(result.data)
    unknowns = sum(1 for r in result.data if r.get("answer") in ("nevim", "unknown"))
    # Dynamic question count from structure — exclude conditional questions with show_when
    all_question_keys = {
        q["key"] for s in QUESTIONNAIRE_SECTIONS for q in s["questions"]
        if not q.get("show_when")
    }
    required_count = len(all_question_keys)
    # is_complete = všechny otázky zodpovězeny A žádná odpověď není "nevím"
    is_complete = total >= required_count and unknowns == 0

    return {
        "is_complete": is_complete,
        "has_unknowns": unknowns > 0,
        "total_answers": total,
        "unknown_count": unknowns,
    }


# ── Autosave: uloží jednu odpověď v reálném čase ──

class AutosavePayload(BaseModel):
    company_id: str
    question_key: str
    section: str
    answer: str
    details: Optional[dict] = None
    tool_name: Optional[str] = None
    current_question_index: Optional[int] = None
    custom_answer: Optional[str] = None


@router.post("/questionnaire/autosave")
async def autosave_answer(payload: AutosavePayload):
    """Uloží jednu odpověď do DB (upsert) + uloží pozici."""
    supabase = get_supabase()

    client_id = await _get_or_create_client(supabase, payload.company_id)

    # Upsert odpovědi
    details = payload.details or {}
    if payload.custom_answer:
        details["custom_answer"] = payload.custom_answer

    row = {
        "client_id": client_id,
        "section": payload.section,
        "question_key": payload.question_key,
        "answer": payload.answer,
        "details": details if details else None,
        "tool_name": payload.tool_name,
    }
    supabase.table("questionnaire_responses").upsert(
        row, on_conflict="client_id,question_key"
    ).execute()

    # Uloží aktuální pozici jako speciální záznam
    if payload.current_question_index is not None:
        pos_row = {
            "client_id": client_id,
            "section": "__meta__",
            "question_key": "__position__",
            "answer": str(payload.current_question_index),
            "details": None,
            "tool_name": None,
        }
        supabase.table("questionnaire_responses").upsert(
            pos_row, on_conflict="client_id,question_key"
        ).execute()

    logger.info(f"[Autosave] {payload.question_key} = {payload.answer} (pos={payload.current_question_index}) company={payload.company_id}")
    return {"ok": True}


@router.get("/questionnaire/{company_id}/position")
async def get_questionnaire_position(company_id: str):
    """Vrátí uloženou pozici uživatele v dotazníku."""
    supabase = get_supabase()
    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        return {"position": None}

    result = supabase.table("questionnaire_responses") \
        .select("answer") \
        .eq("client_id", client_id) \
        .eq("question_key", "__position__") \
        .limit(1) \
        .execute()

    if result.data:
        try:
            return {"position": int(result.data[0]["answer"])}
        except (ValueError, TypeError):
            pass

    return {"position": None}


class PositionUpdate(BaseModel):
    company_id: str
    position: int


@router.post("/questionnaire/{company_id}/position")
async def save_questionnaire_position(company_id: str, payload: PositionUpdate):
    """Uloží pozici uživatele v dotazníku (volá se při odchodu ze stránky)."""
    supabase = get_supabase()
    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        raise HTTPException(status_code=404, detail="Firma nenalezena")
    pos_row = {
        "client_id": client_id,
        "section": "__meta__",
        "question_key": "__position__",
        "answer": str(payload.position),
        "details": None,
        "tool_name": None,
    }
    supabase.table("questionnaire_responses").upsert(
        pos_row, on_conflict="client_id,question_key"
    ).execute()
    return {"ok": True}


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
        .neq("question_key", "__position__") \
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


@router.get("/questionnaire/{company_id}/progress")
async def get_questionnaire_progress(company_id: str):
    """Vrátí postup vyplnění dotazníku v procentech."""
    supabase = get_supabase()
    total_questions = sum(len(s["questions"]) for s in QUESTIONNAIRE_SECTIONS)

    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        return {
            "company_id": company_id,
            "total_questions": total_questions,
            "answered": 0,
            "unknown_count": 0,
            "percentage": 0,
            "status": "nezahajeno",
        }

    result = supabase.table("questionnaire_responses") \
        .select("question_key, answer") \
        .eq("client_id", client_id) \
        .neq("question_key", "__position__") \
        .execute()

    answered = len(result.data) if result.data else 0
    unknown_count = sum(1 for r in (result.data or []) if r.get("answer") == "unknown")
    pct = round((answered / total_questions) * 100) if total_questions > 0 else 0

    if pct == 0:
        status = "nezahajeno"
    elif pct < 100:
        status = "rozpracovano"
    else:
        status = "dokonceno"

    return {
        "company_id": company_id,
        "total_questions": total_questions,
        "answered": answered,
        "unknown_count": unknown_count,
        "percentage": pct,
        "status": status,
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
            .neq("question_key", "__position__") \
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


# ── Billing prefill z dotazníku ──

BILLING_QUESTION_KEYS = [
    "company_legal_name",
    "company_ico",
    "company_address",
    "company_contact_email",
    "company_phone",
]


@router.get("/questionnaire/billing-prefill")
async def get_billing_prefill(user: AuthUser = Depends(get_current_user)):
    """
    Vrátí fakturační údaje extrahované z dotazníku.
    Používá se při předvyplnění checkout formuláře.
    """
    supabase = get_supabase()

    # Najít firmu podle emailu uživatele
    company_res = supabase.table("companies").select("id").eq(
        "email", user.email
    ).limit(1).execute()

    if not company_res.data:
        return {"prefill": {}}

    company_id = company_res.data[0]["id"]

    # Najít client_id pro tuto firmu
    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        return {"prefill": {}}

    # Načíst relevantní odpovědi z dotazníku
    result = supabase.table("questionnaire_responses") \
        .select("question_key, answer") \
        .eq("client_id", client_id) \
        .in_("question_key", BILLING_QUESTION_KEYS) \
        .execute()

    if not result.data:
        return {"prefill": {}}

    # Sestavit prefill objekt
    answers_map = {r["question_key"]: r["answer"] for r in result.data if r.get("answer")}
    prefill: dict = {}

    if "company_legal_name" in answers_map:
        prefill["company"] = answers_map["company_legal_name"]

    if "company_ico" in answers_map:
        prefill["ico"] = answers_map["company_ico"].strip()

    if "company_contact_email" in answers_map:
        prefill["email"] = answers_map["company_contact_email"]

    if "company_phone" in answers_map:
        prefill["phone"] = answers_map["company_phone"]

    # Adresa — strukturovaný formát: "street || houseNum || city || zip"
    if "company_address" in answers_map:
        addr = answers_map["company_address"]
        parts = addr.split(" || ")
        if len(parts) == 4:
            street_part = parts[0].strip()
            house_part = parts[1].strip()
            # Spojit ulici a číslo popisné
            if house_part:
                prefill["street"] = f"{street_part} {house_part}".strip()
            else:
                prefill["street"] = street_part
            prefill["city"] = parts[2].strip()
            prefill["zip"] = parts[3].strip()
        elif addr.strip():
            # Fallback — nestrukturovaná adresa (starší záznamy)
            prefill["street"] = addr.strip()

    return {"prefill": prefill}


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

    # Doporučení pro odpovědi "Ne" u otázek, kde "Ne" = compliance problém
    # (klient nemá přehled / školení / pravidla / data v EU → musíme to flagovat)
    no_answers = [a for a in answers if a.answer == "no"]
    for ans in no_answers:
        if ans.question_key in _NO_ANSWER_RECOMMENDATIONS:
            q_def = question_map.get(ans.question_key)
            if not q_def:
                continue
            no_rec = _NO_ANSWER_RECOMMENDATIONS[ans.question_key]
            checklist = UNKNOWN_CHECKLISTS.get(ans.question_key, [])
            recommendations.append({
                "question_key": ans.question_key,
                "tool_name": "",
                "risk_level": no_rec["risk_level"],
                "ai_act_article": q_def.get("ai_act_article", ""),
                "recommendation": no_rec["recommendation"],
                "priority": no_rec["priority"],
                "is_no_answer": True,
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
    # Governance
    'has_ai_register': [
        'Koho se zeptat: IT oddělení, compliance officer, vedení firmy.',
        'Příklad: Firma používá ChatGPT, Copilot a AI chatbot na webu, ale nikde nemá centrální seznam těchto nástrojů.',
        'Zjistěte, zda existuje jakýkoliv přehled AI nástrojů — i neformální seznam v Excelu se počítá.',
        'Zkontrolujte IT inventář — zahrnuje i cloudové AI služby?',
    ],
    'has_ai_vendor_contracts': [
        'Koho se zeptat: právní oddělení, IT oddělení, nákup.',
        'Příklad: Firma platí za ChatGPT Plus, ale nemá s OpenAI žádnou firemní smlouvu ani DPA.',
        'Zkontrolujte faktury za AI služby — máte k nim odpovídající smlouvy?',
        'Ověřte, zda smlouvy pokrývají zpracování dat, odpovědnost za chyby AI a podmínky ukončení.',
    ],
    'has_ai_bias_check': [
        'Koho se zeptat: CTO, vývojáři, HR oddělení (pro AI v náboru), compliance officer.',
        'Příklad: AI nástroj pro nábor automaticky vyřazuje kandidáty, ale nikdo netestoval, zda nediskriminuje podle pohlaví nebo věku.',
        'Zkontrolujte, zda AI rozhodnutí nezvýhodňují/neznevýhodňují určité skupiny zákazníků nebo zaměstnanců.',
        'Ověřte, zda máte zpětnou vazbu od uživatelů AI systémů.',
    ],
    # Děti / GPAI
    'uses_ai_for_children': [
        'Koho se zeptat: produktový manažer, vývojáři, marketing.',
        'Příklad: Mobilní aplikace s AI chatbotem, kterou používají děti — např. edukační hra nebo online výuková platforma.',
        'Zkontrolujte, zda vaše AI produkty/služby cílí na osoby mladší 18 let.',
        'Ověřte, zda sbíráte data dětí nebo AI interaguje s dětmi přímo.',
    ],
    'uses_gpai_api': [
        'Koho se zeptat: CTO, vývojáři, produktový tým.',
        'Příklad: Firma volá OpenAI API ze své aplikace a výstupy zobrazuje zákazníkům.',
        'Zkontrolujte zdrojový kód a faktury — platíte za API klíče k LLM službám?',
        'Ověřte, zda výstupy LLM vidí koneční uživatelé vašeho produktu.',
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
    'has_ai_training':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'has_ai_guidelines':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    # Minimální
    'uses_copilot':                 {'severity': 'minimal',  'color': 'gray',   'label': 'Nízká priorita'},
    # Governance
    'has_ai_register':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'has_ai_vendor_contracts':      {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'has_ai_bias_check':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    # Děti / GPAI
    'uses_ai_for_children':         {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_gpai_api':                {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
}


# ── Odpovědi "Ne" které jsou compliance problém ──
# Tyto otázky: pokud klient odpoví "Ne", znamená to nesplnění povinnosti
# nebo nemožnost dodat compliance dokumentaci. Generujeme doporučení.

_NO_ANSWER_RECOMMENDATIONS: dict[str, dict] = {
    'has_ai_training': {
        'risk_level': 'limited',
        'priority': 'vysoká',
        'recommendation': (
            'Vaši zaměstnanci nebyli proškoleni o bezpečném používání AI. '
            'Článek 4 AI Act vyžaduje „dostatečnou úroveň AI gramotnosti" '
            'a tato povinnost platí již od 2. února 2025. '
            'Zajistěte školení co nejdříve — AIshield.cz dodává kompletní '
            'školící prezentaci (PowerPoint) a profesionálně zpracovanou prezenční listinu.'
        ),
    },
    'has_ai_guidelines': {
        'risk_level': 'limited',
        'priority': 'střední',
        'recommendation': (
            'Nemáte ve firmě pravidla pro používání AI. '
            'Bez interní směrnice zaměstnanci nevědí, jaká data smí do AI vkládat, '
            'zda mohou AI výstupy publikovat, ani kdo je zodpovědný za dodržování. '
            'V rámci služby vám dodáme profesionálně zpracovanou směrnici „Pravidla pro AI ve firmě", '
            'která pokrývá obecné zásady a je použitelná pro jakoukoliv firmu. '
            'Pozor: konkrétní pravidla šitá na míru vašim procesům a AI nástrojům '
            'si musíte vytvořit interně — dokumentace vám k tomu poslouží jako základ.'
        ),
    },
    'ai_data_stored_eu': {
        'risk_level': 'limited',
        'priority': 'střední',
        'recommendation': (
            'Data vašich AI systémů nejsou uložena v EU. '
            'Většina velkých AI poskytovatelů (OpenAI, Google, Anthropic) '
            'ukládá data na serverech v USA. To samo o sobě není zakázané, '
            'ale musíte mít s poskytovatelem podepsanou smlouvu o zpracování '
            'osobních údajů, která zaručuje ochranu dat i mimo EU. '
            'Pokud používáte ChatGPT, Gemini nebo Claude, '
            'ověřte si v nastavení, zda máte zapnutou firemní verzi '
            '(Team/Business) — ta obvykle zajišťuje vyšší úroveň ochrany dat.'
        ),
    },
    'has_ai_register': {
        'risk_level': 'limited',
        'priority': 'vysoká',
        'recommendation': (
            'Nemáte interní registr AI systémů. '
            'Článek 26 AI Act vyžaduje, aby zavádějící měli přehled '
            'o všech AI systémech, které používají. '
            'Bez registru nemůžete prokázat soulad s nařízením. '
            'AIshield vám dodá profesionálně zpracovaný registr AI systémů — '
            'jednoduchou tabulku, kterou si snadno vyplníte.'
        ),
    },
    'has_ai_vendor_contracts': {
        'risk_level': 'limited',
        'priority': 'střední',
        'recommendation': (
            'Nemáte smlouvy s dodavateli AI systémů. '
            'GDPR čl. 28 vyžaduje smlouvu se zpracovatelem osobních údajů '
            'a AI Act čl. 25-26 definuje povinnosti v hodnotovém řetězci. '
            'Bez DPA riskujete pokutu za porušení GDPR. '
            'AIshield vám dodá kontrolní seznam bodů, '
            'které by smlouva s AI dodavatelem měla obsahovat.'
        ),
    },
    'has_ai_bias_check': {
        'risk_level': 'limited',
        'priority': 'střední',
        'recommendation': (
            'Netestujete AI systémy na diskriminaci nebo bias. '
            'Články 9 a 10 AI Act vyžadují testování férovosti '
            'zejména u vysoce rizikových AI systémů (HR, finance, přístup ke službám). '
            'I u systémů s nižším rizikem je testování férovosti dobrá praxe. '
            'AIshield vám dodá jednoduchou metodiku pro základní testování biasu.'
        ),
    },
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
        "uses_ai_critical_infra": f"VYSOCE RIZIKOVÝ systém! AI v kritické infrastruktuře (Příloha III bod 2) — registrace u NÁRODNÍHO orgánu (čl. 49 odst. 4), ne ve veřejné EU databázi. Povinnosti: systém řízení rizik (čl. 9), technická dokumentace (Příloha IV), posouzení shody (čl. 43 — interní postačuje), CE označení (čl. 48), post-market monitoring (čl. 72). V ČR kontaktujte NÚKIB. Deadline: 2. 8. 2026. Doporučujeme konzultaci s právníkem — AIshield připraví podklady.",
        "uses_ai_safety_component": f"VYSOCE RIZIKOVÝ systém! AI jako bezpečnostní komponenta (čl. 6 odst. 1) — plná účinnost od 2. 8. 2027. Povinnosti: posouzení shody (Příloha VI — interní), technická dokumentace (Příloha IV), CE označení (čl. 48), registrace v EU databázi (čl. 49), prohlášení o shodě (čl. 47). Notifikovaný subjekt NENÍ nutný (kromě biometrie). AIshield připraví pre-filled dokumentaci.",
        # Ochrana dat
        "ai_processes_personal_data": f"Proveďte DPIA dle GDPR. Zajistěte právní základ pro zpracování a minimalizaci dat v AI systémech.",
        "ai_data_stored_eu": "Ověřte, kde jsou data AI systémů fyzicky uložena. Pro přenos mimo EU zajistěte adekvátní záruky (SCC, adequacy decision).",
        # Provider / deployer
        "develops_own_ai": "Jako vývojář (provider) AI systémů máte povinnosti dle čl. 16 AI Act — dokumentace, posouzení shody, registrace. Identifikujte risk kategorii každého vašeho AI produktu.",
        # AI gramotnost
        "has_ai_training": "Zajistěte proškolení zaměstnanců o bezpečném používání AI nástrojů. Článek 4 AI Act vyžaduje ‚dostatečnou úroveň AI gramotnosti'.",
        "has_ai_guidelines": "Vytvořte interní pravidla pro používání AI — co se smí sdílet, jaká data nesmí do AI nástrojů, a kdo je zodpovědný za dodržování.",
        # Governance
        "has_ai_register": "Vytvořte interní registr všech AI systémů — čl. 26 AI Act vyžaduje přehled o nasazených AI systémech.",
        "has_ai_vendor_contracts": "Uzavřete smlouvy (DPA, SLA) s dodavateli AI systémů — GDPR čl. 28 vyžaduje smlouvu se zpracovatelem dat.",
        "has_ai_bias_check": "Testujte AI systémy na férovost a diskriminaci — čl. 9-10 AI Act vyžadují řízení rizik včetně biasu.",
        # Děti / GPAI
        "uses_ai_for_children": "AI interagující s dětmi je vysoce rizikové dle Přílohy III AI Act. Proveďte posouzení shody a zajistěte zvýšenou ochranu nezletilých.",
        "uses_gpai_api": "Integrujete LLM API do zákaznických produktů — od srpna 2025 platí GPAI pravidla (čl. 51-54). Zajistěte transparentnost a dokumentaci.",
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
