"""
AIshield.cz — Golden Test Suite
Benchmarková sada 20 webů pro ověření kvality skeneru.

Spuštění: python -m pytest backend/scanner/test_golden.py -v
Nebo:     python backend/scanner/test_golden.py
"""

import asyncio
import sys
import os

# Zajistíme, že importy fungují
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.scanner.web_scanner import WebScanner
from backend.scanner.detector import AIDetector


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOLDEN TEST WEBSITES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Formát: (url, expected_min, expected_max, must_find, must_not_find)
#   expected_min: minimální počet findings
#   expected_max: maximální (nad = false positives)
#   must_find: seznam AI systémů, které MUSÍ být nalezeny
#   must_not_find: false positives, které se NESMÍ objevit

GOLDEN_TESTS = [
    # ── Weby BEZ AI (false positive kontrola) ──
    {
        "url": "https://example.com",
        "name": "example.com (statická stránka)",
        "expected_min": 0,
        "expected_max": 0,
        "must_find": [],
        "must_not_find": ["Shoptet AI", "Frase.io", "Drift", "Generický AI chatbot"],
    },
    {
        "url": "https://www.wikipedia.org",
        "name": "Wikipedia (žádné AI)",
        "expected_min": 0,
        "expected_max": 1,
        "must_find": [],
        "must_not_find": ["Shoptet AI", "Drift", "Vercel AI Chatbot"],
    },
    {
        "url": "https://www.seznam.cz",
        "name": "Seznam.cz (analytics, ne AI chatbot)",
        "expected_min": 0,
        "expected_max": 3,
        "must_find": [],
        "must_not_find": ["Generický AI chatbot", "Frase.io"],
    },

    # ── Weby s JEDNÍM AI systémem ──
    {
        "url": "https://www.intercom.com",
        "name": "Intercom (vlastní chatbot)",
        "expected_min": 1,
        "expected_max": 5,
        "must_find": ["Intercom"],
        "must_not_find": [],
    },
    {
        "url": "https://www.drift.com",
        "name": "Drift (vlastní chatbot)",
        "expected_min": 1,
        "expected_max": 5,
        "must_find": ["Drift"],
        "must_not_find": [],
    },

    # ── České e-shopy (Shoptet test) ──
    {
        "url": "https://www.alza.cz",
        "name": "Alza.cz (velký e-shop)",
        "expected_min": 0,
        "expected_max": 8,
        "must_find": [],
        "must_not_find": ["Shoptet AI"],  # Alza nepoužívá Shoptet
    },

    # ── Weby s více AI systémy ──
    {
        "url": "https://www.hubspot.com",
        "name": "HubSpot (chatbot + analytics)",
        "expected_min": 1,
        "expected_max": 8,
        "must_find": [],
        "must_not_find": ["Frase.io"],
    },

    # ── Tech weby (Vercel AI test) ──
    {
        "url": "https://vercel.com",
        "name": "Vercel (AI SDK stránka)",
        "expected_min": 0,
        "expected_max": 8,
        "must_find": [],
        "must_not_find": [],
    },

    # ── Další kontrolní weby ──
    {
        "url": "https://www.google.com",
        "name": "Google (žádné third-party AI)",
        "expected_min": 0,
        "expected_max": 2,
        "must_find": [],
        "must_not_find": ["Generický AI chatbot", "Frase.io", "Shoptet AI"],
    },
    {
        "url": "https://github.com",
        "name": "GitHub (žádné AI chatboty)",
        "expected_min": 0,
        "expected_max": 3,
        "must_find": [],
        "must_not_find": ["Shoptet AI", "Frase.io", "Help Scout Beacon"],
    },
]


async def run_golden_tests():
    """Spustí golden test suite a reportuje výsledky."""
    scanner = WebScanner(timeout_ms=30_000, wait_after_load_ms=3_000)
    detector = AIDetector()

    passed = 0
    failed = 0
    errors = 0
    total = len(GOLDEN_TESTS)

    print("=" * 70)
    print("  AIshield.cz — Golden Test Suite")
    print(f"  Testujeme {total} webů")
    print("=" * 70)
    print()

    for i, test in enumerate(GOLDEN_TESTS, 1):
        url = test["url"]
        name = test["name"]
        print(f"[{i}/{total}] {name}")
        print(f"  URL: {url}")

        try:
            page = await scanner.scan(url)
            if page.error:
                print(f"  ⚠️  Scanner error: {page.error[:100]}")
                errors += 1
                print()
                continue

            findings = detector.detect(page)
            finding_names = [f.name for f in findings]
            finding_names_lower = [n.lower() for n in finding_names]
            count = len(findings)

            test_pass = True
            issues = []

            # Check count range
            if count < test["expected_min"]:
                test_pass = False
                issues.append(
                    f"Příliš málo findings: {count} < {test['expected_min']}"
                )
            if count > test["expected_max"]:
                test_pass = False
                issues.append(
                    f"Příliš mnoho findings: {count} > {test['expected_max']} "
                    f"(možné false positives)"
                )

            # Check must_find
            for must in test["must_find"]:
                if must.lower() not in finding_names_lower:
                    test_pass = False
                    issues.append(f"Chybí expected finding: {must}")

            # Check must_not_find
            for must_not in test["must_not_find"]:
                if must_not.lower() in finding_names_lower:
                    test_pass = False
                    issues.append(f"False positive nalezeno: {must_not}")

            if test_pass:
                print(f"  ✅ PASS — {count} findings: {', '.join(finding_names) or '(žádné)'}")
                passed += 1
            else:
                print(f"  ❌ FAIL — {count} findings: {', '.join(finding_names) or '(žádné)'}")
                for issue in issues:
                    print(f"     ↳ {issue}")
                failed += 1

        except Exception as e:
            print(f"  💥 ERROR: {e}")
            errors += 1

        print()

    # Summary
    print("=" * 70)
    print(f"  VÝSLEDKY: {passed} passed / {failed} failed / {errors} errors")
    print(f"  Success rate: {passed}/{total} ({100 * passed // max(total, 1)}%)")
    print("=" * 70)

    return failed == 0 and errors == 0


if __name__ == "__main__":
    success = asyncio.run(run_golden_tests())
    sys.exit(0 if success else 1)
