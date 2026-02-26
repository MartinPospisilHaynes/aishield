"""
AIshield.cz — Bank Payment Checker (Cron)
Kontroluje příchozí platby přes FIO Banka API a páruje je
s objednávkami podle variabilního symbolu.

Spouští se cronem každých 5 minut:
  */5 * * * * cd /opt/aishield && /opt/aishield/venv/bin/python -m backend.payments.bank_checker

FIO API dokumentace:
  https://www.fio.cz/docs/cz/API_Bankovnictvi.pdf
"""

import asyncio
import base64
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import get_settings
from backend.database import get_supabase
from backend.outbound.email_engine import send_email
from backend.outbound.payment_emails import (
    build_payment_received_email,
    generate_variable_symbol,
)
from backend.outbound.invoice_pdf import (
    generate_invoice_pdf,
    build_invoice_email_html,
)

logger = logging.getLogger("bank_checker")

# FIO Banka API base URL
FIO_API_BASE = "https://fioapi.fio.cz/v1/rest"


async def fetch_fio_transactions(token: str, days_back: int = 3) -> list[dict]:
    """
    Stáhne transakce z FIO Banky za posledních N dní.
    Vrací seznam příchozích plateb s variabilním symbolem.
    """
    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")

    url = f"{FIO_API_BASE}/periods/{token}/{date_from}/{date_to}/transactions.json"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        # FIO API rate limit: max 1 request per 30s per token → 409
        if resp.status_code == 409:
            logger.warning("FIO API rate limit (409) — will retry next cron run")
            return []
        resp.raise_for_status()
        data = resp.json()

    account_statement = data.get("accountStatement", {})
    transaction_list = account_statement.get("transactionList", {})
    transactions = transaction_list.get("transaction", [])

    incoming = []
    for tx in transactions:
        # FIO columns:
        # column0 = datum, column1 = objem, column5 = VS, column7 = poznámka,
        # column14 = typ (příjem / výdaj), column22 = id
        cols = tx.get("column", {}) if isinstance(tx.get("column"), dict) else {}
        # Some FIO responses use flat dict with "columnN" keys
        if not cols:
            cols = tx

        amount_col = cols.get("column1", {})
        vs_col = cols.get("column5", {})
        date_col = cols.get("column0", {})
        id_col = cols.get("column22", {})

        amount = amount_col.get("value", 0) if isinstance(amount_col, dict) else 0
        vs = str(vs_col.get("value", "")).strip() if isinstance(vs_col, dict) else ""
        tx_date = date_col.get("value", "") if isinstance(date_col, dict) else ""
        tx_id = str(id_col.get("value", "")) if isinstance(id_col, dict) else ""

        # Pouze příchozí platby (kladné částky) s variabilním symbolem
        if amount > 0 and vs:
            incoming.append({
                "fio_id": tx_id,
                "amount": amount,
                "variable_symbol": vs,
                "date": tx_date,
            })

    return incoming


async def match_and_confirm_payments():
    """
    Hlavní logika:
    1. Stáhne transakce z FIO
    2. Najde objednávky AWAITING_PAYMENT s odpovídajícím VS
    3. Aktualizuje status na PAID
    4. Pošle email o přijaté platbě
    """
    settings = get_settings()

    if not settings.fio_api_token:
        logger.warning("FIO_API_TOKEN is not set — skipping bank payment check")
        return

    supabase = get_supabase()

    # 1. Stáhni transakce
    try:
        transactions = await fetch_fio_transactions(settings.fio_api_token)
        logger.info(f"Fetched {len(transactions)} incoming transactions from FIO")
    except Exception as e:
        logger.error(f"Failed to fetch FIO transactions: {e}")
        return

    if not transactions:
        logger.info("No incoming transactions to process")
        return

    # 2. Načti všechny čekající objednávky (bank_transfer)
    awaiting = supabase.table("orders").select("*").eq(
        "payment_gateway", "bank_transfer"
    ).eq("status", "AWAITING_PAYMENT").execute()

    if not awaiting.data:
        logger.info("No orders awaiting payment")
        return

    # Mapuj VS → objednávka (VS je uložen v gopay_payment_id jako "BT-{vs}")
    vs_to_order: dict[str, dict] = {}
    for order in awaiting.data:
        payment_id = order.get("gopay_payment_id", "")
        if payment_id.startswith("BT-"):
            vs = payment_id[3:]  # Strip "BT-" prefix
            vs_to_order[vs] = order

    # 3. Páruj platby
    matched = 0
    for tx in transactions:
        vs = tx["variable_symbol"]
        if vs in vs_to_order:
            order = vs_to_order[vs]
            order_num = order["order_number"]

            # Ověř částku (tolerance ±1 Kč kvůli zaokrouhlení)
            expected = order.get("amount", 0)
            actual = tx["amount"]
            if abs(actual - expected) > 1:
                logger.warning(
                    f"Amount mismatch for {order_num}: expected {expected}, got {actual} (VS={vs})"
                )
                continue

            # Aktualizuj status
            supabase.table("orders").update({
                "status": "PAID",
                "paid_at": datetime.utcnow().isoformat(),
                "activated": True,
            }).eq("order_number", order_num).execute()

            logger.info(f"✅ Payment confirmed for {order_num} (VS={vs}, amount={actual})")

            # Aktualizuj workflow_status na firmě
            email = order.get("email", order.get("user_email", ""))
            if email:
                # Najdi firmu
                company = supabase.table("companies").select("id").eq(
                    "contact_email", email
                ).execute()
                if not company.data:
                    # Zkus přes clients tabulku
                    client = supabase.table("clients").select("company_id").eq(
                        "email", email
                    ).execute()
                    if client.data:
                        company_id = client.data[0]["company_id"]
                        supabase.table("companies").update({
                            "workflow_status": "processing",
                        }).eq("id", company_id).execute()
                else:
                    supabase.table("companies").update({
                        "workflow_status": "processing",
                    }).eq("id", company.data[0]["id"]).execute()

            # ── Auto-faktura (invoice) ──────────────────────────────
            invoice_number = ""
            try:
                billing = order.get("billing_data") or {}
                vs = generate_variable_symbol(order_num)
                paid_at_str = datetime.utcnow().isoformat()

                # 1) Generate PDF
                pdf_bytes, invoice_number = generate_invoice_pdf(
                    order_number=order_num,
                    plan=order.get("plan", "basic"),
                    amount=int(actual),
                    buyer_name=billing.get("company", ""),
                    buyer_ico=billing.get("ico", ""),
                    buyer_dic=billing.get("dic", ""),
                    buyer_street=billing.get("street", ""),
                    buyer_city=billing.get("city", ""),
                    buyer_zip=billing.get("zip", ""),
                    buyer_email=email,
                    paid_at=paid_at_str,
                    created_at=order.get("created_at"),
                    variable_symbol=vs,
                )

                # 2) Build email + attachment
                invoice_html = build_invoice_email_html(
                    invoice_number=invoice_number,
                    order_number=order_num,
                    plan=order.get("plan", "basic"),
                    amount=int(actual),
                )
                pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
                pdf_filename = f"faktura-{invoice_number}.pdf"
                attachments = [{"filename": pdf_filename, "content": pdf_b64}]

                await send_email(
                    to=email,
                    subject=f"AIshield.cz — Faktura {invoice_number}",
                    html=invoice_html,
                    from_email="info@aishield.cz",
                    from_name="AIshield.cz",
                    attachments=attachments,
                )
                logger.info(f"Invoice {invoice_number} sent to {email} ({len(pdf_bytes)} B)")

                # 3) Save to Supabase Storage
                try:
                    from backend.documents.pdf_generator import save_pdf_to_supabase
                    company_id = order.get("company_id") or "no-company"
                    pdf_url = save_pdf_to_supabase(
                        pdf_bytes=pdf_bytes,
                        filename=pdf_filename,
                        client_id=f"invoices/{company_id}",
                        bucket="documents",
                    )
                    logger.info(f"Invoice PDF → Supabase Storage: {pdf_url}")
                except Exception as e:
                    pdf_url = ""
                    logger.error(f"Failed to save invoice to Supabase: {e}")

                # 4) Save locally on VPS
                try:
                    year = datetime.utcnow().strftime("%Y")
                    local_dir = f"/opt/aishield/invoices/{year}"
                    os.makedirs(local_dir, exist_ok=True)
                    with open(f"{local_dir}/{pdf_filename}", "wb") as f:
                        f.write(pdf_bytes)
                    logger.info(f"Invoice PDF → {local_dir}/{pdf_filename}")
                except Exception as e:
                    logger.error(f"Failed to save invoice locally: {e}")

                # 5) Insert into invoices table
                try:
                    supabase.table("invoices").insert({
                        "invoice_number": invoice_number,
                        "order_number": order_num,
                        "company_id": order.get("company_id"),
                        "email": email,
                        "plan": order.get("plan", ""),
                        "amount": int(actual),
                        "buyer_name": billing.get("company", ""),
                        "buyer_ico": billing.get("ico", ""),
                        "pdf_url": pdf_url,
                        "pdf_filename": pdf_filename,
                    }).execute()
                    logger.info(f"Invoice record inserted: {invoice_number}")
                except Exception as e:
                    logger.error(f"Failed to insert invoice record: {e}")

                # 6) Copy to admin
                try:
                    await send_email(
                        to="info@aishield.cz",
                        subject=f"[KOPIE] Faktura {invoice_number} — {email}",
                        html=invoice_html,
                        from_email="info@aishield.cz",
                        from_name="AIshield.cz",
                        attachments=attachments,
                    )
                except Exception as e:
                    logger.error(f"Failed to send invoice copy to admin: {e}")

            except Exception as e:
                logger.error(f"Auto-invoice failed for {order_num}: {e}", exc_info=True)

            # ── Platba přijata email ──────────────────────────────
            try:
                html = build_payment_received_email(
                    order_number=order_num,
                    plan=order.get("plan", "basic"),
                    amount=int(actual),
                )
                await send_email(
                    to=email,
                    subject=f"AIshield.cz — Platba přijata ✅ ({order_num})",
                    html=html,
                    from_email="info@aishield.cz",
                    from_name="AIshield.cz",
                )
                logger.info(f"Payment confirmation email sent to {email}")
            except Exception as e:
                logger.error(f"Failed to send payment email for {order_num}: {e}")

            # ── Enqueue Compliance Kit generation ─────────────────
            try:
                from arq import create_pool
                from backend.jobs.worker import WorkerSettings
                pool = await create_pool(WorkerSettings)
                company_id = order.get("company_id") or ""
                order_id = order.get("id") or ""
                if company_id:
                    await pool.enqueue_job(
                        "generate_compliance_kit_job",
                        company_id,
                        order_id,
                    )
                    logger.info(f"Compliance Kit job enqueued for company={company_id}")
                else:
                    logger.warning(f"No company_id on order {order_num} — skipping kit")
            except Exception as e:
                logger.error(f"Failed to enqueue compliance kit for {order_num}: {e}")

            matched += 1

    logger.info(f"Matched {matched} payments out of {len(transactions)} transactions")


def main():
    """Entry point pro cron."""
    logger.info("=== Bank Payment Checker starting ===")
    asyncio.run(match_and_confirm_payments())
    logger.info("=== Bank Payment Checker finished ===")


if __name__ == "__main__":
    main()
