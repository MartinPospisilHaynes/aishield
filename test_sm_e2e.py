#!/usr/bin/env python3
"""
State Machine E2E Test — Single Persona through Uršula Chat
============================================================
Tests: init → chat (all questions) → closing → document generation
Uses BioKrása.cz persona with realistic natural-language answers.
Tracks total token usage and cost.
"""

import json
import os
import sys
import time
import uuid
import requests

API_BASE = "https://api.aishield.cz/api"

# BioKrása persona — natural language answers (like a real user would type)
ANSWERS = [
    # Q: company_legal_name
    "BioKrása.cz s.r.o.",
    # Q: company_ico
    "78901204",
    # Q: company_address (ARES should auto-fill, but if asked)
    "Na Příkopě 22, 110 00 Praha 1",
    # Q: company_contact_email
    "petr@biokrasa.cz",
    # Q: company_industry
    "E-shop / Online obchod",
    # Q: eshop_platform
    "Shoptet",
    # Q: company_size
    "10–49 zaměstnanců",
    # Q: company_annual_revenue
    "10–50 mil. Kč",
    # Q: develops_own_ai
    "Ne, nevyvíjíme vlastní AI",
    # Q: uses_chatgpt
    "Ano, používáme ChatGPT pro psaní produktových popisků a odpovídání zákazníkům. Pracujeme jen s veřejnými daty.",
    # Q: uses_copilot
    "Ne",
    # Q: uses_ai_content
    "Ano, používáme ChatGPT a Canvu na tvorbu obsahu pro web a sociální sítě.",
    # Q: uses_deepfake
    "Ne",
    # Q: uses_ai_chatbot
    "Ano, máme chatbot Tidio na webu",
    # Q: uses_ai_email_auto
    "Ano, používáme Mailchimp AI pro e-mailové kampaně",
    # Q: uses_ai_decision
    "Ne, žádné automatické rozhodování nepoužíváme",
    # Q: uses_dynamic_pricing
    "Ano, máme dynamické ceny podle poptávky a konkurence, vlastní řešení",
    # Q: uses_ai_for_children
    "Ne",
    # Q: uses_ai_recruitment
    "Ne",
    # Q: uses_ai_employee_monitoring
    "Ne",
    # Q: uses_emotion_recognition
    "Ne",
    # Q: uses_ai_accounting
    "Ne",
    # Q: uses_ai_creditscoring
    "Ne",
    # Q: uses_ai_insurance
    "Ne",
    # Q: uses_social_scoring
    "Ne",
    # Q: uses_subliminal_manipulation
    "Ne",
    # Q: uses_realtime_biometric
    "Ne",
    # Q: uses_ai_critical_infra
    "Ne",
    # Q: uses_ai_safety_component
    "Ne",
    # Q: ai_processes_personal_data
    "Ano, zpracováváme e-maily, objednávky a adresy zákazníků. DPIA jsme nedělali.",
    # Q: ai_data_stored_eu
    "Nevím přesně kde jsou data uložena",
    # Q: has_ai_vendor_contracts
    "Ne, nemáme žádné smlouvy s dodavateli AI",
    # Q: has_ai_training
    "Ne, zaměstnance jsme neškolili",
    # Q: has_ai_guidelines
    "Ne, nemáme žádné interní směrnice pro AI",
    # Q: has_oversight_person
    "Ne, nikdo to nemá na starosti",
    # Q: can_override_ai
    "Ano, u chatbotu a dynamických cen můžeme zasáhnout",
    # Q: ai_decision_logging
    "Ne, nelogujeme",
    # Q: has_ai_register
    "Ne, nemáme registr",
    # Q: modifies_ai_purpose
    "Ne",
    # Q: uses_gpai_api
    "Ne",
    # Q: has_incident_plan
    "Ne, nemáme žádný plán pro incidenty",
    # Q: monitors_ai_outputs
    "Ne",
    # Q: tracks_ai_changes
    "Ne",
    # Q: has_ai_bias_check
    "Ne",
    # Q: transparency_page
    "Implementujeme sami",
]

def parse_sse(raw: str) -> dict:
    """Parse SSE events from raw response text."""
    events = {}
    current_event = None
    current_data = []
    
    for line in raw.split("\n"):
        if line.startswith("event: "):
            if current_event and current_data:
                data_str = "\n".join(current_data)
                events[current_event] = data_str
            current_event = line[7:].strip()
            current_data = []
        elif line.startswith("data: "):
            current_data.append(line[6:])
        elif line == "" and current_event:
            if current_data:
                events[current_event] = "\n".join(current_data)
            current_event = None
            current_data = []
    
    # Last event
    if current_event and current_data:
        events[current_event] = "\n".join(current_data)
    
    return events


def main():
    print("=" * 60)
    print("AIshield State Machine E2E Test — BioKrása.cz s.r.o.")
    print("=" * 60)
    
    company_id = str(uuid.uuid4())
    print(f"\nCompany ID: {company_id}")
    
    # ── Step 1: Init ──
    print("\n── Step 1: Init ──")
    resp = requests.get(f"{API_BASE}/mart1n/init", params={"company_id": company_id})
    init_data = resp.json()
    session_id = init_data["session_id"]
    print(f"Session: {session_id}")
    print(f"Greeting: {init_data['multi_messages'][0]['text'][:100]}...")
    print(f"First question: {init_data['multi_messages'][1]['text'][:100]}")
    
    # ── Step 2: Chat through all answers ──
    print("\n── Step 2: Chat (State Machine) ──")
    total_in = 0
    total_out = 0
    total_cache_read = 0
    total_cache_write = 0
    total_cost = 0.0
    extracted_total = 0
    turn = 0
    
    for i, answer in enumerate(ANSWERS):
        turn += 1
        resp = requests.post(
            f"{API_BASE}/mart1n/chat/stream",
            json={
                "session_id": session_id,
                "company_id": company_id,
                "message": answer,
            },
            timeout=60,
        )
        
        events = parse_sse(resp.text)
        
        if "error" in events:
            err = json.loads(events["error"])
            print(f"  Turn {turn}: ❌ ERROR: {err}")
            # If rate limited, wait and retry
            if "rate" in str(err).lower() or "příliš" in str(err).lower():
                print("  Waiting 10s for rate limit...")
                time.sleep(10)
                resp = requests.post(
                    f"{API_BASE}/mart1n/chat/stream",
                    json={"session_id": session_id, "company_id": company_id, "message": answer},
                    timeout=60,
                )
                events = parse_sse(resp.text)
                if "error" in events:
                    print(f"  Turn {turn}: ❌ STILL ERROR after retry")
                    continue
            else:
                continue
        
        if "full" in events:
            # Closing response — parse it
            full_data = json.loads(events["full"])
            print(f"\n  Turn {turn}: 🎉 COMPLETE!")
            print(f"  Closing messages: {len(full_data.get('multi_messages', []))}")
            for mm in full_data.get("multi_messages", [])[:3]:
                text = mm.get("text", "")[:80]
                print(f"    → {text}...")
            break
        
        if "meta" in events:
            meta = json.loads(events["meta"])
            extracted = meta.get("extracted_answers", [])
            extracted_total += len(extracted)
            progress = meta.get("progress", 0)
            section = meta.get("current_section", "")
            msg = meta.get("message", "")[:80]
            
            keys_extracted = [ea["question_key"] for ea in extracted]
            
            print(f"  Turn {turn:2d}: progress={progress:3d}% section={section:20s} "
                  f"extracted={keys_extracted or '[]'}")
            if not extracted:
                print(f"         ⚠ No extraction! Msg: {msg}")
        else:
            # Tokens only, no meta
            token_text = ""
            for line in resp.text.split("\n"):
                if line.startswith("data: ") and not line.startswith("data: {}"):
                    try:
                        token_text += json.loads(line[6:])
                    except:
                        pass
            print(f"  Turn {turn:2d}: [tokens only] {token_text[:80]}...")
        
        # Small delay to avoid rate limiting
        time.sleep(1.5)
    
    print(f"\n── Results ──")
    print(f"Total turns: {turn}")
    print(f"Total extracted answers: {extracted_total}")
    
    # ── Step 3: Check progress ──
    print("\n── Step 3: Check Progress ──")
    resp = requests.get(f"{API_BASE}/mart1n/progress/{company_id}")
    if resp.status_code == 200:
        prog = resp.json()
        print(f"Answered: {prog.get('answered', 0)} / {prog.get('total', 0)} = {prog.get('progress', 0)}%")
    
    # ── Step 4: Check server logs for cost ──
    print("\n── Step 4: Cost Summary ──")
    print("Check server logs: ssh root@46.28.110.102 'journalctl -u aishield-api --since \"10 min ago\" | grep \"Stream usage\" | tail -50'")
    
    print(f"\n{'='*60}")
    print("E2E Test Complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
