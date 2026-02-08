"""
AIshield.cz — Unsubscribe API
Veřejný endpoint pro odhlášení z emailových notifikací.
Povinné dle GDPR — musí fungovat jedním klikem.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from datetime import datetime
from backend.database import get_supabase

router = APIRouter()


@router.get("/unsubscribe")
async def unsubscribe_page(company: str = "", email: str = ""):
    """
    GET /api/unsubscribe?company=URL&email=EMAIL
    Zobrazí potvrzovací stránku — GDPR vyžaduje jednoduchost.
    """
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Odhlášení — AIshield.cz</title>
        <style>
            body {{
                font-family: -apple-system, sans-serif;
                background: #0f172a;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .card {{
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 40px;
                max-width: 500px;
                text-align: center;
            }}
            h1 {{ color: #e879f9; font-size: 24px; }}
            p {{ color: #94a3b8; line-height: 1.6; }}
            button {{
                background: #e879f9;
                color: #0f172a;
                border: none;
                padding: 12px 32px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 16px;
            }}
            button:hover {{ background: #d946ef; }}
            .done {{ color: #22d3ee; }}
        </style>
    </head>
    <body>
        <div class="card" id="card">
            <h1>Odhlášení z upozornění</h1>
            <p>Kliknutím na tlačítko se odhlásíte z emailových upozornění od AIshield.cz.</p>
            <p style="font-size: 14px;">Už vám nebudeme posílat žádné emaily.</p>
            <button onclick="doUnsubscribe()">Odhlásit se</button>
        </div>
        <script>
            async function doUnsubscribe() {{
                const res = await fetch('/api/unsubscribe', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        company: '{company}',
                        email: '{email}'
                    }})
                }});
                document.getElementById('card').innerHTML = `
                    <h1 class="done">✅ Odhlášeno</h1>
                    <p>Byli jste úspěšně odhlášeni. Už vám nebudeme posílat žádné emaily.</p>
                    <p style="font-size: 14px;">Omlouváme se za obtěžování.</p>
                `;
            }}
        </script>
    </body>
    </html>
    """)


@router.post("/unsubscribe")
async def unsubscribe_action(request: Request):
    """
    POST /api/unsubscribe — zpracuje odhlášení.
    Nastaví prospecting_status='unsubscribed' + přidá do blacklistu.
    """
    try:
        body = await request.json()
        company_url = body.get("company", "")
        email = body.get("email", "")
    except Exception:
        company_url = ""
        email = ""

    supabase = get_supabase()

    unsubscribed = False

    # Odhlásit podle URL
    if company_url:
        res = supabase.table("companies").update({
            "prospecting_status": "unsubscribed",
        }).eq("url", company_url).execute()
        if res.data:
            unsubscribed = True

    # Odhlásit podle emailu
    if email:
        res = supabase.table("companies").update({
            "prospecting_status": "unsubscribed",
        }).eq("email", email).execute()
        if res.data:
            unsubscribed = True

        # Přidat do blacklistu
        supabase.table("email_blacklist").upsert({
            "email": email.lower(),
            "reason": "user_unsubscribed",
            "created_at": datetime.utcnow().isoformat(),
        }, on_conflict="email").execute()

    # Zalogovat
    supabase.table("email_events").insert({
        "to_email": email or company_url,
        "event_type": "unsubscribe",
        "raw_data": {"company": company_url, "email": email},
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return {"unsubscribed": unsubscribed, "message": "Odhlášení provedeno"}
