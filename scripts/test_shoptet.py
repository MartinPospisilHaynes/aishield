"""
AIshield.cz — Shoptet Addon: Standalone testy
Spuštění: python3 test_shoptet.py

Testuje:
1. Klasifikace AI systémů (modely)
2. Crypto (Fernet encrypt/decrypt)
3. Webhook IP verifikace
4. Wizard logiku
5. Compliance stránka generování HTML
"""

import os
import sys

# Nastavit env vars pro testy
os.environ.setdefault("SHOPTET_ENCRYPTION_KEY", "dGVzdF9rZXlfMzJfYnl0ZXNfYmFzZTY0X189")  # placeholder
os.environ.setdefault("CHAT_ENCRYPTION_KEY", "dGVzdF9rZXlfMzJfYnl0ZXNfYmFzZTY0X189")

# Přidat project root do path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0
errors = []


def test(name):
    """Dekorátor pro test funkce."""
    def decorator(fn):
        global passed, failed
        try:
            fn()
            passed += 1
            print(f"  OK  {name}")
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  FAIL  {name}: {e}")
    return decorator


# ═══════════════════════════════════════════
# TEST 1: Klasifikace AI systémů
# ═══════════════════════════════════════════

@test("Klasifikace chatbot → art50, limited")
def _():
    from backend.shoptet.models import AI_ACT_CLASSIFICATION
    cls = AI_ACT_CLASSIFICATION["chatbot"]
    assert cls["ai_act_article"] == "art50", f"Očekáváno art50, dostáno {cls['ai_act_article']}"
    assert cls["risk_level"] == "limited", f"Očekáváno limited, dostáno {cls['risk_level']}"


@test("Klasifikace content → art50, limited")
def _():
    from backend.shoptet.models import AI_ACT_CLASSIFICATION
    cls = AI_ACT_CLASSIFICATION["content"]
    assert cls["ai_act_article"] == "art50"
    assert cls["risk_level"] == "limited"


@test("Klasifikace recommendation → art4, minimal")
def _():
    from backend.shoptet.models import AI_ACT_CLASSIFICATION
    cls = AI_ACT_CLASSIFICATION["recommendation"]
    assert cls["ai_act_article"] == "art4"
    assert cls["risk_level"] == "minimal"


@test("Klasifikace search → art4, minimal")
def _():
    from backend.shoptet.models import AI_ACT_CLASSIFICATION
    cls = AI_ACT_CLASSIFICATION["search"]
    assert cls["ai_act_article"] == "art4"
    assert cls["risk_level"] == "minimal"


@test("Klasifikace pricing → art4, minimal")
def _():
    from backend.shoptet.models import AI_ACT_CLASSIFICATION
    cls = AI_ACT_CLASSIFICATION["pricing"]
    assert cls["ai_act_article"] == "art4"


@test("Klasifikace other → art4, minimal")
def _():
    from backend.shoptet.models import AI_ACT_CLASSIFICATION
    cls = AI_ACT_CLASSIFICATION["other"]
    assert cls["ai_act_article"] == "art4"


# ═══════════════════════════════════════════
# TEST 2: Fernet Crypto
# ═══════════════════════════════════════════

@test("Crypto: encrypt → decrypt roundtrip")
def _():
    from cryptography.fernet import Fernet
    # Vygenerovat skutečný klíč pro test
    key = Fernet.generate_key().decode()
    os.environ["SHOPTET_ENCRYPTION_KEY"] = key

    from importlib import reload
    import backend.shoptet.crypto as crypto_mod
    reload(crypto_mod)

    encrypted = crypto_mod.encrypt_token("my_secret_oauth_token_123")
    assert encrypted is not None, "Encrypt vrátil None"
    assert encrypted != "my_secret_oauth_token_123", "Token nebyl zašifrován"

    decrypted = crypto_mod.decrypt_token(encrypted)
    assert decrypted == "my_secret_oauth_token_123", f"Decrypt selhal: {decrypted}"


@test("Crypto: encrypt_email → decrypt_email roundtrip")
def _():
    from backend.shoptet.crypto import encrypt_email, decrypt_email
    encrypted = encrypt_email("test@example.com")
    assert encrypted is not None
    decrypted = decrypt_email(encrypted)
    assert decrypted == "test@example.com"


@test("Crypto: prázdný vstup → None")
def _():
    from backend.shoptet.crypto import encrypt_token, decrypt_token
    assert encrypt_token("") is None
    assert decrypt_token("") is None


# ═══════════════════════════════════════════
# TEST 3: Webhook IP verifikace
# ═══════════════════════════════════════════

@test("Webhook: Shoptet IP je validní (185.184.254.1)")
def _():
    from backend.shoptet.webhooks import is_shoptet_ip
    assert is_shoptet_ip("185.184.254.1") is True
    assert is_shoptet_ip("185.184.254.100") is True
    assert is_shoptet_ip("185.184.254.254") is True


@test("Webhook: cizí IP je odmítnuta")
def _():
    from backend.shoptet.webhooks import is_shoptet_ip
    assert is_shoptet_ip("1.2.3.4") is False
    assert is_shoptet_ip("192.168.1.1") is False
    assert is_shoptet_ip("10.0.0.1") is False


@test("Webhook: neplatná IP → False")
def _():
    from backend.shoptet.webhooks import is_shoptet_ip
    assert is_shoptet_ip("not-an-ip") is False
    assert is_shoptet_ip("") is False


# ═══════════════════════════════════════════
# TEST 4: HMAC verifikace
# ═══════════════════════════════════════════

@test("HMAC: platný podpis")
def _():
    import hashlib
    import hmac as hmac_mod
    os.environ["SHOPTET_CLIENT_SECRET"] = "test_secret_123"

    from backend.shoptet.client import verify_webhook_signature
    body = b'{"event":"addon:uninstall","eshopId":12345}'
    expected_sig = hmac_mod.new(b"test_secret_123", body, hashlib.sha1).hexdigest()
    assert verify_webhook_signature(body, expected_sig) is True


@test("HMAC: neplatný podpis")
def _():
    os.environ["SHOPTET_CLIENT_SECRET"] = "test_secret_123"
    from backend.shoptet.client import verify_webhook_signature
    body = b'{"event":"addon:uninstall","eshopId":12345}'
    assert verify_webhook_signature(body, "invalid_signature") is False


# ═══════════════════════════════════════════
# TEST 5: Pydantic modely
# ═══════════════════════════════════════════

@test("WizardRequest: validní vstup")
def _():
    from backend.shoptet.models import WizardRequest, AISystemEntry
    data = WizardRequest(
        chatbots=[AISystemEntry(provider="Smartsupp", ai_type="chatbot")],
        content_ai=[],
        other_ai=[],
    )
    assert len(data.chatbots) == 1
    assert data.chatbots[0].provider == "Smartsupp"


@test("WizardRequest: prázdný vstup je OK")
def _():
    from backend.shoptet.models import WizardRequest
    data = WizardRequest()
    assert len(data.chatbots) == 0
    assert len(data.content_ai) == 0
    assert len(data.other_ai) == 0


@test("AISystemEntry: neplatný ai_type → ValidationError")
def _():
    from backend.shoptet.models import AISystemEntry
    from pydantic import ValidationError
    try:
        AISystemEntry(provider="Test", ai_type="invalid_type")
        assert False, "Měla být ValidationError"
    except ValidationError:
        pass  # OK — správně odmítnuto


@test("WizardResponse model")
def _():
    from backend.shoptet.models import WizardResponse
    resp = WizardResponse(
        installation_id="test-id",
        ai_systems_count=3,
        compliance_score=70,
        art50_relevant=1,
        art4_relevant=2,
        message="OK",
    )
    assert resp.compliance_score == 70
    assert resp.compliance_page_url is None


# ═══════════════════════════════════════════
# TEST 6: Compliance HTML generování
# ═══════════════════════════════════════════

@test("Compliance HTML: základní generování")
def _():
    from backend.shoptet.compliance_page import _generate_compliance_html
    ai_systems = [
        {
            "provider": "Smartsupp",
            "ai_type": "chatbot",
            "ai_act_article": "art50",
            "risk_level": "limited",
            "details": {"description_cs": "AI chatbot"},
        },
        {
            "provider": "Doporučovač",
            "ai_type": "recommendation",
            "ai_act_article": "art4",
            "risk_level": "minimal",
            "details": {"description_cs": "Doporučovací engine"},
        },
    ]
    html = _generate_compliance_html("Testshop.cz", ai_systems)
    assert "Testshop.cz" in html, "Chybí jméno eshopu"
    assert "Smartsupp" in html, "Chybí Art50 systém"
    assert "Article 50" in html, "Chybí zmínka o Article 50"
    assert "aishield.cz" in html, "Chybí AIshield odkaz"


@test("Compliance HTML: XSS escape")
def _():
    from backend.shoptet.compliance_page import _generate_compliance_html
    ai_systems = [{
        "provider": "<script>alert('xss')</script>",
        "ai_type": "chatbot",
        "ai_act_article": "art50",
        "risk_level": "limited",
        "details": {"description_cs": "Test"},
    }]
    html = _generate_compliance_html("Test", ai_systems)
    assert "<script>" not in html, "XSS: <script> tag prošel!"
    assert "&lt;script&gt;" in html, "XSS: chybí escape"


@test("Compliance HTML: prázdné AI systémy")
def _():
    from backend.shoptet.compliance_page import _generate_compliance_html
    html = _generate_compliance_html("Prázdný shop", [])
    assert "nebyly identifikovány" in html


# ═══════════════════════════════════════════
# TEST 7: Wizard klasifikace
# ═══════════════════════════════════════════

@test("Wizard: _classify_ai_system chatbot")
def _():
    from backend.shoptet.wizard import _classify_ai_system
    result = _classify_ai_system("chatbot")
    assert result["ai_act_article"] == "art50"
    assert result["risk_level"] == "limited"


@test("Wizard: _classify_ai_system neznámý typ → other")
def _():
    from backend.shoptet.wizard import _classify_ai_system
    result = _classify_ai_system("neexistujici_typ")
    assert result["ai_act_article"] == "art4"
    assert result["risk_level"] == "minimal"


@test("Wizard: _calculate_compliance_score")
def _():
    from backend.shoptet.wizard import _calculate_compliance_score
    # 0 systémů → 40 (základ za wizard)
    assert _calculate_compliance_score([]) == 40
    # 1 systém → 40 + 10 = 50
    assert _calculate_compliance_score([{"a": 1}]) == 50
    # 3 systémy → 40 + 30 = 70 (cap)
    assert _calculate_compliance_score([{}, {}, {}]) == 70
    # 5 systémů → stále 70 (max 30 bonus)
    assert _calculate_compliance_score([{}, {}, {}, {}, {}]) == 70


# ═══════════════════════════════════════════
# SOUHRN
# ═══════════════════════════════════════════

print(f"\n{'='*50}")
print(f"  VÝSLEDKY: {passed} OK, {failed} FAIL")
print(f"{'='*50}")

if errors:
    print("\nSelhané testy:")
    for name, err in errors:
        print(f"  - {name}: {err}")
    print()

sys.exit(1 if failed > 0 else 0)
