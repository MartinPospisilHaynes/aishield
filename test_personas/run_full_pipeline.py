#!/usr/bin/env python3
"""
AIshield.cz — Full Pipeline Test with 10 Personas
===================================================
Projde celou zákaznickou cestu pro 10 různých person:
  1. Quick scan webu
  2. Vyplnění dotazníku (osobité odpovědi per persona)
  3. Objednávka balíčku (basic / pro / enterprise)
  4. Deep scan (zkrácený režim — 6 kol × 5 min)
  5. Generování dokumentů

Použití:  python run_full_pipeline.py [--skip-scan] [--skip-deep]
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import requests
from supabase import create_client

# ── Konfigurace ──
API_BASE = "https://api.aishield.cz/api"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://rsxwqcrkttlfnqbjgpgc.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Pro přímé DB operace (orders) — načteme z backendu
SCAN_POLL_INTERVAL = 10   # seconds
SCAN_POLL_TIMEOUT = 300  # seconds (5 min — scany trvají déle)

# ── 10 Person ──
PERSONAS = [
    # ── Persona 01: Kadeřnice OSVČ (basic) ──
    {
        "name": "Martina Nováková — Kadeřnictví",
        "plan": "basic",
        "test_url": "https://www.seznam.cz",  # placeholder — real URL for scannable site
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "Martina Nováková — Kadeřnictví Martina"},
            {"question_key": "company_ico", "section": "industry", "answer": "12345601"},
            {"question_key": "company_address", "section": "industry", "answer": "Lipová 12, 370 01 České Budějovice"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "martina@kadrnictvi-martina.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Kadeřnictví / Kosmetika"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Nemám e-shop"},
            {"question_key": "company_size", "section": "industry", "answer": "Jen já (OSVČ)"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "Do 2 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT"], "chatgpt_purpose": ["Psaní textů"], "chatgpt_data_type": ["Pouze veřejná data"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "yes",
             "details": {"content_tool_name": ["ChatGPT / GPT-4o"], "content_published": ["Web / sociální sítě"]}},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "no"},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "unknown"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "no"},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "no"},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "no"},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Implementujeme sami (vlastní IT / technik)"},
        ],
    },
    # ── Persona 02: AI Konglomerát (enterprise) ──
    {
        "name": "NeuralForge Technologies s.r.o.",
        "plan": "enterprise",
        "test_url": "https://www.novinky.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "NeuralForge Technologies s.r.o."},
            {"question_key": "company_ico", "section": "industry", "answer": "98765402"},
            {"question_key": "company_address", "section": "industry", "answer": "Technická 8, 160 00 Praha 6"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "cto@neuralforge.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "IT / Technologie"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Vlastní řešení (custom)"},
            {"question_key": "company_size", "section": "industry", "answer": "250+ zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "250 mil. – 1 mld. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "yes",
             "details": {"ai_role": ["Vyvíjíme AI (provider)", "Nasazujeme AI od jiných (deployer)"]}},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT", "Claude", "Gemini"], "chatgpt_purpose": ["Programování", "Analýza dat", "Psaní textů"], "chatgpt_data_type": ["Interní dokumenty", "Zdrojový kód / obchodní tajemství"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "yes",
             "details": {"copilot_tool_name": ["GitHub Copilot", "Cursor"], "copilot_code_type": ["Backend/API", "Data/ML", "Webové aplikace"]}},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "yes",
             "details": {"content_tool_name": ["ChatGPT / GPT-4o", "Midjourney", "Gemini (Google)"], "content_published": ["Web / sociální sítě", "Reklamní kampaně"]}},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "yes",
             "details": {"deepfake_tool_name": ["ChatGPT (Sora)", "Gemini / VEO3 (Google)", "HeyGen"]}},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "yes",
             "details": {"chatbot_tool_name": ["ChatGPT API", "Intercom"]}},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "yes",
             "details": {"email_tool": ["ChatGPT", "Intercom"]}},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "yes",
             "details": {"decision_scope": ["Schvalování žádostí", "Slevy / ceny"], "decision_human_review": "Ano"}},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "yes",
             "details": {"recruitment_tool": ["ChatGPT", "LinkedIn Recruiter"], "recruitment_autonomous": "Ne, pouze doporučuje"}},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "yes",
             "details": {"monitoring_type": ["Měření produktivity", "Analýza emailů"]}},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "yes",
             "details": {"accounting_tool": ["Pohoda", "ChatGPT"], "accounting_decisions": "Ne, pouze asistuje"}},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "yes",
             "details": {"biometric_tool_name": ["Přístupový systém"], "biometric_purpose": ["Kontrola přístupu"]}},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Finanční údaje", "Fotografie / video"], "dpia_done": "Ano"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "no"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "yes",
             "details": {"vendor_contract_scope": ["DPA (zpracování osobních údajů)", "SLA (dostupnost a kvalita služby)", "Odpovědnost za škody způsobené AI"]}},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "yes",
             "details": {"training_attendance": "Ano", "training_audience_size": "100+ osob", "training_audience_level": "Mix — různé úrovně"}},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "yes",
             "details": {"guidelines_scope": ["Které AI nástroje smí zaměstnanci používat", "Jaká data se smí do AI vkládat", "Kdo schvaluje nové AI nástroje", "Postup při AI incidentu"], "guidelines_format": "Písemná směrnice / interní předpis"}},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "yes",
             "details": {"oversight_role": "Tým / komise AI governance", "oversight_person_name": "Ing. Tomáš Říha", "oversight_person_email": "riha@neuralforge.cz", "oversight_scope": ["Vše — zastřešuje kompletní AI governance"]}},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Vždy — AI jen doporučuje, člověk rozhoduje"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "yes",
             "details": {"logging_method": ["Logy v aplikaci (automatické)", "Export do SIEM / centrálního logu"], "logging_retention": "1–3 roky"}},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "yes",
             "details": {"register_contents": ["Název AI systému", "Dodavatel / poskytovatel", "Účel použití", "Kategorie rizika dle AI Act", "Odpovědná osoba", "Datum nasazení", "Typ zpracovávaných dat"]}},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "yes"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "yes",
             "details": {"gpai_provider": ["OpenAI (GPT-4/4o)", "Anthropic (Claude)", "Google (Gemini)"], "gpai_customer_facing": "Ano, zákazníci vidí AI výstupy přímo"}},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "yes",
             "details": {"incident_plan_scope": ["Postup při chybné AI odpovědi zákazníkovi", "Eskalační proces (kdo rozhoduje o dalších krocích)", "Okamžité odstavení AI systému", "Hlášení incidentu dozorové autoritě"]}},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "yes",
             "details": {"monitoring_frequency": "Denně"}},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "yes",
             "details": {"changes_tracking_method": ["Verze v Git / repozitáři", "Ticketovací systém (Jira)"]}},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "yes",
             "details": {"bias_check_method": ["Automatizované testy férovosti", "Porovnání výstupů pro různé skupiny (pohlaví, věk, etnicita)"]}},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Implementujeme sami (vlastní IT / technik)"},
        ],
    },
    # ── Persona 03: Účetní kancelář (enterprise) ──
    {
        "name": "EkoÚčto s.r.o.",
        "plan": "enterprise",
        "test_url": "https://www.idnes.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "EkoÚčto s.r.o."},
            {"question_key": "company_ico", "section": "industry", "answer": "56789003"},
            {"question_key": "company_address", "section": "industry", "answer": "Žižkova 5, 586 01 Jihlava"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "jana@ekoúčto.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Účetnictví / Finance"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Nemám e-shop"},
            {"question_key": "company_size", "section": "industry", "answer": "2–9 zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "2–10 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT"], "chatgpt_purpose": ["Analýza dat", "Psaní textů"], "chatgpt_data_type": ["Pouze veřejná data"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "yes",
             "details": {"accounting_tool": ["Pohoda", "ChatGPT"], "accounting_decisions": "Ne, pouze asistuje"}},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Rodná čísla / OP", "Finanční údaje"], "dpia_done": "Ne"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "unknown"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "no"},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Vždy — AI jen doporučuje, člověk rozhoduje"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "no"},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Náš webdesignér / externí dodavatel"},
            {"question_key": "implementation_contact", "section": "implementation", "answer": "yes",
             "details": {"implementor_name": "Jan Procházka", "implementor_email": "jan@webdesign-studio.cz", "implementor_phone": "+420 601 234 567"}},
        ],
    },
    # ── Persona 04: E-shop střední (pro) ──
    {
        "name": "BioKrása.cz s.r.o.",
        "plan": "pro",
        "test_url": "https://www.alza.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "BioKrása.cz s.r.o."},
            {"question_key": "company_ico", "section": "industry", "answer": "78901204"},
            {"question_key": "company_address", "section": "industry", "answer": "Na Příkopě 22, 110 00 Praha 1"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "petr@biokrasa.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "E-shop / Online obchod"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Shoptet"},
            {"question_key": "company_size", "section": "industry", "answer": "10–49 zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "10–50 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT"], "chatgpt_purpose": ["Psaní textů", "Zákaznický servis"], "chatgpt_data_type": ["Pouze veřejná data"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "yes",
             "details": {"content_tool_name": ["ChatGPT / GPT-4o", "Canva AI"], "content_published": ["Web / sociální sítě", "Reklamní kampaně"]}},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "yes",
             "details": {"chatbot_tool_name": ["Tidio"]}},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "yes",
             "details": {"email_tool": ["ChatGPT"]}},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "yes",
             "details": {"pricing_tool": ["ChatGPT"], "pricing_basis": ["Poptávka", "Čas / sezóna"]}},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Finanční údaje"], "dpia_done": "Ne"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "unknown"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "no"},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Při reklamacích a stížnostech"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "no"},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Chci, aby to udělal AIshield za mě (od balíčku Pro)"},
            {"question_key": "aishield_implementation_request", "section": "implementation", "answer": "yes",
             "details": {"implementation_web_url": "https://www.biokrasa.cz", "implementation_cms_access": "Ano, mám přístup"}},
        ],
    },
    # ── Persona 05: Zdravotnická klinika (enterprise) ──
    {
        "name": "MediCare Plus s.r.o.",
        "plan": "enterprise",
        "test_url": "https://www.csfd.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "MediCare Plus s.r.o."},
            {"question_key": "company_ico", "section": "industry", "answer": "45678905"},
            {"question_key": "company_address", "section": "industry", "answer": "Pekařská 55, 602 00 Brno"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "svarcova@medicareplus.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Zdravotnictví"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Vlastní řešení (custom)"},
            {"question_key": "company_size", "section": "industry", "answer": "10–49 zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "10–50 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT"], "chatgpt_purpose": ["Překlady", "Analýza dat"], "chatgpt_data_type": ["Pouze veřejná data"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "yes",
             "details": {"chatbot_tool_name": ["ChatGPT API"]}},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "yes",
             "details": {"decision_scope": ["Schvalování žádostí"], "decision_human_review": "Ano"}},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "yes",
             "details": {"safety_product": ["Zdravotnický přístroj"], "safety_ce_mark": "Ne"}},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Zdravotní údaje", "Rodná čísla / OP"], "dpia_done": "Ne"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "yes"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "yes",
             "details": {"vendor_contract_scope": ["DPA (zpracování osobních údajů)"]}},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Vždy — AI jen doporučuje, člověk rozhoduje"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "yes",
             "details": {"gpai_provider": ["OpenAI (GPT-4/4o)"], "gpai_customer_facing": "Částečně — AI navrhuje, člověk kontroluje"}},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "yes",
             "details": {"monitoring_frequency": "Denně"}},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Chci, aby to udělal AIshield za mě (od balíčku Pro)"},
            {"question_key": "aishield_implementation_request", "section": "implementation", "answer": "yes",
             "details": {"implementation_web_url": "https://www.medicareplus.cz", "implementation_cms_access": "Ne, přístup má někdo jiný"}},
        ],
    },
    # ── Persona 06: Advokátní kancelář (pro) ──
    {
        "name": "AK Novotný & Partners s.r.o.",
        "plan": "pro",
        "test_url": "https://www.heureka.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "AK Novotný & Partners s.r.o."},
            {"question_key": "company_ico", "section": "industry", "answer": "12345606"},
            {"question_key": "company_address", "section": "industry", "answer": "Revoluční 3, 110 00 Praha 1"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "novotny@aknovotny.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Právní služby"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "WooCommerce (WordPress)"},
            {"question_key": "company_size", "section": "industry", "answer": "10–49 zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "10–50 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT", "Claude"], "chatgpt_purpose": ["Analýza dat", "Psaní textů"], "chatgpt_data_type": ["Pouze veřejná data", "Interní dokumenty"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "yes",
             "details": {"copilot_tool_name": ["GitHub Copilot"], "copilot_code_type": ["Automatizace"]}},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "yes",
             "details": {"decision_scope": ["Schvalování žádostí"], "decision_human_review": "Ano"}},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "yes",
             "details": {"accounting_tool": ["Fakturoid"], "accounting_decisions": "Ne, pouze asistuje"}},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Rodná čísla / OP", "Finanční údaje"], "dpia_done": "Ne"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "yes"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "yes",
             "details": {"vendor_contract_scope": ["DPA (zpracování osobních údajů)", "Podmínky ukončení spolupráce"]}},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "yes",
             "details": {"guidelines_scope": ["Jaká data se smí do AI vkládat", "Ochrana osobních údajů při práci s AI"], "guidelines_format": "Písemná směrnice / interní předpis"}},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Vždy — AI jen doporučuje, člověk rozhoduje"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "yes",
             "details": {"monitoring_frequency": "Denně"}},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Náš webdesignér / externí dodavatel"},
            {"question_key": "implementation_contact", "section": "implementation", "answer": "yes",
             "details": {"implementor_name": "Petr Štefan", "implementor_email": "petr@webfix.cz", "implementor_phone": "+420 775 333 444"}},
        ],
    },
    # ── Persona 07: Restaurace OSVČ (basic) ──
    {
        "name": "U Staré Lípy — Jaroslav Kučera",
        "plan": "basic",
        "test_url": "https://www.czc.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "Jaroslav Kučera — U Staré Lípy"},
            {"question_key": "company_ico", "section": "industry", "answer": "98765407"},
            {"question_key": "company_address", "section": "industry", "answer": "Masarykova 18, 370 01 České Budějovice"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "info@ustarelipy.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Restaurace / Gastronomie"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Nemám e-shop"},
            {"question_key": "company_size", "section": "industry", "answer": "2–9 zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "2–10 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "no"},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "unknown"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "no"},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "no"},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "no"},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Implementujeme sami (vlastní IT / technik)"},
        ],
    },
    # ── Persona 08: Realitní kancelář (pro) ──
    {
        "name": "METRO Reality a.s.",
        "plan": "pro",
        "test_url": "https://www.lupa.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "METRO Reality a.s."},
            {"question_key": "company_ico", "section": "industry", "answer": "56789008"},
            {"question_key": "company_address", "section": "industry", "answer": "Václavské náměstí 56, 110 00 Praha 1"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "pospisil@metroreality.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Nemovitosti / Reality"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Vlastní řešení (custom)"},
            {"question_key": "company_size", "section": "industry", "answer": "50–249 zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "50–250 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "yes",
             "details": {"ai_role": ["Nasazujeme AI od jiných (deployer)"]}},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT"], "chatgpt_purpose": ["Psaní textů", "Zákaznický servis"], "chatgpt_data_type": ["Pouze veřejná data", "Interní dokumenty"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "yes",
             "details": {"content_tool_name": ["ChatGPT / GPT-4o", "Midjourney"], "content_published": ["Web / sociální sítě"]}},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "yes",
             "details": {"chatbot_tool_name": ["Intercom"]}},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "yes",
             "details": {"email_tool": ["ChatGPT"]}},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "yes",
             "details": {"decision_scope": ["Schvalování žádostí", "Slevy / ceny"], "decision_human_review": "Ano"}},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "yes",
             "details": {"recruitment_tool": ["ChatGPT"], "recruitment_autonomous": "Ne, pouze doporučuje"}},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "yes",
             "details": {"accounting_tool": ["Fakturoid"], "accounting_decisions": "Ne, pouze asistuje"}},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Finanční údaje", "Fotografie / video"], "dpia_done": "Ne"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "yes"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "yes",
             "details": {"vendor_contract_scope": ["DPA (zpracování osobních údajů)", "SLA (dostupnost a kvalita služby)"]}},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "yes",
             "details": {"training_attendance": "Ano", "training_audience_size": "21–50 osob", "training_audience_level": "Netechničtí (administrativa, obchod, marketing)"}},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "yes",
             "details": {"guidelines_scope": ["Jaká data se smí do AI vkládat", "Pravidla pro AI generovaný obsah"], "guidelines_format": "Písemná směrnice / interní předpis"}},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Vždy — AI jen doporučuje, člověk rozhoduje"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "yes",
             "details": {"monitoring_frequency": "Týdně"}},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Náš webdesignér / externí dodavatel"},
            {"question_key": "implementation_contact", "section": "implementation", "answer": "yes",
             "details": {"implementor_name": "Martin Dvořák", "implementor_email": "dvorak@webstudio.cz", "implementor_phone": "+420 777 888 999"}},
        ],
    },
    # ── Persona 09: Výrobní podnik Automotive (enterprise) ──
    {
        "name": "CzechParts Manufacturing a.s.",
        "plan": "enterprise",
        "test_url": "https://www.root.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "CzechParts Manufacturing a.s."},
            {"question_key": "company_ico", "section": "industry", "answer": "34567809"},
            {"question_key": "company_address", "section": "industry", "answer": "Průmyslová 1, 293 01 Mladá Boleslav"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "cerny@czechparts.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Výroba / Průmysl"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Vlastní řešení (custom)"},
            {"question_key": "company_size", "section": "industry", "answer": "250+ zaměstnanců"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "250 mil. – 1 mld. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "yes",
             "details": {"ai_role": ["Vyvíjíme AI (provider)", "Nasazujeme AI od jiných (deployer)"]}},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes",
             "details": {"chatgpt_tool_name": ["ChatGPT"], "chatgpt_purpose": ["Překlady", "Psaní textů"], "chatgpt_data_type": ["Pouze veřejná data"]}},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "yes",
             "details": {"copilot_tool_name": ["GitHub Copilot", "ChatGPT"], "copilot_code_type": ["Data/ML", "Automatizace"]}},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "yes",
             "details": {"decision_scope": ["Schvalování žádostí"], "decision_human_review": "Ano"}},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "yes",
             "details": {"recruitment_tool": ["ChatGPT"], "recruitment_autonomous": "Ne, pouze doporučuje"}},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "yes",
             "details": {"monitoring_type": ["Kamerový dohled s AI", "GPS sledování"]}},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "yes",
             "details": {"accounting_tool": ["Helios"], "accounting_decisions": "Ne, pouze asistuje"}},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "yes",
             "details": {"infra_tool_name": ["Siemens MindSphere"], "infra_sector": ["Doprava"]}},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "yes",
             "details": {"safety_product": ["Průmyslový stroj", "Automobil / dopravní prostředek"], "safety_ce_mark": "Ano"}},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes",
             "details": {"personal_data_types": ["Jména a kontakty", "Fotografie / video", "Lokační data"], "dpia_done": "Ano"}},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "yes"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "yes",
             "details": {"vendor_contract_scope": ["DPA (zpracování osobních údajů)", "SLA (dostupnost a kvalita služby)", "Odpovědnost za škody způsobené AI", "Audit / kontrola dodavatele"]}},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "yes",
             "details": {"training_attendance": "Ano", "training_audience_size": "100+ osob", "training_audience_level": "Mix — různé úrovně"}},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "yes",
             "details": {"guidelines_scope": ["Které AI nástroje smí zaměstnanci používat", "Jaká data se smí do AI vkládat", "Kdo schvaluje nové AI nástroje", "Postup při AI incidentu"], "guidelines_format": "Písemná směrnice / interní předpis"}},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "yes",
             "details": {"oversight_role": "IT manažer / vedoucí IT", "oversight_person_name": "Ing. Radek Černý", "oversight_person_email": "cerny@czechparts.cz", "oversight_scope": ["Vše — zastřešuje kompletní AI governance"]}},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes",
             "details": {"override_scope": ["Vždy — AI jen doporučuje, člověk rozhoduje"]}},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "yes",
             "details": {"logging_method": ["Logy v aplikaci (automatické)"], "logging_retention": "1–3 roky"}},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "yes",
             "details": {"register_contents": ["Název AI systému", "Dodavatel / poskytovatel", "Účel použití", "Kategorie rizika dle AI Act", "Odpovědná osoba", "Datum nasazení"]}},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "yes",
             "details": {"incident_plan_scope": ["Postup při chybné AI odpovědi zákazníkovi", "Eskalační proces (kdo rozhoduje o dalších krocích)", "Okamžité odstavení AI systému"]}},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "yes",
             "details": {"monitoring_frequency": "Denně"}},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "yes",
             "details": {"changes_tracking_method": ["Verze v Git / repozitáři", "Changelog v dokumentaci"]}},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "yes",
             "details": {"bias_check_method": ["Manuální kontrola výstupů na vzorku dat"]}},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Implementujeme sami (vlastní IT / technik)"},
        ],
    },
    # ── Persona 10: Zemědělec OSVČ (basic) ──
    {
        "name": "František Malý — Farma Zelený Kopec",
        "plan": "basic",
        "test_url": "https://www.datart.cz",
        "answers": [
            {"question_key": "company_legal_name", "section": "industry", "answer": "František Malý — Farma Zelený Kopec"},
            {"question_key": "company_ico", "section": "industry", "answer": "11223310"},
            {"question_key": "company_address", "section": "industry", "answer": "Zelený Kopec 1, 393 01 Pelhřimov"},
            {"question_key": "company_contact_email", "section": "industry", "answer": "frantafarmar@email.cz"},
            {"question_key": "company_industry", "section": "industry", "answer": "Zemědělství"},
            {"question_key": "eshop_platform", "section": "industry", "answer": "Nemám e-shop"},
            {"question_key": "company_size", "section": "industry", "answer": "Jen já (OSVČ)"},
            {"question_key": "company_annual_revenue", "section": "industry", "answer": "2–10 mil. Kč"},
            {"question_key": "develops_own_ai", "section": "industry", "answer": "no"},
            {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_copilot", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},
            {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},
            {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
            {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},
            {"question_key": "uses_ai_accounting", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
            {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},
            {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},
            {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},
            {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "no"},
            {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "unknown"},
            {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "no"},
            {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},
            {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "no"},
            {"question_key": "can_override_ai", "section": "human_oversight", "answer": "no"},
            {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "no"},
            {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},
            {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
            {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "no"},
            {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
            {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "no"},
            {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
            {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
            {"question_key": "transparency_page_implementation", "section": "implementation", "answer": "Implementujeme sami (vlastní IT / technik)"},
        ],
    },
]

PLAN_PRICES = {
    "basic": 4999,
    "pro": 14999,
    "enterprise": 39999,
}


# ═══════════════════════════════════════════════════════════════
# Míra zmatenosti (Confusion Metric)
# ═══════════════════════════════════════════════════════════════
# Pro každou personu určíme, které otázky jsou z jejího hlediska
# irelevantní / matoucí.  Skóre = irelevantní / celkem × 100 %.
#
# Pravidla:
#   1) OSVČ / 1 osoba → HR otázky jsou zbytečné
#   2) Nepoužívá žádné AI → governance/dohled/registr/incident = matoucí
#   3) Není finanční inst. → credit scoring, pojišťovnictví
#   4) Není výroba / automotive → safety component, critical infra
#   5) Není tech firma → copilot, GPAI API, AI vývoj
#   6) Otázky typu "social scoring", "subliminal manipulation",
#      "realtime biometric" jsou matoucí pro >80 % malých firem
# ═══════════════════════════════════════════════════════════════

# Otázky, které jsou VŽDY relevantní pro KAŽDÉHO (identifikace + základní AI)
ALWAYS_RELEVANT = {
    "company_legal_name", "company_ico", "company_address",
    "company_contact_email", "company_industry", "company_size",
    "company_annual_revenue", "develops_own_ai",
    "uses_chatgpt",  # Každý by měl vědět, jestli GPT používá
}

# HR otázky — irelevantní pro OSVČ / 1 osobu
HR_QUESTIONS = {
    "uses_ai_recruitment", "uses_ai_employee_monitoring", "uses_emotion_recognition",
}

# Finance / credit scoring — relevantní jen pro finance, banky, pojišťovny
FINANCE_SPECIALIST_QUESTIONS = {
    "uses_ai_creditscoring", "uses_ai_insurance",
}

# Kritická infrastruktura / safety — relevantní jen pro výrobu, energetiku, dopravu
CRITICAL_INFRA_QUESTIONS = {
    "uses_ai_critical_infra", "uses_ai_safety_component",
}

# Zakázané systémy — matoucí terminologie pro malé / ne-tech firmy
PROHIBITED_SYSTEM_QUESTIONS = {
    "uses_social_scoring", "uses_subliminal_manipulation", "uses_realtime_biometric",
}

# Pokročilý AI governance — irelevantní když firma nepoužívá žádné AI
AI_GOVERNANCE_QUESTIONS = {
    "has_ai_training", "has_ai_guidelines", "has_oversight_person",
    "can_override_ai", "ai_decision_logging", "has_ai_register",
    "modifies_ai_purpose", "uses_gpai_api",
    "has_incident_plan", "monitors_ai_outputs",
    "tracks_ai_changes", "has_ai_bias_check",
}

# Technické otázky — matoucí pro ne-tech firmy
TECH_QUESTIONS = {
    "uses_copilot", "uses_deepfake", "uses_gpai_api", "modifies_ai_purpose",
}

# Data protection questions — partially confusing if no AI used
DATA_QUESTIONS = {
    "ai_processes_personal_data", "ai_data_stored_eu", "has_ai_vendor_contracts",
}


def compute_confusion(persona: dict) -> dict:
    """
    Spočítá míru zmatenosti (confusion) pro danou personu.
    Vrací dict:
      - total_questions: celkový počet otázek
      - irrelevant_questions: list irelevantních otázek (question_key + důvod)
      - confusion_pct: procento zmatenosti
      - confusion_label: "nízká" / "střední" / "vysoká"
    """
    answers = persona["answers"]
    total = len(answers)

    # Parse persona characteristics
    industry = ""
    size = ""
    uses_any_ai = False

    for a in answers:
        if a["question_key"] == "company_industry":
            industry = a["answer"].lower()
        elif a["question_key"] == "company_size":
            size = a["answer"].lower()
        elif a["question_key"] == "develops_own_ai" and a["answer"] == "yes":
            uses_any_ai = True

    # Check if persona uses ANY AI tool (answer != "no" for any AI usage question)
    ai_usage_keys = {
        "uses_chatgpt", "uses_copilot", "uses_ai_content", "uses_deepfake",
        "uses_ai_chatbot", "uses_ai_email_auto", "uses_ai_decision",
        "uses_dynamic_pricing", "uses_ai_recruitment", "uses_ai_employee_monitoring",
        "uses_emotion_recognition", "uses_ai_accounting", "uses_ai_creditscoring",
        "uses_ai_insurance",
    }
    for a in answers:
        if a["question_key"] in ai_usage_keys and a["answer"] == "yes":
            uses_any_ai = True
            break

    is_solo = "osvč" in size or "jen já" in size
    is_small = is_solo or "2–9" in size
    is_tech = any(kw in industry for kw in ["it", "technolog", "software"])
    is_finance = any(kw in industry for kw in ["účet", "finan", "bank", "pojišt"])
    is_manufacturing = any(kw in industry for kw in ["výrob", "průmysl", "automotive", "stroj"])
    is_health = "zdravot" in industry

    irrelevant = []

    for a in answers:
        qk = a["question_key"]

        # Skip always-relevant questions
        if qk in ALWAYS_RELEVANT:
            continue

        # Rule 1: OSVČ → HR questions irrelevant
        if is_solo and qk in HR_QUESTIONS:
            irrelevant.append({
                "question_key": qk,
                "reason": "OSVČ bez zaměstnanců — HR/monitoring nepotřebuje",
            })
            continue

        # Rule 2: No AI used → governance/oversight/incident irrelevant
        if not uses_any_ai and qk in AI_GOVERNANCE_QUESTIONS:
            irrelevant.append({
                "question_key": qk,
                "reason": "Nepoužívá žádné AI — governance otázky bez kontextu",
            })
            continue

        # Rule 3: Not finance → credit scoring / insurance AI irrelevant
        if not is_finance and qk in FINANCE_SPECIALIST_QUESTIONS:
            irrelevant.append({
                "question_key": qk,
                "reason": f"Obor '{industry}' — credit scoring/pojišťovnictví AI irelevantní",
            })
            continue

        # Rule 4: Not manufacturing/energy/transport → critical infra irrelevant
        if not is_manufacturing and not is_health and qk in CRITICAL_INFRA_QUESTIONS:
            # Allow safety_component for health
            if qk == "uses_ai_safety_component" and is_health:
                continue
            irrelevant.append({
                "question_key": qk,
                "reason": f"Obor '{industry}' — kritická infrastruktura nepravděpodobná",
            })
            continue

        # Rule 5: Small non-tech firm → prohibited systems terminology confusing
        if is_small and not is_tech and qk in PROHIBITED_SYSTEM_QUESTIONS:
            irrelevant.append({
                "question_key": qk,
                "reason": "Malá ne-tech firma — 'sociální skóring' / 'subliminalní manipulace' = matoucí terminologie",
            })
            continue

        # Rule 6: Non-tech → copilot / deepfake / GPAI questions confusing
        if not is_tech and qk in TECH_QUESTIONS:
            # uses_deepfake is actually understandable for content creators
            if qk == "uses_deepfake":
                continue  # deepfake is a known term
            irrelevant.append({
                "question_key": qk,
                "reason": f"Ne-tech firma — '{qk}' je příliš odborný pojem",
            })
            continue

        # Rule 7: No AI at all → data protection AI questions confusing
        if not uses_any_ai and qk in DATA_QUESTIONS:
            irrelevant.append({
                "question_key": qk,
                "reason": "Nepoužívá AI — otázky o AI zpracování dat matoucí",
            })
            continue

    # Calculate
    irrelevant_count = len(irrelevant)
    confusion_pct = round(irrelevant_count / total * 100, 1) if total > 0 else 0.0

    if confusion_pct <= 10:
        label = "nízká ✅"
    elif confusion_pct <= 25:
        label = "střední ⚠️"
    else:
        label = "vysoká 🔴"

    return {
        "total_questions": total,
        "irrelevant_count": irrelevant_count,
        "irrelevant_questions": irrelevant,
        "confusion_pct": confusion_pct,
        "confusion_label": label,
    }


# ═══════════════════════════════════════════════════════════════
# Pomocné funkce
# ═══════════════════════════════════════════════════════════════

def step_scan(persona: dict) -> dict:
    """Spustí quick scan a čeká na dokončení."""
    url = persona["test_url"]
    name = persona["name"]

    print(f"\n  [1/5] 🔍 Quick scan: {url}")

    # Retry loop pro rate limiting (429)
    for attempt in range(5):
        r = requests.post(f"{API_BASE}/scan", json={"url": url}, timeout=30)
        if r.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"        ⏳ Rate limit — čekám {wait}s (pokus {attempt+1}/5)")
            time.sleep(wait)
            continue
        r.raise_for_status()
        break
    else:
        print(f"        ❌ Rate limit — vyčerpány pokusy")
        return {"scan_id": "rate_limited", "company_id": "rate_limited", "findings": 0, "error": True}

    data = r.json()
    scan_id = data["scan_id"]
    company_id = data["company_id"]
    print(f"        scan_id={scan_id[:8]}…  company_id={company_id[:8]}…")

    # Poll until done
    elapsed = 0
    while elapsed < SCAN_POLL_TIMEOUT:
        time.sleep(SCAN_POLL_INTERVAL)
        elapsed += SCAN_POLL_INTERVAL
        sr = requests.get(f"{API_BASE}/scan/{scan_id}", timeout=15)
        status = sr.json().get("status", "unknown")
        if status == "done":
            findings = sr.json().get("total_findings", 0)
            print(f"        ✅ Scan hotov — {findings} nálezů ({elapsed}s)")
            return {"scan_id": scan_id, "company_id": company_id, "findings": findings}
        elif status == "error":
            print(f"        ❌ Scan selhal: {sr.json().get('error_message', '?')}")
            return {"scan_id": scan_id, "company_id": company_id, "findings": 0, "error": True}

    print(f"        ⚠️ Timeout po {elapsed}s")
    return {"scan_id": scan_id, "company_id": company_id, "findings": 0, "timeout": True}


def step_questionnaire(persona: dict, scan_result: dict) -> dict:
    """Odešle dotazník za personu."""
    name = persona["name"]
    company_id = scan_result["company_id"]
    scan_id = scan_result["scan_id"]

    print(f"  [2/5] 📋 Dotazník: {len(persona['answers'])} odpovědí")
    payload = {
        "company_id": company_id,
        "scan_id": scan_id,
        "answers": persona["answers"],
    }
    r = requests.post(f"{API_BASE}/questionnaire/submit", json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    analysis = data.get("analysis", {})
    risk = analysis.get("risk_breakdown", {})
    total = data.get("saved_count", 0)

    risk_str = ", ".join(f"{k}:{v}" for k, v in risk.items()) if risk else "N/A"
    print(f"        ✅ Uloženo {total} odpovědí — riziko: {risk_str}")
    return {"saved": total, "analysis": analysis}


def step_order(persona: dict, scan_result: dict) -> dict:
    """Vytvoří objednávku přímo v DB (simuluje platbu).

    Tabulka orders NEMÁ company_id — vazba je přes email →
    clients.email → clients.company_id → companies.id.
    Po insertu také aktualizujeme clients.workflow_status = 'paid'.
    """
    name = persona["name"]
    plan = persona["plan"]
    company_id = scan_result["company_id"]
    amount = PLAN_PRICES[plan]
    order_number = f"AS-{plan.upper()}-TEST{PERSONAS.index(persona)+1:02d}"
    email = persona["answers"][3]["answer"]  # company_contact_email

    print(f"  [3/5] 💳 Objednávka: {plan.upper()} ({amount} Kč) — {order_number}")

    # Přímý insert do DB přes Supabase
    from supabase import create_client as sc
    sb = sc(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    now = datetime.now(timezone.utc).isoformat()

    order_data = {
        "order_number": order_number,
        "gopay_payment_id": f"TEST-{order_number}",
        "plan": plan,
        "amount": amount,
        "email": email,
        "user_email": email,
        "status": "PAID",
        "order_type": "one_time",
        "payment_gateway": "test_simulation",
        "paid_at": now,
        "created_at": now,
    }

    # Smazat starý testovací order, pokud existuje (duplicitní order_number)
    try:
        sb.table("orders").delete().eq("order_number", order_number).execute()
    except Exception:
        pass

    r = sb.table("orders").insert(order_data).execute()
    order_id = r.data[0]["id"] if r.data else None
    print(f"        ✅ Order {order_number} — ID {order_id[:8] if order_id else '?'}…")

    # Aktualizovat klienta — nastavit plan + email dle objednávky
    try:
        sb.table("clients").update({
            "plan": plan,
            "email": email,
        }).eq("company_id", company_id).execute()
        print(f"        ✅ Client plan → {plan}, email → {email}")
    except Exception as e:
        print(f"        ⚠️ Client update: {e}")

    return {"order_id": order_id, "order_number": order_number, "plan": plan}


def _wait_for_scan_done(scan_id: str, max_wait: int = 600) -> str:
    """Čeká, dokud quick scan neskončí (done/error). Max max_wait sekund."""
    elapsed = 0
    while elapsed < max_wait:
        try:
            sr = requests.get(f"{API_BASE}/scan/{scan_id}", timeout=15)
            status = sr.json().get("status", "unknown")
            if status in ("done", "error"):
                return status
        except Exception:
            pass
        time.sleep(10)
        elapsed += 10
        if elapsed % 60 == 0:
            print(f"        ⏳ Čekám na dokončení quick scanu… ({elapsed}s)")
    return "timeout"


def step_deep_scan(persona: dict, scan_result: dict) -> dict:
    """Spustí deep scan. Pokud quick scan ještě neskončil, počká na něj."""
    scan_id = scan_result["scan_id"]

    if scan_id in ("rate_limited", "skip"):
        print(f"  [4/5] ❌ Deep scan nelze — chybí scan_id")
        return {"deep_scan": "error", "reason": "no valid scan_id"}

    # Pokud quick scan neskončil, počkáme na něj (max 10 min)
    if scan_result.get("timeout") or scan_result.get("error"):
        print(f"  [4/5] 🌍 Quick scan nebyl hotov — čekám na dokončení…")
        final_status = _wait_for_scan_done(scan_id, max_wait=600)
        if final_status == "done":
            print(f"        ✅ Quick scan dokončen — pokračuji s deep scanem")
        elif final_status == "error":
            print(f"        ❌ Quick scan selhal — deep scan nelze spustit")
            return {"deep_scan": "error", "reason": "quick scan failed"}
        else:
            print(f"        ❌ Quick scan stále nehotov po 10 min — deep scan nelze")
            return {"deep_scan": "error", "reason": "quick scan stuck"}

    print(f"  [4/5] 🌍 Deep scan spouštím…")

    try:
        r = requests.post(f"{API_BASE}/scan/{scan_id}/deep", timeout=30)
        if r.status_code == 200:
            data = r.json()
            status = data.get("deep_scan_status", "?")
            msg = data.get("message", "")
            print(f"        ✅ Deep scan: {status} — {msg}")
            return {"deep_scan": status}
        elif r.status_code == 429:
            msg = r.json().get("detail", "rate limit")
            print(f"        ⚠️ Deep scan cooldown: {msg}")
            return {"deep_scan": "cooldown", "reason": msg}
        elif r.status_code == 400:
            # Scan ještě není done — počkat a zkusit znovu
            msg = ""
            try:
                msg = r.json().get("detail", "")
            except Exception:
                msg = r.text[:200]
            if "nedokončen" in msg.lower() or "not done" in msg.lower():
                print(f"        ⏳ Scan ještě nedokončen — čekám…")
                final = _wait_for_scan_done(scan_id, max_wait=300)
                if final == "done":
                    # Retry
                    r2 = requests.post(f"{API_BASE}/scan/{scan_id}/deep", timeout=30)
                    if r2.status_code == 200:
                        data = r2.json()
                        print(f"        ✅ Deep scan: {data.get('deep_scan_status', '?')}")
                        return {"deep_scan": data.get("deep_scan_status", "pending")}
                print(f"        ❌ Deep scan nelze spustit: {msg}")
            return {"deep_scan": "error", "reason": msg}
        else:
            msg = ""
            try:
                msg = r.json().get("detail", r.text[:200])
            except Exception:
                msg = r.text[:200]
            print(f"        ⚠️ Deep scan ({r.status_code}): {msg}")
            return {"deep_scan": "error", "reason": msg}
    except Exception as e:
        print(f"        ❌ Deep scan exception: {e}")
        return {"deep_scan": "error", "reason": str(e)}


def step_generate_docs(persona: dict, scan_result: dict) -> dict:
    """Generuje compliance dokumenty (7 PDF + HTML + PPTX)."""
    company_id = scan_result["company_id"]

    if company_id in ("rate_limited", "skip"):
        print(f"  [5/5] ❌ Dokumenty nelze — chybí company_id")
        return {"docs": "error", "reason": "no valid company_id"}

    # Najít client_id
    from supabase import create_client as sc
    sb = sc(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    clients = sb.table("clients").select("id, plan").eq("company_id", company_id).limit(1).execute()
    if not clients.data:
        print(f"  [5/5] ❌ Client nenalezen pro company {company_id[:8]}…")
        return {"docs": "no_client"}

    client_id = clients.data[0]["id"]
    client_plan = clients.data[0].get("plan", "?")
    print(f"  [5/5] 📄 Generuji dokumenty (client={client_id[:8]}…, plan={client_plan})")

    try:
        r = requests.post(f"{API_BASE}/documents/generate/{client_id}", timeout=300)
        if r.status_code == 200:
            data = r.json()
            docs_list = data.get("documents", [])
            errors = data.get("errors", [])
            ok = len(docs_list)
            err = len(errors)
            summary = data.get("summary", {})
            print(f"        ✅ Vygenerováno: {ok} dokumentů, {err} chyb")
            if docs_list:
                for d in docs_list:
                    print(f"           📎 {d.get('template_name', d.get('template_key', '?'))} [{d.get('format', '?')}]")
            if errors:
                for e in errors[:3]:
                    print(f"           ❌ {e}")
            return {
                "docs_ok": ok,
                "docs_err": err,
                "client_id": client_id,
                "docs_list": [d.get("template_key", "?") for d in docs_list],
                "docs_summary": summary,
            }
        else:
            msg = ""
            try:
                msg = r.json().get("detail", r.text[:300])
            except Exception:
                msg = r.text[:300]
            print(f"        ❌ Chyba ({r.status_code}): {msg}")
            return {"docs": "error", "status_code": r.status_code, "detail": msg}
    except requests.exceptions.Timeout:
        print(f"        ❌ Timeout (300s) — generování trvá příliš dlouho")
        return {"docs": "timeout"}
    except Exception as e:
        print(f"        ❌ Exception: {e}")
        return {"docs": "error", "detail": str(e)}


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="AIshield Full Pipeline Test — KOMPLETNÍ (scan+dotazník+order+deep+docs)")
    parser.add_argument("--personas", type=str, default="1-10", help="Rozsah person (např. '1-3' nebo '1,5,8')")
    args = parser.parse_args()

    # Parse persona range
    persona_indices = []
    for part in args.personas.split(","):
        if "-" in part:
            start, end = part.split("-")
            persona_indices.extend(range(int(start) - 1, int(end)))
        else:
            persona_indices.append(int(part) - 1)

    # Validate env
    if not SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_SERVICE_KEY není nastaven!")
        print("   Export: export SUPABASE_SERVICE_KEY='...'")
        sys.exit(1)

    print("=" * 70)
    print(f"  AIshield.cz — Full Pipeline Test ({len(persona_indices)} person)")
    print(f"  API: {API_BASE}")
    print(f"  Deep scan interval: 5 min (testovací režim)")
    print("=" * 70)

    results = []

    for idx in persona_indices:
        persona = PERSONAS[idx]
        name = persona["name"]
        plan = persona["plan"]
        num = idx + 1

        print(f"\n{'─' * 60}")
        print(f"  PERSONA {num:02d}: {name}  [{plan.upper()}]")
        print(f"{'─' * 60}")

        result = {"persona": num, "name": name, "plan": plan}

        # Step 0: Confusion metric (míra zmatenosti)
        confusion = compute_confusion(persona)
        result["confusion"] = confusion
        print(f"  [0/5] 🧩 Zmatenost: {confusion['confusion_pct']}% ({confusion['irrelevant_count']}/{confusion['total_questions']} irelevantních) — {confusion['confusion_label']}")
        if confusion["irrelevant_questions"]:
            for iq in confusion["irrelevant_questions"][:5]:  # max 5 příkladů
                print(f"         • {iq['question_key']}: {iq['reason']}")
            if len(confusion["irrelevant_questions"]) > 5:
                print(f"         … a dalších {len(confusion['irrelevant_questions']) - 5}")

        # Step 1: Scan
        scan_result = step_scan(persona)
        result.update(scan_result)

        if scan_result.get("scan_id") == "rate_limited":
            # Fatální chyba — nemáme ani scan_id
            print(f"  ❌ Fatální chyba scanu (rate limit) — přeskakuji personu")
            results.append(result)
            continue

        # Step 2: Questionnaire
        q_result = step_questionnaire(persona, scan_result)
        result.update(q_result)

        # Step 3: Order
        try:
            o_result = step_order(persona, scan_result)
            result.update(o_result)
        except Exception as e:
            print(f"  [3/5] ❌ Order error: {e}")
            result["order_error"] = str(e)

        # Step 4: Deep scan — VŽDY (nepřeskakuje se)
        d_result = step_deep_scan(persona, scan_result)
        result.update(d_result)

        # Step 5: Generate docs — VŽDY (nepřeskakuje se)
        doc_result = step_generate_docs(persona, scan_result)
        result.update(doc_result)

        results.append(result)

        # Krátká pauza mezi personami (rate limiting)
        if idx < persona_indices[-1]:
            print(f"\n  ⏳ Pauza 30s před další personou…")
            time.sleep(30)

    # ── Souhrn ──
    print(f"\n\n{'═' * 90}")
    print(f"  SOUHRN PIPELINE TESTU")
    print(f"{'═' * 90}")
    print(f"{'Nr':>3} | {'Persona':<30} | {'Plán':>10} | {'Otázek':>6} | {'Zmatenost':>12} | {'Risk':>15} | {'Docs':>5}")
    print(f"{'─' * 3}-+-{'─' * 30}-+-{'─' * 10}-+-{'─' * 6}-+-{'─' * 12}-+-{'─' * 15}-+-{'─' * 5}")

    for r in results:
        risk_info = ""
        analysis = r.get("analysis", {})
        if analysis:
            risk = analysis.get("risk_breakdown", {})
            high = risk.get("high", 0)
            limited = risk.get("limited", 0)
            minimal = risk.get("minimal", 0)
            risk_info = f"H:{high} L:{limited} M:{minimal}"

        confusion = r.get("confusion", {})
        conf_str = f"{confusion.get('confusion_pct', '?')}%" if confusion else "?"

        docs = f"{r.get('docs_ok', '?')}" if 'docs_ok' in r else r.get('docs', '-')
        print(f"{r['persona']:>3} | {r['name']:<30} | {r['plan']:>10} | {r.get('saved', '?'):>6} | {conf_str:>12} | {risk_info:>15} | {docs:>5}")

    # ── Tabulka zmatenosti (detailní) ──
    print(f"\n{'═' * 90}")
    print(f"  DETAILNÍ PŘEHLED ZMATENOSTI (Míra zmatenosti)")
    print(f"{'═' * 90}")
    for r in results:
        confusion = r.get("confusion", {})
        if not confusion:
            continue
        label = confusion.get("confusion_label", "?")
        pct = confusion.get("confusion_pct", 0)
        irr = confusion.get("irrelevant_count", 0)
        tot = confusion.get("total_questions", 0)
        items = confusion.get("irrelevant_questions", [])

        print(f"\n  P{r['persona']:02d} {r['name']}")
        print(f"      {label}  —  {pct}%  ({irr} z {tot} otázek irelevantních)")
        if items:
            for iq in items:
                print(f"        • {iq['question_key']}: {iq['reason']}")
        else:
            print(f"        (žádné irelevantní otázky)")
    print()

    # Uložit JSON výsledky
    out_path = os.path.join(os.path.dirname(__file__), "pipeline_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  📁 Výsledky uloženy: {out_path}")
    print()


if __name__ == "__main__":
    main()
