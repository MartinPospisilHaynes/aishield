#!/usr/bin/env python3
"""Quick CI job status + failure logs"""
import json, urllib.request, io, zipfile

TOKEN = "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"
REPO = "MartinPospisilHaynes/aishield"
API = f"https://api.github.com/repos/{REPO}"

def get(path):
    req = urllib.request.Request(f"{API}/{path}")
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

# Latest run
runs = get("actions/runs?per_page=1")
run = runs['workflow_runs'][0]
run_id = run['id']
print(f"Run #{run_id} | {run['event']} | {run['status']} | {run.get('conclusion','?')}")

# Jobs
jobs = get(f"actions/runs/{run_id}/jobs")
for j in jobs['jobs']:
    c = j.get('conclusion') or j['status']
    print(f"  {'OK' if c=='success' else 'FAIL' if c=='failure' else c:6s} {j['name']}")
    if c == 'failure':
        for s in j.get('steps', []):
            if s.get('conclusion') == 'failure':
                print(f"         FAILED: {s['name']}")

# Download logs
print("\n--- E2E Test Logs (last 50 lines) ---")
req = urllib.request.Request(f"{API}/actions/runs/{run_id}/logs")
req.add_header("Authorization", f"token {TOKEN}")
with urllib.request.urlopen(req) as r:
    z = zipfile.ZipFile(io.BytesIO(r.read()))
for name in z.namelist():
    if 'E2E' in name and 'mega' in name.lower():
        lines = z.read(name).decode(errors='replace').strip().split('\n')
        for l in lines[-50:]:
            print(l)
        break
