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
        signatures=["driftt", "drift.com", "js.driftt.com", "drift-frame"],
        script_patterns=["drift.com", "js.driftt.com"],
        cookie_patterns=["driftt_"],
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
    # ANALYTIKA s AI
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="Google Analytics 4",
        category="analytics",
        signatures=["gtag(", "google-analytics", "analytics.js", "GA4"],
        script_patterns=["googletagmanager.com/gtag", "google-analytics.com"],
        cookie_patterns=["_ga", "_gid"],
        risk_level="minimal",
        ai_act_article="minimální riziko (čl. 95 — dobrovolné kodexy)",
        action_required="GA4 samo o sobě není AI systém dle EU AI Act. "
                       "Pokud používáte Predictive Audiences, zvažte transparentnost vůči uživatelům.",
        description_cs="Google Analytics 4 — webová analytika s volitelnými AI predikcemi.",
    ),

    AISignature(
        name="Google Tag Manager",
        category="analytics",
        signatures=["GTM-", "googletagmanager"],
        script_patterns=["googletagmanager.com/gtm.js"],
        risk_level="minimal",
        ai_act_article="minimální riziko (čl. 95 — dobrovolné kodexy)",
        action_required="GTM není AI systém — je to správce tagů. "
                       "Zkontrolujte, zda některé tagy nezavádějí AI systémy.",
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
        ai_act_article="čl. 4 (gramotnost v oblasti AI)",
        action_required="Meta provádí AI cílení reklam na své straně. "
                       "Informujte uživatele v cookie banneru a privacy policy.",
        description_cs="Meta Pixel — sledování konverzí, AI cílení provádí Meta na své platformě.",
    ),

    AISignature(
        name="TikTok Pixel",
        category="analytics",
        signatures=["ttq.load", "tiktok.com/i18n/pixel"],
        script_patterns=["analytics.tiktok.com"],
        cookie_patterns=["_ttp"],
        risk_level="limited",
        ai_act_article="čl. 4 (gramotnost v oblasti AI)",
        action_required="TikTok provádí AI cílení reklam na své straně. "
                       "Informujte uživatele v cookie banneru a privacy policy.",
        description_cs="TikTok Pixel — sledování konverzí, AI cílení provádí TikTok na své platformě.",
    ),

    AISignature(
        name="LinkedIn Insight Tag",
        category="analytics",
        signatures=["_linkedin_partner_id", "snap.licdn.com"],
        script_patterns=["snap.licdn.com"],
        cookie_patterns=["li_sugr", "bcookie"],
        risk_level="limited",
        ai_act_article="čl. 4 (gramotnost v oblasti AI)",
        action_required="LinkedIn provádí AI cílení reklam na své straně. "
                       "Informujte uživatele v cookie banneru a privacy policy.",
        description_cs="LinkedIn Insight Tag — B2B analytika, AI cílení provádí LinkedIn na své platformě.",
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
        signatures=["shoptet-ai", "shoptetAiRecommend", "shoptet-personalization"],
        script_patterns=["cdn.myshoptet.com/ai", "cdn.myshoptet.com/recommender"],
        cookie_patterns=["shoptet_ai"],
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
        ai_act_article="minimální riziko (čl. 95 — dobrovolné kodexy)",
        action_required="Seznam retargeting — přidejte do cookie banneru. "
                       "AI cílení provádí Seznam na své straně.",
        description_cs="Seznam — český vyhledávač s retargetingem.",
    ),

    AISignature(
        name="Heureka",
        category="analytics",
        signatures=["heureka", "heureka.cz"],
        script_patterns=["im9.cz", "heureka.cz"],
        risk_level="minimal",
        ai_act_article="minimální riziko (čl. 95 — dobrovolné kodexy)",
        action_required="Heureka měření konverzí — přidejte do cookie banneru.",
        description_cs="Heureka — měření konverzí a recenze.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DALŠÍ CHATBOTY (rozšířeno)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="JivoChat",
        category="chatbot",
        signatures=["jivosite", "jivo-", "jivochat", "JivoSite"],
        script_patterns=["code.jivosite.com", "jivo.chat"],
        cookie_patterns=["jv_"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="JivoChat s AI odpověďmi musí být označen.",
        description_cs="JivoChat (JivoSite) — chatbot s AI asistencí.",
    ),

    AISignature(
        name="Chatra",
        category="chatbot",
        signatures=["chatra", "ChatraID", "ChatraSetup"],
        script_patterns=["call.chatra.io"],
        cookie_patterns=["chatra"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Chatra chatbot s AI musí být označen.",
        description_cs="Chatra — live chat a chatbot s AI funkcemi.",
    ),

    AISignature(
        name="Olark",
        category="chatbot",
        signatures=["olark", "olarkIdentify", "olark.configure"],
        script_patterns=["static.olark.com"],
        cookie_patterns=["olark"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Olark chatbot s AI musí být označen.",
        description_cs="Olark — live chat s AI CoPilot funkcemi.",
    ),

    AISignature(
        name="LivePerson",
        category="chatbot",
        signatures=["liveperson", "lpTag", "LivePerson"],
        script_patterns=["lptag.liveperson.net", "lpcdn.lpsnmedia.net"],
        cookie_patterns=["LivePerson"],
        network_patterns=["lptag.liveperson.net"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="LivePerson AI chatbot musí být transparentně označen.",
        description_cs="LivePerson — enterprise AI konverzační platforma.",
    ),

    AISignature(
        name="Gorgias",
        category="chatbot",
        signatures=["gorgias", "gorgias-chat"],
        script_patterns=["config.gorgias.chat", "gorgias.chat"],
        network_patterns=["gorgias.chat"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Gorgias AI chatbot musí být označen.",
        description_cs="Gorgias — AI helpdesk pro e-commerce.",
    ),

    AISignature(
        name="Re:amaze",
        category="chatbot",
        signatures=["reamaze", "re:amaze", "reAmaze"],
        script_patterns=["d2sh4fq2xsdeg9.cloudfront.net"],
        network_patterns=["reamaze.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Re:amaze AI chatbot musí být označen.",
        description_cs="Re:amaze — helpdesk s AI chatbotem pro e-commerce.",
    ),

    AISignature(
        name="Typebot",
        category="chatbot",
        signatures=["typebot", "typebot.io"],
        script_patterns=["cdn.jsdelivr.net/npm/@typebot.io", "typebot.io"],
        network_patterns=["typebot.io"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Typebot s AI odpověďmi musí být označen.",
        description_cs="Typebot — open-source chatbot builder s AI integrací.",
    ),

    AISignature(
        name="Kommunicate",
        category="chatbot",
        signatures=["kommunicate", "applozic"],
        script_patterns=["widget.kommunicate.io"],
        network_patterns=["api.kommunicate.io"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Kommunicate AI chatbot musí být označen.",
        description_cs="Kommunicate — AI chatbot platforma s GPT integrací.",
    ),

    AISignature(
        name="CustomGPT",
        category="chatbot",
        signatures=["customgpt", "custom-gpt"],
        script_patterns=["cdn.customgpt.ai"],
        network_patterns=["app.customgpt.ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="CustomGPT chatbot musí být transparentně označen jako AI.",
        description_cs="CustomGPT — vlastní AI chatbot trénovaný na firemních datech.",
    ),

    AISignature(
        name="YourGPT",
        category="chatbot",
        signatures=["yourgpt", "your-gpt"],
        script_patterns=["widget.yourgpt.ai"],
        network_patterns=["yourgpt.ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="YourGPT chatbot musí být označen jako AI systém.",
        description_cs="YourGPT — no-code AI chatbot builder.",
    ),

    AISignature(
        name="Zapier Chatbot",
        category="chatbot",
        signatures=["zapier-interfaces", "zap-chat", "interfaces.zapier.com"],
        script_patterns=["interfaces.zapier.com"],
        network_patterns=["interfaces.zapier.com", "nla.zapier.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Zapier AI chatbot musí být označen.",
        description_cs="Zapier AI Chatbot — automatizovaný AI agent na webu.",
    ),

    AISignature(
        name="Userlike",
        category="chatbot",
        signatures=["userlike", "userlikeReady"],
        script_patterns=["userlike-cdn-widgets.s3-eu-west-1.amazonaws.com"],
        cookie_patterns=["uslk_"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Userlike AI chatbot musí být označen.",
        description_cs="Userlike — live chat s AI automatizací.",
    ),

    AISignature(
        name="Help Scout Beacon",
        category="chatbot",
        signatures=["helpscout", "beacon-v2.helpscout", "HS.beacon"],
        script_patterns=["beacon-v2.helpscout.net"],
        network_patterns=["beaconapi.helpscout.net"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Help Scout AI Answers musí být označen.",
        description_cs="Help Scout Beacon — helpdesk s AI Answers.",
    ),

    AISignature(
        name="Chatwoot",
        category="chatbot",
        signatures=["chatwoot", "chatwootSettings", "chatwootSDK"],
        script_patterns=["app.chatwoot.com"],
        network_patterns=["chatwoot.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Chatwoot AI odpovědi musí být označeny.",
        description_cs="Chatwoot — open-source zákaznická podpora s AI.",
    ),

    AISignature(
        name="Vercel AI Chatbot",
        category="chatbot",
        signatures=["@ai-sdk/react", "sdk.vercel.ai", "vercel-ai-chatbot"],
        script_patterns=["sdk.vercel.ai"],
        network_patterns=["sdk.vercel.ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="AI chatbot postavený na Vercel AI SDK musí být označen.",
        description_cs="AI chatbot na bázi Vercel AI SDK.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI A/B TESTOVÁNÍ & PERSONALIZACE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="VWO (Visual Website Optimizer)",
        category="recommender",
        signatures=["vwo_", "VWO", "visualwebsiteoptimizer"],
        script_patterns=["dev.visualwebsiteoptimizer.com", "vwo.com"],
        cookie_patterns=["_vwo", "_vis_opt"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="VWO AI personalizace a prediktivní targeting vyžaduje transparenci.",
        description_cs="VWO — A/B testování s AI personalizací a prediktivním targetingem.",
    ),

    AISignature(
        name="Optimizely",
        category="recommender",
        signatures=["optimizely", "optimizelyEndUserId"],
        script_patterns=["cdn.optimizely.com", "logx.optimizely.com"],
        cookie_patterns=["optimizely"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Optimizely AI experimentace vyžaduje transparenci.",
        description_cs="Optimizely — AI experimentace a personalizace.",
    ),

    AISignature(
        name="AB Tasty",
        category="recommender",
        signatures=["abtasty", "ABTasty"],
        script_patterns=["try.abtasty.com", "abtasty.com"],
        cookie_patterns=["ABTasty"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="AB Tasty AI personalizace vyžaduje transparenci.",
        description_cs="AB Tasty — A/B testování s AI personalizací.",
    ),

    AISignature(
        name="Clerk.io",
        category="recommender",
        signatures=["clerk.io", "clerkjs", "Clerk("],
        script_patterns=["cdn.clerk.io"],
        network_patterns=["api.clerk.io"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Clerk.io AI doporučování vyžaduje transparenci.",
        description_cs="Clerk.io — AI doporučovací engine pro e-commerce.",
    ),

    AISignature(
        name="Luigi's Box",
        category="recommender",
        signatures=["luigisbox", "luigi"],
        script_patterns=["scripts.luigisbox.com"],
        network_patterns=["live.luigisbox.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Luigi's Box AI vyhledávání vyžaduje transparenci.",
        description_cs="Luigi's Box — slovenský AI vyhledávač a doporučovač pro e-shopy.",
    ),

    AISignature(
        name="Bloomreach",
        category="recommender",
        signatures=["bloomreach", "exponea"],
        script_patterns=["cdn.exponea.com", "api.exponea.com"],
        cookie_patterns=["__exponea"],
        network_patterns=["api.exponea.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1, čl. 26",
        action_required="Bloomreach AI personalizace a predikce vyžaduje transparenci.",
        description_cs="Bloomreach (Exponea) — AI personalizace a prediktivní marketing.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI CONTENT & SEO NÁSTROJE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="Writesonic",
        category="content_gen",
        signatures=["writesonic", "writesonic.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generovaný obsah musí být označen.",
        description_cs="Writesonic — AI generování obsahu a chatbot Botsonic.",
    ),

    AISignature(
        name="Surfer SEO",
        category="content_gen",
        signatures=["surferseo", "surfer-seo", "surfer.ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generovaný obsah musí být označen.",
        description_cs="Surfer SEO — AI optimalizace a generování SEO obsahu.",
    ),

    AISignature(
        name="Frase.io",
        category="content_gen",
        signatures=["frase.io", "frase-answer", "frase-widget"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generovaný obsah musí být označen.",
        description_cs="Frase — AI výzkum a generování obsahu.",
    ),

    AISignature(
        name="MarketMuse",
        category="content_gen",
        signatures=["marketmuse", "market-muse"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generovaný obsah musí být označen.",
        description_cs="MarketMuse — AI plánování a optimalizace obsahu.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI PŘEKLAD & LOKALIZACE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="DeepL Translator",
        category="content_gen",
        signatures=["deepl", "deepl.com"],
        script_patterns=["static.deepl.com"],
        network_patterns=["api-free.deepl.com", "api.deepl.com"],
        risk_level="minimal",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI překlad by měl být označen.",
        description_cs="DeepL — AI překladač, pokud se obsah automaticky překládá.",
    ),

    AISignature(
        name="Weglot",
        category="content_gen",
        signatures=["weglot", "Weglot.initialize"],
        script_patterns=["cdn.weglot.com"],
        network_patterns=["api.weglot.com"],
        risk_level="minimal",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI překlad webu by měl být označen.",
        description_cs="Weglot — AI překlad a lokalizace webových stránek.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI OBRÁZKY & GENERATIVNÍ MEDIA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="DALL-E / OpenAI Images",
        category="content_gen",
        signatures=["dall-e", "dalle", "oaidalleapiprodscus"],
        network_patterns=["api.openai.com/v1/images"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generované obrázky musí být označeny jako vytvořené AI.",
        description_cs="DALL-E — AI generování obrázků od OpenAI.",
    ),

    AISignature(
        name="Midjourney",
        category="content_gen",
        signatures=["midjourney", "mj-"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generované obrázky musí být označeny.",
        description_cs="Midjourney — AI generování obrázků.",
    ),

    AISignature(
        name="Stable Diffusion",
        category="content_gen",
        signatures=["stable-diffusion", "stablediffusion", "stability.ai"],
        network_patterns=["api.stability.ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 2",
        action_required="AI generované obrázky musí být označeny.",
        description_cs="Stable Diffusion — open-source AI generování obrázků.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AI ZÁKAZNICKÝ SERVIS & TICKETING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="Salesforce Einstein",
        category="chatbot",
        signatures=["einstein", "salesforce-chat", "embeddedservice"],
        script_patterns=["service.force.com", "salesforce.com"],
        network_patterns=["salesforce.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Salesforce Einstein AI musí být transparentně označen.",
        description_cs="Salesforce Einstein — AI asistent v CRM a zákaznické podpoře.",
    ),

    AISignature(
        name="Kayako",
        category="chatbot",
        signatures=["kayako", "kayako.com"],
        script_patterns=["kayako.com"],
        network_patterns=["kayako.com"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Kayako AI odpovědi musí být označeny.",
        description_cs="Kayako — helpdesk s AI chatbotem.",
    ),

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERICKÉ DETEKCE (fallback)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    AISignature(
        name="Generický AI chatbot",
        category="chatbot",
        signatures=["data-ai-chatbot", "id=\"ai-chatbot\"", "class=\"ai-assistant\"",
                     "data-virtual-assistant"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="Jakýkoli AI chatbot musí být označen jako AI systém.",
        description_cs="Generický AI chatbot detekovaný na stránce.",
    ),

    AISignature(
        name="Generický AI API",
        category="chatbot",
        signatures=[],
        network_patterns=["huggingface.co/api", "api.replicate.com",
                         "api-inference.huggingface.co",
                         "api.cohere.ai", "api.mistral.ai",
                         "api.together.xyz", "api.perplexity.ai",
                         "api.groq.com", "api.fireworks.ai"],
        risk_level="limited",
        ai_act_article="čl. 50 odst. 1",
        action_required="AI API volání musí být transparentně identifikováno.",
        description_cs="Přímé volání AI API (Hugging Face, Replicate, Cohere, Mistral aj.).",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NON-AI TRACKERY A ANALYTIKA — nespadají pod AI Act, ale detekujeme je
# pro zvýšení důvěryhodnosti testu. Klient vidí, že skener odhalí vše.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class TrackerSignature:
    """Signatura non-AI sledovacího systému."""
    name: str
    category: str  # tracking, analytics, advertising, consent
    signatures: list[str]
    script_patterns: list[str] = field(default_factory=list)
    cookie_patterns: list[str] = field(default_factory=list)
    description_cs: str = ""
    icon: str = ""  # emoji for frontend


NON_AI_TRACKERS: list[TrackerSignature] = [

    # ── Google ──
    TrackerSignature(
        name="Google Tag Manager",
        category="tracking",
        signatures=["googletagmanager.com", "gtm.js", "GTM-"],
        script_patterns=["googletagmanager.com/gtm.js"],
        cookie_patterns=["_gtm"],
        description_cs="Správce tagů pro marketing a analytiku. Koordinuje ostatní sledovací skripty na webu.",
        icon="🏷️",
    ),
    TrackerSignature(
        name="Google Analytics 4",
        category="analytics",
        signatures=["gtag(", "google-analytics.com", "googletagmanager.com/gtag", "G-", "ga('"],
        script_patterns=["googletagmanager.com/gtag", "google-analytics.com/analytics.js"],
        cookie_patterns=["_ga", "_gid", "_gat"],
        description_cs="Webová analytika od Google — sleduje návštěvnost, chování uživatelů a konverze.",
        icon="📊",
    ),
    TrackerSignature(
        name="Google Ads (Conversion Tracking)",
        category="advertising",
        signatures=["googleads.g.doubleclick.net", "googlesyndication.com", "conversion.js", "AW-"],
        script_patterns=["googleads.g.doubleclick.net", "pagead2.googlesyndication.com"],
        cookie_patterns=["_gcl", "IDE", "DSID"],
        description_cs="Sledování konverzí pro Google Ads kampaně. Měří efektivitu reklam.",
        icon="📢",
    ),

    # ── Meta / Facebook ──
    TrackerSignature(
        name="Meta Pixel (Facebook)",
        category="advertising",
        signatures=["fbq(", "connect.facebook.net", "facebook.com/tr", "fb-pixel"],
        script_patterns=["connect.facebook.net/en_US/fbevents.js"],
        cookie_patterns=["_fbp", "_fbc"],
        description_cs="Sledovací pixel Facebooku — měří konverze z reklam na Facebooku a Instagramu.",
        icon="📘",
    ),

    # ── Microsoft ──
    TrackerSignature(
        name="Microsoft Clarity",
        category="analytics",
        signatures=["clarity.ms", "clarity("],
        script_patterns=["clarity.ms/tag"],
        cookie_patterns=["_clck", "_clsk"],
        description_cs="Heatmapy a záznamy relací od Microsoftu. Vizualizuje, jak uživatelé interagují se stránkou.",
        icon="🔍",
    ),

    # ── Hotjar ──
    TrackerSignature(
        name="Hotjar",
        category="analytics",
        signatures=["hotjar", "hj(", "hjSiteSettings"],
        script_patterns=["static.hotjar.com"],
        cookie_patterns=["_hj"],
        description_cs="Heatmapy, záznamy relací a zpětná vazba od návštěvníků.",
        icon="🔥",
    ),

    # ── Seznam.cz ──
    TrackerSignature(
        name="Seznam Sklik",
        category="advertising",
        signatures=["sklik.js", "c.imedia.cz", "im.imedia.cz"],
        script_patterns=["c.imedia.cz/js", "im.imedia.cz"],
        cookie_patterns=["szn"],
        description_cs="Reklamní systém Seznamu — sledování konverzí z kampaní na Seznam.cz.",
        icon="🔎",
    ),
    TrackerSignature(
        name="Seznam Retargeting",
        category="advertising",
        signatures=["sznRetargeting", "retargeting.seznam.cz"],
        script_patterns=["retargeting.seznam.cz"],
        description_cs="Retargetingový pixel Seznamu pro opakované oslovení návštěvníků.",
        icon="🔄",
    ),

    # ── Heureka ──
    TrackerSignature(
        name="Heureka Ověřeno zákazníky",
        category="tracking",
        signatures=["heureka.cz/direct", "overeno-zakazniky"],
        script_patterns=["heureka.cz"],
        description_cs="Systém sběru recenzí a ověření zákazníků od Heureky.",
        icon="⭐",
    ),

    # ── Cookie consent ──
    TrackerSignature(
        name="Cookiebot",
        category="consent",
        signatures=["cookiebot.com", "Cookiebot", "CookieConsent"],
        script_patterns=["consent.cookiebot.com"],
        cookie_patterns=["CookieConsent"],
        description_cs="Platforma pro správu souhlasu s cookies dle GDPR.",
        icon="🍪",
    ),
    TrackerSignature(
        name="Cookie Consent Banner",
        category="consent",
        signatures=["cookie-consent", "cookie-notice", "cookie-banner", "cookie-policy",
                     "gdpr-consent", "consent-banner"],
        description_cs="Obecný cookie consent banner pro správu souhlasu dle GDPR.",
        icon="🍪",
    ),

    # ── LinkedIn ──
    TrackerSignature(
        name="LinkedIn Insight Tag",
        category="advertising",
        signatures=["linkedin.com/px", "snap.licdn.com", "_linkedin_data_partner_id"],
        script_patterns=["snap.licdn.com/li.lms-analytics"],
        cookie_patterns=["li_sugr", "bcookie", "lidc"],
        description_cs="Sledovací tag LinkedIn pro B2B marketing a konverze z reklam.",
        icon="💼",
    ),

    # ── Twitter / X ──
    TrackerSignature(
        name="X (Twitter) Pixel",
        category="advertising",
        signatures=["twq(", "static.ads-twitter.com", "analytics.twitter.com"],
        script_patterns=["static.ads-twitter.com/uwt.js"],
        description_cs="Konverzní pixel platformy X (dříve Twitter) pro měření reklam.",
        icon="🐦",
    ),

    # ── TikTok ──
    TrackerSignature(
        name="TikTok Pixel",
        category="advertising",
        signatures=["ttq.load", "analytics.tiktok.com"],
        script_patterns=["analytics.tiktok.com"],
        description_cs="Sledovací pixel TikToku pro měření konverzí z reklam.",
        icon="🎵",
    ),

    # ── Ostatní ──
    TrackerSignature(
        name="Matomo (Piwik)",
        category="analytics",
        signatures=["matomo", "piwik", "_paq.push"],
        script_patterns=["matomo.js", "piwik.js"],
        cookie_patterns=["_pk_id", "_pk_ses"],
        description_cs="Open-source webová analytika — alternativa ke Google Analytics.",
        icon="📈",
    ),
    TrackerSignature(
        name="Zboží.cz",
        category="tracking",
        signatures=["zbozi.cz/conversion", "zboziKonverze"],
        script_patterns=["zbozi.cz"],
        description_cs="Konverzní měření pro srovnávač cen Zboží.cz od Seznamu.",
        icon="🛒",
    ),
]


def get_all_signatures() -> list[AISignature]:
    """Vrátí všechny signatury."""
    return AI_SIGNATURES


def get_signatures_by_category(category: str) -> list[AISignature]:
    """Vrátí signatury podle kategorie."""
    return [s for s in AI_SIGNATURES if s.category == category]


def get_all_trackers() -> list[TrackerSignature]:
    """Vrátí všechny non-AI tracker signatury."""
    return NON_AI_TRACKERS
