#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from api.questionnaire import QUESTIONNAIRE_SECTIONS

for sec in QUESTIONNAIRE_SECTIONS:
    sid = sec["id"]
    stitle = sec["title"]
    print(f"\n=== {sid.upper()}: {stitle} ===")
    for q in sec["questions"]:
        risk = q.get("risk_hint", "none")
        art = q.get("ai_act_article", "-")
        qtype = q.get("type", "?")
        print(f"  [{q['key']}] type={qtype} risk={risk} art={art}")
        print(f"    Q: {q['text']}")
        fu = q.get("followup")
        if fu:
            for f in fu["fields"]:
                print(f"      -> followup({fu['condition']}): [{f['key']}] {f['type']} | {f['label'][:90]}")
        fy = q.get("followup_yes")
        if fy:
            for f in fy["fields"]:
                print(f"      -> yes: [{f['key']}] {f['type']} | {f['label'][:90]}")
        fn = q.get("followup_no")
        if fn:
            for f in fn["fields"]:
                print(f"      -> no: [{f['key']}] {f['type']} | {f['label'][:90]}")

print(f"\n--- TOTAL: {sum(len(s['questions']) for s in QUESTIONNAIRE_SECTIONS)} questions in {len(QUESTIONNAIRE_SECTIONS)} sections ---")
