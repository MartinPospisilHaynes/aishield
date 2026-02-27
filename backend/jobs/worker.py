"""
AIshield.cz — ARQ Worker & Job Queue
Asynchronní zpracování úloh: generování dokumentů, monitoring skeny,
email remindery. Běží jako samostatný systemd service.

Spuštění:  arq backend.jobs.worker.WorkerSettings
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from arq import cron, func
from arq.connections import RedisSettings

from backend.config import get_settings
from backend.database import get_supabase
from backend.jobs.deep_scan import deep_scan_job

logger = logging.getLogger(__name__)

# ── Redis settings ──
REDIS_SETTINGS = RedisSettings(host="localhost", port=6379, database=0)


# ═══════════════════════════════════════════════════════════════
# JOB 1: Generování Compliance Kitu (po zaplacení)
# ═══════════════════════════════════════════════════════════════

async def generate_compliance_kit_job(ctx: dict, client_id: str, order_id: str | None = None):
    """
    Background job: vygeneruje celý Compliance Kit pro klienta.
    Volané po potvrzení platby (Stripe webhook / admin).
    """
    logger.info(f"[JOB] Generování Compliance Kitu: client={client_id}, order={order_id}")
    supabase = get_supabase()

    try:
        # Update workflow status → "generating"
        if order_id:
            supabase.table("orders").update({
                "workflow_status": "generating",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", order_id).execute()

        # Spustit generování
        from backend.documents.pipeline import generate_compliance_kit
        result = await generate_compliance_kit(client_id)

        # Update workflow status → "awaiting_approval"
        # BEZPEČNOSTNÍ PRAVIDLO: Dokumenty se NEPOSÍLAJÍ klientovi automaticky.
        # Admin je musí nejdřív schválit v CRM (endpoint /crm/company/{id}/approve-docs).
        if order_id:
            supabase.table("orders").update({
                "workflow_status": "awaiting_approval",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", order_id).execute()

        # Notifikovat admina, že dokumenty čekají na schválení
        try:
            company = supabase.table("companies").select("name, email").eq(
                "id", client_id
            ).limit(1).execute()

            company_name = ""
            if company.data:
                company_name = company.data[0].get("name", "")

            from backend.outbound.email_engine import send_email
            await send_email(
                to="info@aishield.cz",
                subject=f"🔔 Dokumenty čekají na schválení — {company_name}",
                html=(
                    f"<p>Compliance Kit pro <strong>{company_name}</strong> "
                    f"(client_id: {client_id}) byl vygenerován.</p>"
                    f"<p>Dokumenty čekají na vaše schválení v CRM administraci.</p>"
                    f"<p><a href='https://aishield.cz/admin/crm'>Otevřít CRM →</a></p>"
                ),
                from_email="info@aishield.cz",
            )
            logger.info(f"[JOB] Admin notifikace odeslána — dokumenty čekají na schválení: {company_name}")
        except Exception as email_err:
            logger.warning(f"[JOB] Nepodařilo se odeslat admin notifikaci: {email_err}")

        logger.info(
            f"[JOB] Compliance Kit hotov: {result.success_count} OK, "
            f"{result.error_count} chyb"
        )
        return {"status": "ok", "documents": result.success_count, "errors": result.error_count}

    except Exception as e:
        logger.error(f"[JOB] CHYBA generování kitu: {e}", exc_info=True)

        # Update workflow status → "failed"
        if order_id:
            try:
                supabase.table("orders").update({
                    "workflow_status": "generation_failed",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", order_id).execute()
            except Exception:
                pass

        raise  # ARQ retry


# ═══════════════════════════════════════════════════════════════
# JOB 2: Monitoring rescan jednoho klienta
# ═══════════════════════════════════════════════════════════════

async def rescan_client_job(ctx: dict, company_id: str):
    """
    Background job: provede re-sken webu jednoho klienta,
    porovná s předchozím skenem a případně odešle alert.
    """
    logger.info(f"[JOB] Monitoring rescan: company={company_id}")
    supabase = get_supabase()

    try:
        # Načíst firmu
        company = supabase.table("companies").select("id, name, url, email").eq(
            "id", company_id
        ).limit(1).execute()

        if not company.data:
            logger.warning(f"[JOB] Firma {company_id} nenalezena")
            return {"status": "skipped", "reason": "company_not_found"}

        comp = company.data[0]
        url = comp.get("url", "")

        if not url:
            return {"status": "skipped", "reason": "no_url"}

        # Spustit sken
        from backend.scanner.web_scanner import scan_website
        scan_result = await scan_website(url, company_id=company_id)

        # Porovnat s předchozím
        scans = supabase.table("scans").select("id").eq(
            "company_id", company_id
        ).eq("status", "done").order("created_at", desc=True).limit(2).execute()

        if scans.data and len(scans.data) >= 2:
            from backend.monitoring.diff_engine import compare_scans
            diff = await compare_scans(scans.data[1]["id"], scans.data[0]["id"])

            if diff.has_changes:
                from backend.monitoring.alert_system import generate_alerts_from_diff
                from backend.monitoring.alert_system import send_alerts_from_diff
                alerts = generate_alerts_from_diff(diff, comp.get("email", ""))
                if alerts:
                    await send_alerts_from_diff(diff, comp.get("email", ""))
                    logger.info(f"[JOB] Odeslány alerty pro {comp['name']}: {len(alerts)}")

            # Update widget
            from backend.api.widget import auto_update_widget_after_scan
            await auto_update_widget_after_scan(company_id, scans.data[0]["id"])

        logger.info(f"[JOB] Rescan hotov: {comp['name']}")
        return {"status": "ok", "company": comp["name"]}

    except Exception as e:
        logger.error(f"[JOB] CHYBA rescan: {e}", exc_info=True)
        raise


# ═══════════════════════════════════════════════════════════════
# JOB 3: Email reminder (nevyplněný dotazník)
# ═══════════════════════════════════════════════════════════════

async def send_questionnaire_reminder_job(ctx: dict, company_id: str, email: str, day: int):
    """
    Pošle reminder email klientovi, který zaplatil ale nevyplnil dotazník.
    day: kolikátý den po zaplacení (1, 3, 7).
    """
    logger.info(f"[JOB] Questionnaire reminder D+{day}: {email}")

    try:
        from backend.outbound.reminder_emails import build_questionnaire_reminder_email
        from backend.outbound.email_engine import send_email

        html = build_questionnaire_reminder_email(email, company_id, day)

        subject_map = {
            1: "📋 Vyplňte dotazník — ještě dnes dokončíme vaši dokumentaci",
            3: "⏰ Připomínka: Dotazník čeká na vyplnění",
            7: "💡 Rádi vám pomůžeme s dotazníkem — jsme tu pro vás",
        }

        await send_email(
            to=email,
            subject=subject_map.get(day, "📋 Vyplňte dotazník pro AIshield.cz"),
            html=html,
            from_email="ahoj@aishield.cz",
        )
        logger.info(f"[JOB] Reminder D+{day} odeslán: {email}")
        return {"status": "sent", "day": day}

    except Exception as e:
        logger.error(f"[JOB] CHYBA reminder: {e}", exc_info=True)
        raise


# ═══════════════════════════════════════════════════════════════
# CRON: Měsíční monitoring (všichni platící klienti)
# ═══════════════════════════════════════════════════════════════

async def monthly_monitoring_cron(ctx: dict):
    """
    Cron job: 1× denně ve 03:00.
    Spouští PLNÉ 24h deep scany pro monitoring klienty.
    Monitoring: 1× měsíčně, Monitoring Plus: 2× měsíčně.
    Enterprise: 1× měsíčně (2 roky v ceně).
    Rozloží skeny po dnech podle hash(company_id).
    """
    logger.info("[CRON] Spouštím monitoring deep scan check")
    supabase = get_supabase()

    try:
        today = datetime.now(timezone.utc).date()
        queued = 0

        from arq import create_pool
        from backend.payments.subscription_manager import (
            get_active_monitoring_subscriptions,
            get_enterprise_monitoring_clients,
            get_scan_days_for_plan,
            check_enterprise_expiry,
            check_overdue_subscriptions,
        )

        redis = await create_pool(REDIS_SETTINGS)

        # ── 1. Aktivní monitoring subscriptions ──
        subs = await get_active_monitoring_subscriptions()
        for sub in subs:
            company_id = sub.get("company_id")
            if not company_id:
                continue

            plan = sub.get("plan", "monitoring")
            scan_days = get_scan_days_for_plan(company_id, plan)

            if today.day not in scan_days:
                continue

            # Najít URL firmy
            company = supabase.table("companies").select("url").eq(
                "id", company_id
            ).limit(1).execute()
            if not company.data or not company.data[0].get("url"):
                continue

            url = company.data[0]["url"]

            # Vytvořit scan record
            import uuid
            scan_id = str(uuid.uuid4())
            supabase.table("scans").insert({
                "id": scan_id,
                "company_id": company_id,
                "url": url,
                "status": "pending",
                "scan_type": "monitoring_deep",
                "subscription_id": sub["id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

            # Enqueue DEEP scan (ne quick rescan!)
            await redis.enqueue_job(
                "deep_scan_job",
                scan_id, url, company_id,
                _job_id=f"monitoring_deep_{company_id}_{today.isoformat()}",
            )

            # Update subscription scan count
            scans_done = (sub.get("scans_this_period") or 0) + 1
            supabase.table("subscriptions").update({
                "scans_this_period": scans_done,
                "last_scan_id": scan_id,
                "next_scan_at": None,  # Bude nastaveno po dokončení
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", sub["id"]).execute()

            queued += 1
            logger.info(f"[CRON] Deep scan queued: {company_id} (plan={plan}, scan={scan_id})")

        # ── 2. Enterprise klienti (monitoring v ceně, 2 roky) ──
        enterprise = await get_enterprise_monitoring_clients()
        for order in enterprise:
            company_id = order.get("company_id")
            if not company_id:
                continue

            # Enterprise = 1× měsíčně
            scan_days = get_scan_days_for_plan(company_id, "monitoring")
            if today.day not in scan_days:
                continue

            company = supabase.table("companies").select("url").eq(
                "id", company_id
            ).limit(1).execute()
            if not company.data or not company.data[0].get("url"):
                continue

            url = company.data[0]["url"]
            import uuid
            scan_id = str(uuid.uuid4())
            supabase.table("scans").insert({
                "id": scan_id,
                "company_id": company_id,
                "url": url,
                "status": "pending",
                "scan_type": "enterprise_monitoring",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

            await redis.enqueue_job(
                "deep_scan_job",
                scan_id, url, company_id,
                _job_id=f"enterprise_deep_{company_id}_{today.isoformat()}",
            )
            queued += 1
            logger.info(f"[CRON] Enterprise deep scan queued: {company_id}")

        await redis.close()

        # ── 3. Kontrola expirovaných Enterprise (2 roky) ──
        expired_count = await check_enterprise_expiry()
        if expired_count:
            logger.info(f"[CRON] Notified {expired_count} expired Enterprise clients")

        # ── 4. Kontrola neplateb FIO monitoring ──
        await check_overdue_subscriptions()

        logger.info(f"[CRON] Naplánováno {queued} monitoring deep skenů")
        return {"status": "ok", "queued": queued}

    except Exception as e:
        logger.error(f"[CRON] CHYBA monitoring: {e}", exc_info=True)
        raise


# ═══════════════════════════════════════════════════════════════
# CRON: Reminder checker (každý den v 9:00)
# ═══════════════════════════════════════════════════════════════

async def questionnaire_reminder_cron(ctx: dict):
    """
    Cron job: Každý den v 9:00 — zkontroluje, kdo zaplatil
    ale nevyplnil dotazník, a pošle reminder (D+1, D+3, D+7).
    """
    logger.info("[CRON] Kontroluji nevyplněné dotazníky")
    supabase = get_supabase()

    try:
        # Zaplacené objednávky
        orders = supabase.table("orders").select(
            "id, user_email, company_id, created_at"
        ).eq("status", "paid").execute()

        if not orders.data:
            return {"status": "ok", "reminders": 0}

        from arq import create_pool
        redis = await create_pool(REDIS_SETTINGS)
        reminders_sent = 0

        for order in orders.data:
            company_id = order.get("company_id")
            email = order.get("user_email")
            if not company_id or not email:
                continue

            # Má dotazník?
            questionnaire = supabase.table("questionnaire_responses").select(
                "id"
            ).eq("company_id", company_id).limit(1).execute()

            if questionnaire.data:
                continue  # Má vyplněný dotazník → přeskočit

            # Kolik dní od objednávky?
            created = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
            days_since = (datetime.now(timezone.utc) - created).days

            # Odeslat reminder jen v konkrétní dny
            reminder_day = None
            if days_since == 1:
                reminder_day = 1
            elif days_since == 3:
                reminder_day = 3
            elif days_since == 7:
                reminder_day = 7

            if reminder_day:
                await redis.enqueue_job(
                    "send_questionnaire_reminder_job",
                    company_id,
                    email,
                    reminder_day,
                    _job_id=f"reminder_{company_id}_d{reminder_day}",
                )
                reminders_sent += 1

        await redis.close()
        logger.info(f"[CRON] Naplánováno {reminders_sent} reminderů")
        return {"status": "ok", "reminders": reminders_sent}

    except Exception as e:
        logger.error(f"[CRON] CHYBA reminder check: {e}", exc_info=True)
        raise

# ═══════════════════════════════════════════════════════════════
# JOB: Monitoring post-scan — diff, alert, selective regen (P6)
# ═══════════════════════════════════════════════════════════════

async def monitoring_post_scan_job(ctx: dict, scan_id: str, company_id: str, subscription_id: str = ""):
    """
    Po dokončení monitoring deep scanu:
    1. Porovná s předchozím skenem (diff)
    2. Pokud jsou změny → alert email + admin notifikace
    3. Selektivní regenerace POUZE dotčených dokumentů
    4. Admin schvaluje a posílá klientovi
    """
    logger.info(f"[JOB] Monitoring post-scan: scan={scan_id}, company={company_id}")
    supabase = get_supabase()

    try:
        # Načíst firmu
        company = supabase.table("companies").select("id, name, url, email").eq(
            "id", company_id
        ).limit(1).execute()

        if not company.data:
            logger.warning(f"[PostScan] Company not found: {company_id}")
            return {"status": "skipped"}

        comp = company.data[0]
        email = comp.get("email", "")
        company_name = comp.get("name", "")

        # Najít předchozí scan (ne tento)
        scans = supabase.table("scans").select("id, created_at").eq(
            "company_id", company_id
        ).eq("status", "done").order("created_at", desc=True).limit(5).execute()

        previous_scan_id = None
        if scans.data:
            for s in scans.data:
                if s["id"] != scan_id:
                    previous_scan_id = s["id"]
                    break

        has_changes = False
        diff = None
        diff_summary = ""

        if previous_scan_id:
            from backend.monitoring.diff_engine import compare_scans
            diff = await compare_scans(previous_scan_id, scan_id)
            has_changes = diff.has_changes

            if has_changes:
                diff_summary = (
                    f"Přidáno: {len(diff.added)}, "
                    f"Odebráno: {len(diff.removed)}, "
                    f"Změněno: {len(diff.changed)}, "
                    f"Beze změny: {len(diff.unchanged)}"
                )
                logger.info(f"[PostScan] CHANGES detected for {company_name}: {diff_summary}")

                # ── Alert email klientovi ──
                from backend.monitoring.alert_system import send_alerts_from_diff
                await send_alerts_from_diff(diff, email)

                # ── Admin CRM task ──
                from backend.outbound.email_engine import send_email

                # Determine which documents need regeneration
                affected_docs = _determine_affected_documents(diff)

                admin_html = f"""
                <div style="font-family:system-ui;max-width:600px;padding:20px;">
                    <h2>🔄 Monitoring změna: {company_name}</h2>
                    <p><strong>Diff:</strong> {diff_summary}</p>
                    <p><strong>Scan ID:</strong> {scan_id}</p>

                    <h3>Přidané AI systémy:</h3>
                    <ul>{"".join(f"<li>{c.finding_name} ({c.risk_level})</li>" for c in diff.added) if diff.added else "<li>žádné</li>"}</ul>

                    <h3>Odebrané AI systémy:</h3>
                    <ul>{"".join(f"<li>{c.finding_name}</li>" for c in diff.removed) if diff.removed else "<li>žádné</li>"}</ul>

                    <h3>Změněné:</h3>
                    <ul>{"".join(f"<li>{c.finding_name}: {c.details}</li>" for c in diff.changed) if diff.changed else "<li>žádné</li>"}</ul>

                    <h3>Dotčené dokumenty k regeneraci:</h3>
                    <ul>{"".join(f"<li>{d}</li>" for d in affected_docs)}</ul>

                    <p style="margin-top:20px;">
                        <strong>Akce:</strong> Dokumenty čekají na vaše schválení v CRM.<br>
                        <a href="https://aishield.cz/admin/crm">Otevřít CRM →</a>
                    </p>
                </div>
                """

                await send_email(
                    to="info@aishield.cz",
                    subject=f"🔄 [MONITORING ZMĚNA] {company_name} — {len(diff.added)} přidáno, {len(diff.removed)} odebráno",
                    html=admin_html,
                    from_email="info@aishield.cz",
                    from_name="AIshield.cz Monitoring",
                )

                # ── Selective document regeneration ──
                if affected_docs:
                    try:
                        # Enqueue selective regen (only affected docs)
                        from backend.jobs.enqueue import enqueue_job
                        await enqueue_job(
                            "selective_regen_job",
                            company_id,
                            affected_docs,
                            scan_id,
                            _job_id=f"regen_{company_id}_{scan_id[:8]}",
                        )
                        logger.info(f"[PostScan] Selective regen enqueued: {affected_docs}")
                    except Exception as e:
                        logger.error(f"[PostScan] Failed to enqueue regen: {e}")

                # Check if Monitoring Plus → need to create CRM task for implementation
                if subscription_id:
                    sub = supabase.table("subscriptions").select("plan").eq(
                        "id", subscription_id
                    ).limit(1).execute()
                    if sub.data and sub.data[0].get("plan") == "monitoring_plus":
                        # Create admin task for web implementation
                        await send_email(
                            to="info@aishield.cz",
                            subject=f"🔧 [MONITORING PLUS TASK] {company_name} — implementace změn na webu",
                            html=f"""
                            <div style="font-family:system-ui;padding:20px;">
                                <h2>Monitoring Plus — implementace změn</h2>
                                <p>Klient <strong>{company_name}</strong> ({email}) má Monitoring Plus.</p>
                                <p>Na webu byly detekovány změny. Je třeba:</p>
                                <ol>
                                    <li>Zkontrolovat nové dokumenty po regeneraci</li>
                                    <li>Implementovat změny na webu klienta</li>
                                    <li>Aktualizovat transparenční stránku</li>
                                </ol>
                                <p><a href="https://aishield.cz/admin/crm">Otevřít CRM →</a></p>
                            </div>
                            """,
                            from_email="info@aishield.cz",
                        )
                        logger.info(f"[PostScan] Monitoring Plus task created for {company_name}")

            else:
                # Žádné změny
                logger.info(f"[PostScan] No changes for {company_name}")
                from backend.outbound.email_engine import send_email
                await send_email(
                    to=email,
                    subject=f"AIshield.cz — Měsíční monitoring: žádné změny ✅",
                    html=f"""
                    <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:24px;">
                        <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:32px;border-radius:16px;color:#f1f5f9;">
                            <h1 style="color:#22c55e;margin:0 0 8px;">✅ Žádné změny</h1>
                            <p style="color:#cbd5e1;">
                                Hloubkový monitoring sken webu <strong>{comp.get('url', '')}</strong>
                                pro firmu <strong>{company_name}</strong> proběhl úspěšně.
                            </p>
                            <p style="color:#94a3b8;">
                                Na vašem webu nebyly detekovány žádné nové AI systémy
                                ani změny oproti předchozímu skenu. Vaše compliance dokumentace
                                zůstává aktuální.
                            </p>
                            <p style="color:#64748b;font-size:12px;margin-top:20px;">
                                Další sken proběhne v příštím období dle vašeho monitorovacího plánu.
                            </p>
                        </div>
                    </div>
                    """,
                    from_email="info@aishield.cz",
                    from_name="AIshield.cz",
                )

        # Aktualizovat subscription
        if subscription_id:
            supabase.table("subscriptions").update({
                "last_diff_has_changes": has_changes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", subscription_id).execute()

        return {"status": "ok", "has_changes": has_changes, "diff_summary": diff_summary}

    except Exception as e:
        logger.error(f"[PostScan] Error: {e}", exc_info=True)
        raise


def _determine_affected_documents(diff) -> list[str]:
    """
    Určí, které dokumenty potřebují regeneraci na základě diffu.
    Vrací seznam doc_type identifikátorů.
    """
    affected = set()

    for change in (diff.added + diff.removed + diff.changed):
        risk = change.risk_level.lower() if change.risk_level else ""
        category = change.category.lower() if change.category else ""

        # Compliance Report — vždy při jakékoliv změně
        affected.add("compliance_report")

        # Registr AI systémů — vždy
        affected.add("ai_registry")

        # Transparenční stránka — vždy při added/removed
        if change.change_type in ("added", "removed"):
            affected.add("transparency_page")
            affected.add("notification_texts")

        # High-risk → DPIA, monitoring plán
        if risk in ("high", "unacceptable"):
            affected.add("dpia")
            affected.add("monitoring_plan")
            affected.add("transparency_oversight")

        # Chatbot/doporučení → notification texts
        if any(kw in category for kw in ("chatbot", "recommendation", "conversational")):
            affected.add("notification_texts")

    return sorted(affected)


async def selective_regen_job(ctx: dict, company_id: str, doc_types: list[str], scan_id: str = ""):
    """
    Selektivní regenerace POUZE dotčených dokumentů.
    Výsledek čeká na schválení adminem (NEPOSÍLÁ se automaticky klientovi).
    """
    logger.info(f"[JOB] Selective regen: company={company_id}, docs={doc_types}")
    supabase = get_supabase()

    try:
        from backend.documents.pipeline import generate_compliance_kit

        # Generate only affected documents
        result = await generate_compliance_kit(
            company_id,
            doc_types=doc_types,  # selective
        )

        # Notify admin that docs are ready for review
        company = supabase.table("companies").select("name, email").eq(
            "id", company_id
        ).limit(1).execute()
        company_name = company.data[0].get("name", "") if company.data else ""

        from backend.outbound.email_engine import send_email
        await send_email(
            to="info@aishield.cz",
            subject=f"📄 [KE SCHVÁLENÍ] Monitoring regen: {company_name} — {len(doc_types)} dokumentů",
            html=f"""
            <div style="font-family:system-ui;padding:20px;">
                <h2>Regenerované dokumenty ke schválení</h2>
                <p>Firma: <strong>{company_name}</strong></p>
                <p>Scan ID: {scan_id}</p>
                <p>Dokumenty:</p>
                <ul>{"".join(f"<li>{d}</li>" for d in doc_types)}</ul>
                <p>Po schválení pošlete klientovi PDF emailem.</p>
                <p><a href="https://aishield.cz/admin/crm">Otevřít CRM →</a></p>
            </div>
            """,
            from_email="info@aishield.cz",
        )

        logger.info(f"[JOB] Selective regen done: {company_name}, {len(doc_types)} docs")
        return {"status": "ok", "docs_regenerated": doc_types}

    except Exception as e:
        logger.error(f"[JOB] Selective regen error: {e}", exc_info=True)
        raise



# ═══════════════════════════════════════════════════════════════
# ARQ Worker Settings
# ═══════════════════════════════════════════════════════════════

class WorkerSettings:
    """ARQ worker konfigurace — spouští se jako: arq backend.jobs.worker.WorkerSettings"""

    # Registrace job funkcí
    functions = [
        generate_compliance_kit_job,
        rescan_client_job,
        send_questionnaire_reminder_job,
        func(deep_scan_job, max_tries=1),  # Deep scan = 24h, drahý → žádný retry
        monitoring_post_scan_job,
        selective_regen_job,
    ]

    # Cron jobs
    cron_jobs = [
        cron(monthly_monitoring_cron, hour=3, minute=0),        # 03:00 — monitoring
        cron(questionnaire_reminder_cron, hour=9, minute=0),    # 09:00 — reminders
    ]

    # Redis
    redis_settings = REDIS_SETTINGS

    # Limity
    import os
    _testing = os.getenv("DEEP_SCAN_MODE", "production").lower() == "testing"
    max_jobs = 5           # Max paralelních jobů (Playwright → RAM limit)
    job_timeout = 1800 if _testing else 90000    # Testing: 30min, Production: 25h
    max_tries = 2          # 2 pokusy při selhání (deep_scan_job má vlastní max_tries=1)
    retry_delay = 300      # 5min mezi pokusy

    # Logging
    log_results = True

    @staticmethod
    async def on_startup(ctx: dict):
        # Configure Python logging for the ARQ worker process
        import logging as _logging
        _logging.basicConfig(
            level=_logging.INFO,
            format="%(levelname)s %(name)s: %(message)s",
            force=True,
        )
        logger.info("🚀 AIshield ARQ Worker starting...")

    @staticmethod
    async def on_shutdown(ctx: dict):
        logger.info("🛑 AIshield ARQ Worker shutting down...")
