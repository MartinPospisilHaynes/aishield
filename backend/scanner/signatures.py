"""
AIshield.cz — AI Signature Database
Databáze signatur pro detekci AI systémů na webových stránkách.

Každá signatura obsahuje:
- name: název AI systému (Smartsupp, Tidio, GA4...)
- category: kategorie (chatbot, analytics, recommender, content_gen...)
- signatures: seznam řetězců/patterns, které hledáme v HTML, skriptech, URL...
- risk_level: klasifikace podle AI Act (minimal, limited, high)
- ai_act_article: relevantní článek AI Act
- action_required: co musí firma udělat
"""

from dataclasses import dataclass, field


@dataclass
class AISignature:
    """Jedna signatura AI systému."""
    name: str
    category: str
    signatures: list[str]                   # Řetězce k hledání
    script_patterns: list[str] = field(default_factory=list)  # Patterns v URL skriptů
    iframe_patterns: list[str] = field(default_factory=list)  # Patterns v iframe src
    cookie_patterns: list[str] = field(default_factory=list)  # Patterns v cookies
    network_patterns: list[str] = field(default_factory=list) # Patterns v network requests
    risk_level: str = "limited"             # minimal, limited, high, unacceptable
    ai_act_article: str = "čl. 50"
    action_required: str = ""
    description_cs: str = ""                # Popis česky pro klienta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABÁZE SIGNATUR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI_SIGNATURES: list[AISignature] = [

    # ── CHATBOTY (AI Act čl. 50 — povinnost transparence) ──

    AISignature(
        name="Smartsupp",
        category="chatbot",
        signatures=["smartsupp", "smartsuppChat", "smartsupp.com"],
        script_patterns=["smartsupp.com"],
        cookie_patterns=["ssupp"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení, že uživatel komunikuje s AI chatbotem. "
                       "Zajistit možnost přepojení na lidského operátora.",
        description_cs="Smartsupp — český chatbot s AI funkcemi. Pokud používáte "
                       "automatické odpovědi, spadá pod čl. 50 AI Act.",
    ),

    AISignature(
        name="Tidio",
        category="chatbot",
        signatures=["tidio", "tidioChatCode", "tidio.co"],
        script_patterns=["tidio.co", "widget-v4.tidiochat"],
        cookie_patterns=["tidio"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení o AI chatbotu. Zajistit přepojení na člověka.",
        description_cs="Tidio — chatbot s AI funkcemi pro zákaznickou podporu.",
    ),

    AISignature(
        name="Intercom",
        category="chatbot",
        signatures=["intercom", "intercomSettings", "Intercom(", "intercom.io"],
        script_patterns=["widget.intercom.io", "intercom.com"],
        cookie_patterns=["intercom"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Označit AI odpovědi jako automaticky generované. "
                       "Umožnit eskalaci na člověka.",
        description_cs="Intercom — platforma zákaznické podpory s AI Fin chatbotem.",
    ),

    AISignature(
        name="Drift",
        category="chatbot",
        signatures=["drift", "driftt", "drift.com"],
        script_patterns=["drift.com", "js.driftt.com"],
        cookie_patterns=["drift"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení o AI chatbotu.",
        description_cs="Drift — konverzační AI pro marketing a prodej.",
    ),

    AISignature(
        name="Zendesk Chat",
        category="chatbot",
        signatures=["zopim", "zendesk", "zE(", "zESettings"],
        script_patterns=["static.zdassets.com", "ekr.zdassets.com"],
        cookie_patterns=["__zlcmid"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení o AI chatbotu, pokud používáte Answer Bot.",
        description_cs="Zendesk — helpdesk s AI chatbotem Answer Bot.",
    ),

    AISignature(
        name="LiveChat",
        category="chatbot",
        signatures=["LiveChatWidget", "livechat", "__lc_inited"],
        script_patterns=["cdn.livechatinc.com"],
        cookie_patterns=["__lc_cid"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení o AI chatbotu, pokud AI odpovídá automaticky.",
        description_cs="LiveChat — chat platforma s AI asistencí.",
    ),

    AISignature(
        name="Crisp",
        category="chatbot",
        signatures=["crisp", "$crisp", "CRISP_WEBSITE_ID"],
        script_patterns=["client.crisp.chat"],
        cookie_patterns=["crisp-client"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení o AI chatbotu.",
        description_cs="Crisp — chatbot platforma s AI funkcemi.",
    ),

    AISignature(
        name="HubSpot Chat",
        category="chatbot",
        signatures=["HubSpotConversations", "hubspot", "hs-script-loader"],
        script_patterns=["js.hs-scripts.com", "js.hubspot.com"],
        cookie_patterns=["hubspotutk", "__hs"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přidat oznámení o AI chatbotu u automatických odpovědí.",
        description_cs="HubSpot — CRM s chatbotem a AI asistencí.",
    ),

    AISignature(
        name="ChatGPT Widget",
        category="chatbot",
        signatures=["chatgpt", "openai", "gpt-widget"],
        script_patterns=["cdn.openai.com", "chat.openai.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="POVINNĚ označit jako AI systém. Uživatel musí vědět, "
                       "že komunikuje s umělou inteligencí.",
        description_cs="ChatGPT widget — AI chatbot od OpenAI přímo na webu.",
    ),

    # ── ANALYTIKA s AI (čl. 50 + čl. 26 — profilování) ──

    AISignature(
        name="Google Analytics 4",
        category="analytics",
        signatures=["gtag(", "google-analytics", "analytics.js", "GA4"],
        script_patterns=["googletagmanager.com/gtag", "google-analytics.com"],
        cookie_patterns=["_ga", "_gid"],
        risk_level="minimal",
        ai_act_article="čl. 50 odst. 4 (pokud AI predikce)",
        action_required="Pokud používáte AI predikce chování (Predictive Audiences), "
                       "přidejte informaci do cookie banneru a privacy policy.",
        description_cs="Google Analytics 4 — webová analytika s AI predikcemi chování uživatelů.",
    ),

    AISignature(
        name="Google Tag Manager",
        category="analytics",
        signatures=["GTM-", "googletagmanager"],
        script_patterns=["googletagmanager.com/gtm.js"],
        risk_level="minimal",
        ai_act_article="čl. 50 odst. 4",
        action_required="Zkontrolujte, které AI tagy máte v GTM nakonfigurované. "
                       "Každý AI tag vyžaduje transparenci.",
        description_cs="Google Tag Manager — správce tagů, může obsahovat AI trackery.",
    ),

    AISignature(
        name="Hotjar",
        category="analytics",
        signatures=["hotjar", "_hjSettings", "hjSiteSettings"],
        script_patterns=["static.hotjar.com", "hotjar.com"],
        cookie_patterns=["_hj"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1, čl. 26",
        action_required="Pokud Hotjar AI analyzuje chování uživatelů, přidejte "
                       "informaci do privacy policy. AI heatmapy = profilování.",
        description_cs="Hotjar — analýza chování na webu s AI heatmapami a session recordings.",
    ),

    AISignature(
        name="Microsoft Clarity",
        category="analytics",
        signatures=["clarity", "microsoft.com/clarity"],
        script_patterns=["clarity.ms"],
        cookie_patterns=["_clsk", "_clck"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Clarity používá AI pro analýzu chování. Přidejte do privacy policy.",
        description_cs="Microsoft Clarity — bezplatná analytika s AI session recordings.",
    ),

    AISignature(
        name="Meta Pixel",
        category="analytics",
        signatures=["fbq(", "facebook.com/tr", "Meta Pixel"],
        script_patterns=["connect.facebook.net", "facebook.com/tr"],
        cookie_patterns=["_fbp", "_fbc"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 4, čl. 26",
        action_required="Meta Pixel používá AI pro cílení reklam a lookalike audience. "
                       "Přidejte informaci do cookie banneru.",
        description_cs="Meta Pixel — sledování konverzí s AI cílením reklam.",
    ),

    # ── AI DOPORUČOVACÍ SYSTÉMY (čl. 50 + čl. 26) ──

    AISignature(
        name="Algolia",
        category="recommender",
        signatures=["algolia", "algoliasearch", "ALGOLIA_APP_ID"],
        script_patterns=["algolia.net", "algoliasearch"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Pokud Algolia AI doporučuje produkty, informujte uživatele.",
        description_cs="Algolia — AI vyhledávání a doporučování produktů.",
    ),

    AISignature(
        name="Recombee",
        category="recommender",
        signatures=["recombee", "recombee.com"],
        script_patterns=["client.recombee.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1, čl. 26",
        action_required="AI doporučování produktů vyžaduje transparenci vůči uživateli.",
        description_cs="Recombee — český AI doporučovací engine pro e-shopy.",
    ),

    AISignature(
        name="Barilliance",
        category="recommender",
        signatures=["barilliance", "bari_"],
        script_patterns=["barilliance.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="AI personalizace a doporučování vyžaduje transparenci.",
        description_cs="Barilliance — AI personalizace a product recommendations.",
    ),

    # ── AI CONTENT GENERATION (čl. 50 odst. 2) ──

    AISignature(
        name="Copy.ai",
        category="content_gen",
        signatures=["copy.ai", "copyai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generovaný obsah musí být označen jako vytvořený AI.",
        description_cs="Copy.ai — AI generování marketingového obsahu.",
    ),

    AISignature(
        name="Jasper AI",
        category="content_gen",
        signatures=["jasper.ai", "jasper-ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generovaný obsah musí být označen.",
        description_cs="Jasper AI — AI generování obsahu pro marketing.",
    ),

    # ── DALŠÍ AI NÁSTROJE ──

    AISignature(
        name="Shoptet AI",
        category="recommender",
        signatures=["shoptet", "shoptet.cz"],
        script_patterns=["cdn.myshoptet.com"],
        cookie_patterns=["shoptet"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Pokud Shoptet používá AI doporučování produktů, "
                       "informujte zákazníky.",
        description_cs="Shoptet — česká e-shop platforma s AI funkcemi.",
    ),

    AISignature(
        name="Seznam Retargeting",
        category="analytics",
        signatures=["seznam.cz/retargeting", "szn.cz", "imedia.cz"],
        script_patterns=["c.seznam.cz", "d.seznam.cz", "imedia.cz"],
        cookie_patterns=["szn"],
        risk_level="minimal",
        ai_act_article="čl. 50 odst. 4",
        action_required="Seznam retargeting s AI cílením — přidejte do cookie banneru.",
        description_cs="Seznam — český vyhledávač s AI retargetingem.",
    ),

    AISignature(
        name="Heureka",
        category="analytics",
        signatures=["heureka", "heureka.cz"],
        script_patterns=["im9.cz", "heureka.cz"],
        risk_level="minimal",
        ai_act_article="čl. 50 odst. 4",
        action_required="Heureka Měření konverzí — minimální riziko, ale přidejte do cookie banneru.",
        description_cs="Heureka — měření konverzí a recenze.",
    ),

    AISignature(
        name="Replai / AI Chatbot (generic)",
        category="chatbot",
        signatures=["ai-chatbot", "ai_chatbot", "chatbot-ai", "virtual-assistant"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Jakýkoli AI chatbot musí být označen jako AI systém.",
        description_cs="Generický AI chatbot detekovaný na stránce.",
    ),
]


def get_all_signatures() -> list[AISignature]:
    """Vrátí všechny signatury."""
    return AI_SIGNATURES


def get_signatures_by_category(category: str) -> list[AISignature]:
    """Vrátí signatury podle kategorie."""
    return [s for s in AI_SIGNATURES if s.category == category]
