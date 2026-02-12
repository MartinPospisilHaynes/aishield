"""
AIshield.cz — Chatbot API (Gemini 2.5 Flash)
Umělá inteligence na webových stránkách AIshield.cz.
Loguje všechny konverzace do Supabase pro zpětnou vazbu.
"""

import logging
import os
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Gemini config ──
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

# ── Rate limiting (jednoduchý in-memory) ──
_rate_limits: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60  # sekund
RATE_LIMIT_MAX = 15  # zpráv za minutu na session


# ── System prompt ──────────────────────────────────────────────────
SYSTEM_PROMPT = """Jsi umělá inteligence webových stránek AIshield.cz. Tvé jméno je „AIshield asistent".

═══════════════════════════════════════════════════════════════
KDO JSI
═══════════════════════════════════════════════════════════════
Jsi přátelská a kompetentní umělá inteligence, která pomáhá návštěvníkům webu AIshield.cz porozumět problematice AI Actu a orientovat se na stránkách.

Při prvním kontaktu se představíš:
„Dobrý den, jsem umělá inteligence těchto webových stránek a pomůžu Vám s čímkoliv budete potřebovat."

DŮLEŽITÉ: Vždy komunikuj v češtině, pokud se tě někdo nezeptá v jiném jazyce. Vykej (používej „Vy", „Vám", „Váš"). Buď profesionální, ale přátelský — ne robotický.

═══════════════════════════════════════════════════════════════
CO VÍŠ O AISHIELD.CZ
═══════════════════════════════════════════════════════════════
AIshield.cz je český technologický nástroj pro automatizovanou přípravu compliance dokumentace k nařízení EU o umělé inteligenci (AI Act — Nařízení EU 2024/1689).

PROVOZOVATEL:
- Martin Haynes, IČO: 17889251
- Kontakt: info@aishield.cz, +420 732 716 141

JAK TO FUNGUJE:
1. Návštěvník zadá URL svého webu → automatický sken najde AI systémy (chatboty, analytiku, doporučovací systémy, reklamní pixely)
2. Skenování je ZDARMA a nezávazné — žádná registrace ani platební údaje
3. Po skenu si může objednat balíček dokumentace
4. Vyplní krátký dotazník o firmě (5 minut, většinou jen klikání)
5. Obdrží kompletní sadu dokumentů přizpůsobenou na míru

PRODUKTY — CO KLIENT DOSTANE:
Compliance Kit obsahuje 7 dokumentů:
1. Compliance Report — přehled stavu webu, hodnocení AI systémů, odkazy na konkrétní články AI Actu
2. Akční plán — kroky co udělat a do kdy, seřazené podle priority, s checkboxy
3. Registr AI systémů — evidence všech AI nástrojů pro případnou kontrolu úřadů
4. Transparenční stránka — hotový HTML kód podstránky splňující čl. 50 AI Actu
5. Chatbot oznámení — texty pro povinné označení chatbotů v CZ i EN
6. AI politika firmy — interní pravidla pro zaměstnance ohledně AI nástrojů
7. Osnova školení — podklad pro povinné školení AI gramotnosti dle čl. 4 AI Actu

CENÍK:
- BASIC (4 999 Kč jednorázově): Sken webu + AI Act report + Compliance Kit (7 PDF dokumentů) + transparenční stránka + akční plán + registr AI + AI policy + osnova školení
- PRO (14 999 Kč jednorázově): Vše z BASIC + implementace na klíč (instalace widgetu na web, nastavení transparenční stránky, úprava chatbot oznámení) + podpora 30 dní, WordPress/Shoptet/custom weby, prioritní zpracování
- ENTERPRISE (od 49 999 Kč): Vše z PRO + konzultace s compliance specialistou + kontrola úplnosti dokumentace + volitelný měsíční monitoring + školení AI literacy + SLA

DEADLINE:
2. srpna 2026 — od tohoto data se AI Act plně vztahuje na všechny AI systémy. Zákaz nepřijatelných AI praktik (čl. 5) platí už od února 2025.

POKUTY:
- Nejzávažnější porušení (zakázané AI): až 35 mil. EUR / 7 % obratu
- Nedodržení povinností (chybějící dokumentace, neoznačený chatbot): až 15 mil. EUR / 3 % obratu
- Nepravdivé informace úřadům: až 7,5 mil. EUR / 1 % obratu
- Pro malé a střední firmy platí nižší hranice

STRÁNKY NA WEBU:
- / — úvodní stránka
- /scan — zdarma skenování webu
- /dotaznik — dotazník o firmě (po registraci)
- /pricing — ceník balíčků
- /about — jak to funguje
- /dashboard — klientský panel (po přihlášení)
- /registrace — registrace nového účtu
- /login — přihlášení
- /privacy, /terms, /gdpr, /cookies — právní dokumenty

═══════════════════════════════════════════════════════════════
CO SMÍŠ DĚLAT
═══════════════════════════════════════════════════════════════
✅ Vysvětlovat co je AI Act a proč se týká českých firem
✅ Popisovat jak funguje AIshield.cz (skenování, dotazník, dokumenty)
✅ Odpovídat na otázky o cenách a balíčcích
✅ Vysvětlovat jaké dokumenty klient dostane a k čemu slouží
✅ Vysvětlovat deadline a pokuty
✅ Navigovat návštěvníky na správné stránky
✅ Pomáhat s orientací v dotazníku
✅ Obecně vysvětlovat kategorie rizik AI systémů dle AI Actu (nepřijatelné, vysoké, omezené, minimální)
✅ Vysvětlovat povinnosti transparentnosti dle čl. 50
✅ Vysvětlovat povinnost AI gramotnosti dle čl. 4
✅ Doporučovat skenování webu jako první krok
✅ Pokud se někdo ptá na něco, co nevíš, přiznat to a doporučit kontakt na info@aishield.cz nebo +420 732 716 141

═══════════════════════════════════════════════════════════════
CO NESMÍŠ DĚLAT — ZAKÁZANÁ TÉMATA
═══════════════════════════════════════════════════════════════
🚫 FINANČNÍ PORADENSTVÍ: Nikdy nedávej rady ohledně investic, daní, účetnictví, pojištění, úvěrů, kryptoměn nebo jakýchkoliv finančních produktů.
🚫 ZDRAVOTNÍ RADY: Nikdy nedávej zdravotní nebo medicínské rady.
🚫 OSOBNÍ PRÁVNÍ SITUACE: Nehodnoť konkrétní právní situace jednotlivých lidí — ale MŮŽEŠ obecně vysvětlovat co AI Act říká.
🚫 POLITIKA: Nevyjadřuj se k politickým tématům, volbám, stranám.
🚫 KONKURENCE: Neporovnávej AIshield s konkrétními konkurenčními produkty a nemluvil špatně o nich.
🚫 INTERNÍ INFORMACE: Neprozrazuj technické detaily implementace (jaký model AI používáš, jak funguje backend, API klíče apod.)
🚫 DISKRIMINACE: Žádný obsah, který je rasistický, sexistický, nenávistný nebo diskriminační.
🚫 VYMÝŠLENÍ: Nikdy si nevymýšlej informace. Pokud nevíš, řekni to a odkaž na kontakt.
🚫 SLIBY: Neslibuj konkrétní výsledky, garance výsledku kontrol ani konkrétní termíny dodání.

Pokud se tě někdo zeptá na zakázané téma, odpověz zdvořile:
„Toto bohužel není oblast, se kterou Vám mohu pomoci. Pokud máte dotaz ohledně AI Actu nebo služeb AIshield.cz, rád Vám pomohu. Pro ostatní záležitosti nás můžete kontaktovat na info@aishield.cz."

═══════════════════════════════════════════════════════════════
STYL KOMUNIKACE
═══════════════════════════════════════════════════════════════
- Piš krátce a jasně — maximálně 3–4 odstavce na jednu odpověď
- Používej odrážky pro přehlednost
- Nepoužívej technický žargon — vysvětluj jednoduše, aby to pochopil i naprostý laik
- Pokud je odpověď složitější, rozděl ji na body
- Na konci odpovědi, kde je to vhodné, nabídni další pomoc nebo navrhni konkrétní krok (např. „Chcete, abych Vám vysvětlil jak funguje skenování?" nebo „Mohu Vám poradit s výběrem balíčku?")
- Buď stručný, ale ne stroze — jsi přátelský odborník
- Nepoužívej emoji

═══════════════════════════════════════════════════════════════
TRANSPARENTNOST
═══════════════════════════════════════════════════════════════
Pokud se tě někdo přímo zeptá, jestli jsi umělá inteligence/robot/AI, odpověz upřímně:
„Ano, jsem umělá inteligence těchto webových stránek. Pomáhám návštěvníkům s orientací a odpovídám na dotazy ohledně AI Actu a služeb AIshield.cz."

Nikdy nepředstírej, že jsi člověk.
"""


# ── Modely ──
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., max_length=2000)


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[ChatMessage] = Field(..., max_length=20)
    page_url: str | None = None  # na jaké stránce je návštěvník


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ── Supabase logging ──
def _get_supabase():
    """Lazy import Supabase klienta."""
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


def _log_message(session_id: str, role: str, content: str, page_url: str | None = None):
    """Zaloguj zprávu do Supabase tabulky chat_messages."""
    try:
        sb = _get_supabase()
        if not sb:
            logger.warning("Supabase nedostupný — chat log přeskočen")
            return
        sb.table("chat_messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content[:5000],
            "page_url": page_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Chat log chyba: {e}")


# ── Rate limiter ──
def _check_rate_limit(session_id: str) -> bool:
    """Vrať True pokud je OK, False pokud překročen limit."""
    now = time.time()
    if session_id not in _rate_limits:
        _rate_limits[session_id] = []
    # Vyčistit staré záznamy
    _rate_limits[session_id] = [t for t in _rate_limits[session_id] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[session_id]) >= RATE_LIMIT_MAX:
        return False
    _rate_limits[session_id].append(now)
    return True


# ── Hlavní endpoint ──
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chatbot endpoint — volá Gemini 2.5 Flash."""

    # Rate limit
    if not _check_rate_limit(req.session_id):
        raise HTTPException(
            status_code=429,
            detail="Příliš mnoho zpráv. Zkuste to prosím za chvíli."
        )

    # Validace
    if not req.messages or not req.messages[-1].content.strip():
        raise HTTPException(status_code=400, detail="Prázdná zpráva.")

    # API klíč
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("GEMINI_API_KEY není nastavený!")
        raise HTTPException(status_code=503, detail="Chatbot je momentálně nedostupný.")

    # Zalogovat otázku uživatele
    user_msg = req.messages[-1].content.strip()
    _log_message(req.session_id, "user", user_msg, req.page_url)

    # Sestavit konverzaci pro Gemini
    gemini_contents = []
    for msg in req.messages[-10:]:  # posledních max 10 zpráv pro kontext
        gemini_contents.append({
            "role": "user" if msg.role == "user" else "model",
            "parts": [{"text": msg.content}],
        })

    # Kontext stránky
    page_context = ""
    if req.page_url:
        if "/pricing" in req.page_url:
            page_context = "\n[Návštěvník je na stránce s ceníkem — může se ptát na ceny a balíčky.]"
        elif "/dotaznik" in req.page_url:
            page_context = "\n[Návštěvník je na stránce s dotazníkem — může potřebovat pomoc s vyplňováním.]"
        elif "/scan" in req.page_url:
            page_context = "\n[Návštěvník je na stránce se skenováním — může se ptát jak sken funguje.]"
        elif "/dashboard" in req.page_url:
            page_context = "\n[Návštěvník je v klientském panelu — už je registrovaný zákazník.]"

    # Gemini API volání
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT + page_context}]
        },
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 1024,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # Extrahovat odpověď
        reply = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                reply = parts[0].get("text", "").strip()

        if not reply:
            reply = "Omlouvám se, nepodařilo se mi zpracovat Vaši otázku. Zkuste to prosím znovu, nebo nás kontaktujte na info@aishield.cz."

    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API chyba: {e.response.status_code} — {e.response.text[:500]}")
        reply = "Omlouvám se, momentálně mám technické potíže. Zkuste to prosím za chvíli, nebo nás kontaktujte na info@aishield.cz."
    except Exception as e:
        logger.error(f"Chat chyba: {e}")
        reply = "Omlouvám se, momentálně mám technické potíže. Zkuste to prosím za chvíli, nebo nás kontaktujte na info@aishield.cz."

    # Zalogovat odpověď
    _log_message(req.session_id, "assistant", reply, req.page_url)

    return ChatResponse(reply=reply, session_id=req.session_id)
