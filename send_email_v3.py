from backend.outbound.email_templates import get_outbound_email, FindingItem
from backend.outbound.email_engine import send_email

findings = [
    FindingItem(
        name='Google Gemini Chatbot',
        category='chatbot',
        risk_level='limited',
        ai_act_article='čl. 50 odst. 1',
        action_required='AI chatbot musí být transparentně označen.',
        description='AI chatbot poháněný Google Gemini přes vlastní proxy (gemini_proxy.php).',
    ),
    FindingItem(
        name='AI-generovaný obsah',
        category='content_gen',
        risk_level='limited',
        ai_act_article='čl. 50 odst. 2',
        action_required='AI generovaný obsah musí být označen.',
        description='Web otevřeně deklaruje: texty, grafika i chatbot jsou vytvořeny AI.',
    ),
    FindingItem(
        name='Meta Pixel (AI cílení)',
        category='analytics',
        risk_level='limited',
        ai_act_article='čl. 50 odst. 4, čl. 26',
        action_required='Přidat do cookie banneru.',
        description='AI cílení reklam, lookalike audience.',
    ),
    FindingItem(
        name='Google Tag Manager + GA4',
        category='analytics',
        risk_level='minimal',
        ai_act_article='čl. 50 odst. 4',
        action_required='Zkontrolovat AI tagy v kontejneru.',
        description='Analytika, potenciálně AI predikce.',
    ),
]

email = get_outbound_email(
    company_name='Desperados Design',
    company_url='desperados-design.cz',
    findings_count=6,
    top_finding='Na webu běží AI chatbot poháněný Google Gemini (přes gemini_proxy.php) bez transparenčního označení dle čl. 50 AI Act.',
    variant='A',
    to_email='info@desperados-design.cz',
    screenshot_url='https://rsxwqcrkttlfnqbjgpgc.supabase.co/storage/v1/object/public/screenshots/scans/d8d43f59-83dd-4cdd-bd9b-6d81819fd77d/viewport.png',
    findings=findings,
    scan_id='d8d43f59-83dd-4cdd-bd9b-6d81819fd77d',
)

result = send_email(
    to='info@desperados-design.cz',
    subject=email.subject,
    html=email.body_html,
)
print(f'Subject: {email.subject}')
print(f'Variant: {email.variant_id}')
print(f'Result: {result}')
