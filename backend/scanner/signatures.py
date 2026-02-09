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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CHATBOTY (AI Act čl. 50 odst. 1)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        signatures=["chatgpt-widget", "gpt-widget", "openai-widget"],
        script_patterns=["cdn.openai.com"],
        network_patterns=["api.openai.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="POVINNĚ označit jako AI systém. Uživatel musí vědět, "
                       "že komunikuje s umělou inteligencí.",
        description_cs="ChatGPT widget — AI chatbot od OpenAI přímo na webu.",
    ),

    # ── GOOGLE AI / GEMINI ──

    AISignature(
        name="Google Gemini Chatbot",
        category="chatbot",
        signatures=["gemini_proxy", "geminiProxyUrl", "gemini-proxy",
                     "generativelanguage.googleapis.com",
                     "aistudio.google.com", "ai.google.dev"],
        script_patterns=["generativelanguage.googleapis.com"],
        network_patterns=["generativelanguage.googleapis.com",
                          "gemini_proxy", "gemini-proxy", "gemini-api"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="AI chatbot poháněný Google Gemini musí být transparentně "
                       "označen. Uživatel musí vědět, že komunikuje s AI.",
        description_cs="Google Gemini — AI chatbot využívající Google Gemini API.",
    ),

    AISignature(
        name="Google Dialogflow",
        category="chatbot",
        signatures=["dialogflow", "dialogflow.cloud.google.com",
                     "df-messenger", "df-chat"],
        script_patterns=["dialogflow.cloud.google.com", "dialogflow.googleapis.com"],
        network_patterns=["dialogflow.googleapis.com", "dialogflow.cloud.google.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Dialogflow chatbot musí být označen jako AI systém.",
        description_cs="Google Dialogflow — konverzační AI platforma od Google.",
    ),

    AISignature(
        name="Google Vertex AI",
        category="chatbot",
        signatures=["vertex-ai", "vertexai", "aiplatform.googleapis.com"],
        script_patterns=["aiplatform.googleapis.com"],
        network_patterns=["aiplatform.googleapis.com", "vertexai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Vertex AI systém musí být transparentně označen.",
        description_cs="Google Vertex AI — enterprise AI platforma od Google.",
    ),

    # ── DALŠÍ CHATBOT PLATFORMY ──

    AISignature(
        name="Tawk.to",
        category="chatbot",
        signatures=["tawk.to", "Tawk_API", "tawkto"],
        script_patterns=["embed.tawk.to", "tawk.to"],
        cookie_patterns=["tawkUUID", "TawkConnection"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Pokud Tawk.to používá AI odpovědi, musí být označen.",
        description_cs="Tawk.to — chatbot platforma s AI asistencí.",
    ),

    AISignature(
        name="Voiceflow",
        category="chatbot",
        signatures=["voiceflow", "vf-widget", "voiceflow.com"],
        script_patterns=["cdn.voiceflow.com", "general-runtime.voiceflow.com"],
        network_patterns=["general-runtime.voiceflow.com", "voiceflow.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Voiceflow AI chatbot musí být transparentně označen.",
        description_cs="Voiceflow — AI chatbot builder s GPT integrací.",
    ),

    AISignature(
        name="Botpress",
        category="chatbot",
        signatures=["botpress", "bp-widget"],
        script_patterns=["cdn.botpress.cloud", "mediafiles.botpress.cloud"],
        network_patterns=["chat.botpress.cloud", "api.botpress.cloud"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Botpress AI chatbot musí být označen jako AI systém.",
        description_cs="Botpress — open-source AI chatbot platforma.",
    ),

    AISignature(
        name="ManyChat",
        category="chatbot",
        signatures=["manychat", "mcWidget"],
        script_patterns=["widget.manychat.com"],
        network_patterns=["manychat.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="ManyChat s AI odpověďmi musí být označen.",
        description_cs="ManyChat — chatbot platforma pro marketing s AI.",
    ),

    AISignature(
        name="Ada Support",
        category="chatbot",
        signatures=["ada-embed", "adaReadyCallback", "ada.cx"],
        script_patterns=["static.ada.support", "ada.cx"],
        network_patterns=["ada.support", "ada.cx"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Ada AI chatbot musí být transparentně označen.",
        description_cs="Ada — AI customer support chatbot.",
    ),

    AISignature(
        name="Amazon Lex",
        category="chatbot",
        signatures=["amazon-lex", "aws-lex", "LexRuntime"],
        script_patterns=["sdk.amazonaws.com"],
        network_patterns=["runtime.lex.", "models.lex."],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Amazon Lex chatbot musí být označen jako AI systém.",
        description_cs="Amazon Lex — konverzační AI od AWS.",
    ),

    AISignature(
        name="IBM Watson Assistant",
        category="chatbot",
        signatures=["watson-assistant", "watsonAssistant", "WatsonAssistantChat"],
        script_patterns=["web-chat.global.assistant.watson"],
        network_patterns=["api.au-syd.assistant.watson", "assistant.watson.cloud.ibm.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="IBM Watson chatbot musí být transparentně označen.",
        description_cs="IBM Watson Assistant — enterprise AI chatbot.",
    ),

    AISignature(
        name="Freshdesk/Freshchat",
        category="chatbot",
        signatures=["freshchat", "freshdesk", "fcWidget"],
        script_patterns=["wchat.freshchat.com", "freshdesk.com"],
        cookie_patterns=["freshchat"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Freshchat AI bot musí být označen.",
        description_cs="Freshdesk/Freshchat — zákaznická podpora s AI chatbotem Freddy.",
    ),

    AISignature(
        name="Landbot",
        category="chatbot",
        signatures=["landbot", "mylandbot"],
        script_patterns=["cdn.landbot.io", "landbot.io"],
        network_patterns=["api.landbot.io"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Landbot s AI musí být označen jako AI systém.",
        description_cs="Landbot — no-code chatbot builder s AI.",
    ),

    AISignature(
        name="Chatbase",
        category="chatbot",
        signatures=["chatbase", "chatbase.co"],
        script_patterns=["chatbase.co", "www.chatbase.co"],
        network_patterns=["chatbase.co"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Chatbase AI chatbot musí být transparentně označen.",
        description_cs="Chatbase — custom GPT chatbot pro weby.",
    ),

    # ── OPENAI / ANTHROPIC API (přímé volání z frontendu) ──

    AISignature(
        name="OpenAI API (frontend)",
        category="chatbot",
        signatures=["api.openai.com/v1", "openai.com/v1/chat"],
        network_patterns=["api.openai.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přímé volání OpenAI API z frontendu — AI systém musí "
                       "být transparentně označen. Zvažte bezpečnost API klíčů.",
        description_cs="Přímé volání OpenAI API — chatbot nebo AI funkce na webu.",
    ),

    AISignature(
        name="Anthropic Claude API (frontend)",
        category="chatbot",
        signatures=["api.anthropic.com", "anthropic.com/v1"],
        network_patterns=["api.anthropic.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Přímé volání Anthropic API — AI systém musí být označen.",
        description_cs="Přímé volání Anthropic Claude API — AI chatbot na webu.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ANALYTIKA s AI (čl. 50 + čl. 26)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    AISignature(
        name="TikTok Pixel",
        category="analytics",
        signatures=["ttq.load", "tiktok.com/i18n/pixel"],
        script_patterns=["analytics.tiktok.com"],
        cookie_patterns=["_ttp"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 4, čl. 26",
        action_required="TikTok Pixel používá AI pro cílení — přidejte do cookie banneru.",
        description_cs="TikTok Pixel — sledování konverzí s AI cílením reklam.",
    ),

    AISignature(
        name="LinkedIn Insight Tag",
        category="analytics",
        signatures=["_linkedin_partner_id", "snap.licdn.com"],
        script_patterns=["snap.licdn.com"],
        cookie_patterns=["li_sugr", "bcookie"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 4",
        action_required="LinkedIn Insight Tag s AI cílením — přidejte do cookie banneru.",
        description_cs="LinkedIn Insight Tag — B2B analytika s AI cílením reklam.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI DOPORUČOVACÍ SYSTÉMY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    AISignature(
        name="Nosto",
        category="recommender",
        signatures=["nosto", "nostojs"],
        script_patterns=["connect.nosto.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Nosto AI personalizace — informujte zákazníky.",
        description_cs="Nosto — AI personalizace pro e-commerce.",
    ),

    AISignature(
        name="Dynamic Yield",
        category="recommender",
        signatures=["dynamicyield", "dy-", "DYID"],
        script_patterns=["cdn.dynamicyield.com", "px.dynamicyield.com"],
        cookie_patterns=["_dy"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1, čl. 26",
        action_required="Dynamic Yield AI personalizace vyžaduje transparenci.",
        description_cs="Dynamic Yield — AI personalizace a A/B testování.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI CONTENT GENERATION (čl. 50/2)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ČESKÁ / REGIONÁLNÍ SPECIFIKA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERICKÉ DETEKCE (fallback)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="Generický AI chatbot",
        category="chatbot",
        signatures=["ai-chatbot", "ai_chatbot", "chatbot-ai", "virtual-assistant",
                     "ai-assistant", "ai_assistant"],
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
