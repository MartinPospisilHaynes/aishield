"""
AIshield.cz — ARQ Worker & Job Queue
Asynchronní zpracování úloh: generování dokumentů, monitoring skeny,
email remindery. Běží jako samostatný systemd service.

Spuštění:  arq backend.jobs.worker.WorkerSettings
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from arq import cron
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
    Cron job: 1× denně ve 3:00 — zpracuje klienty, jejichž
    next_scan_date <= dnes. Rozloží skeny po dnech v měsíci
    podle hash(company_id) aby nedošlo k přetížení.
    """
    logger.info("[CRON] Spouštím měsíční monitoring check")
    supabase = get_supabase()

    try:
        # Platící klienti s aktivním monitoringem (PRO, ENTERPRISE)
        orders = supabase.table("orders").select(
            "id, user_email, plan, company_id"
        ).in_("plan", ["pro", "enterprise"]).eq("status", "paid").execute()

        if not orders.data:
            logger.info("[CRON] Žádní klienti pro monitoring")
            return {"status": "ok", "queued": 0}

        today = datetime.now(timezone.utc).date()
        queued = 0

        from arq import create_pool
        redis = await create_pool(REDIS_SETTINGS)

        for order in orders.data:
            company_id = order.get("company_id")
            if not company_id:
                continue

            # Rozložení po měsíci: hash company_id → den 1-28
            scan_day = (hash(company_id) % 28) + 1
            if today.day != scan_day:
                continue

            # Enqueue rescan job
            await redis.enqueue_job(
                "rescan_client_job",
                company_id,
                _job_id=f"rescan_{company_id}_{today.isoformat()}",
            )
            queued += 1

        await redis.close()
        logger.info(f"[CRON] Naplánováno {queued} monitoring skenů")
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
# ARQ Worker Settings
# ═══════════════════════════════════════════════════════════════

class WorkerSettings:
    """ARQ worker konfigurace — spouští se jako: arq backend.jobs.worker.WorkerSettings"""

    # Registrace job funkcí
    functions = [
        generate_compliance_kit_job,
        rescan_client_job,
        send_questionnaire_reminder_job,
        deep_scan_job,
    ]

    # Cron jobs
    cron_jobs = [
        cron(monthly_monitoring_cron, hour=3, minute=0),        # 03:00 — monitoring
        cron(questionnaire_reminder_cron, hour=9, minute=0),    # 09:00 — reminders
    ]

    # Redis
    redis_settings = REDIS_SETTINGS

    # Limity
    max_jobs = 5           # Max paralelních jobů (Playwright → RAM limit)
    job_timeout = 90000    # 25 hodin max (deep scan trvá ~24h)
    max_tries = 2          # 2 pokusy při selhání (deep scan = drahý)
    retry_delay = 300      # 5min mezi pokusy

    # Logging
    log_results = True

    @staticmethod
    async def on_startup(ctx: dict):
        logger.info("🚀 AIshield ARQ Worker starting...")

    @staticmethod
    async def on_shutdown(ctx: dict):
        logger.info("🛑 AIshield ARQ Worker shutting down...")
