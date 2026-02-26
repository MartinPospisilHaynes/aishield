#!/usr/bin/env python3
"""Test which Claude models are available on the API."""
import anthropic

with open("/opt/aishield/.env") as f:
    for line in f:
        if line.startswith("ANTHROPIC_API_KEY="):
            key = line.split("=", 1)[1].strip()
            break

client = anthropic.Anthropic(api_key=key)

models = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet-20240620",
    "claude-3-7-sonnet-20250219",
    "claude-3-7-sonnet-latest",
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
]

for m in models:
    try:
        r = client.messages.create(model=m, max_tokens=5, messages=[{"role": "user", "content": "1+1="}])
        text = r.content[0].text.strip()
        cost_in = r.usage.input_tokens
        cost_out = r.usage.output_tokens
        print(f"  OK: {m:<40} (in={cost_in}, out={cost_out}, reply={text})")
    except Exception as e:
        err = str(e).split("\n")[0][:100]
        print(f"FAIL: {m:<40} -> {err}")
