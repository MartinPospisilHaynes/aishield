"""
AIshield.cz -- Invoice PDF Generator
Generates Czech-compliant invoices (faktury) as PDF using fpdf2.
Supports full Czech diacritics via DejaVu Sans TTF embedding.
"""

import io
import logging
import os
from datetime import datetime, timezone

from fpdf import FPDF

logger = logging.getLogger(__name__)

# -- Font paths --
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

# -- Seller info --
SELLER = {
    "name": "Bc. Martin Haynes",
    "ico": "17889251",
    "street": "Ml\u00fdnsk\u00e1 53",
    "city": "Velk\u00e1 Byst\u0159ice",
    "zip": "783 53",
    "phone": "732 716 141",
    "email": "info@aishield.cz",
    "web": "aishield.cz",
    "bank_account": "2610538018/3030",
    "bank_name": "Air Bank",
    "iban": "CZ9130300000002610538018",
}

PLAN_NAMES = {
    "basic": "BASIC",
    "pro": "PRO",
    "enterprise": "ENTERPRISE",
    "coffee": "Kafe",
}

PLAN_DESCRIPTIONS = {
    "basic": "Sada dokumentace pro soulad s EU AI Act (Compliance Kit) \u2014 BASIC",
    "pro": "Sada dokumentace pro soulad s EU AI Act s implementac\u00ed na kl\u00ed\u010d \u2014 PRO",
    "enterprise": "Komplexn\u00ed \u0159e\u0161en\u00ed souladu s EU AI Act v\u010d. 2 let p\u00e9\u010de \u2014 ENTERPRISE",
    "coffee": "Dobrovoln\u00fd p\u0159\u00edsp\u011bvek na provoz slu\u017eby",
}


def generate_invoice_number(order_number: str, paid_at: str | None = None) -> str:
    parts = order_number.split("-")
    suffix = parts[-1] if len(parts) >= 3 else order_number[-8:]
    if paid_at:
        try:
            dt = datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
            year = dt.year
        except Exception:
            year = datetime.now(timezone.utc).year
    else:
        year = datetime.now(timezone.utc).year
    return f"FV-{year}-{suffix}"


class InvoicePDF(FPDF):

    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", FONT_REGULAR, uni=True)
        self.add_font("DejaVu", "B", FONT_BOLD, uni=True)
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        pass

    def footer(self):
        self.set_y(-20)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(150, 150, 150)
        self.cell(
            0, 4,
            "Dodavatel nen\u00ed pl\u00e1tcem DPH.",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        self.cell(
            0, 4,
            "Faktura vystavena elektronicky syst\u00e9mem AIshield.cz"
            f"  |  {SELLER['name']}  |  I\u010cO: {SELLER['ico']}"
            f"  |  {SELLER['email']}",
            align="C",
        )


def _fmt_amount(a: int) -> str:
    return f"{a:,} K\u010d".replace(",", "\u00a0")


def generate_invoice_pdf(
    order_number: str,
    plan: str,
    amount: int,
    buyer_name: str = "",
    buyer_ico: str = "",
    buyer_dic: str = "",
    buyer_street: str = "",
    buyer_city: str = "",
    buyer_zip: str = "",
    buyer_email: str = "",
    paid_at: str | None = None,
    created_at: str | None = None,
    variable_symbol: str = "",
) -> tuple[bytes, str]:
    """Generate invoice PDF. Returns (pdf_bytes, invoice_number)."""
    invoice_number = generate_invoice_number(order_number, paid_at)
    plan_desc = PLAN_DESCRIPTIONS.get(plan, f"Slu\u017eba AIshield.cz - {plan.upper()}")

    now = datetime.now(timezone.utc)
    if paid_at:
        try:
            issue_date = datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
        except Exception:
            issue_date = now
    else:
        issue_date = now

    fmt_date = lambda d: d.strftime("%d.%m.%Y")

    pdf = InvoicePDF()
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin
    LEFT = pdf.l_margin

    # == HEADER ==
    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(30, 27, 75)
    pdf.cell(W / 2, 10, "AIshield.cz", new_x="RIGHT")

    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(W / 2, 10, "FAKTURA", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(W / 2, 5, "AI Act Compliance", new_x="RIGHT")

    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(W / 2, 5, invoice_number, align="R", new_x="LMARGIN", new_y="NEXT")

    # Paid stamp
    pdf.set_xy(LEFT + W - 45, pdf.get_y() + 1)
    pdf.set_fill_color(34, 197, 94)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 9)
    pdf.cell(40, 7, "ZAPLACENO", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_draw_color(124, 58, 237)
    pdf.set_line_width(0.8)
    pdf.line(LEFT, pdf.get_y(), LEFT + W, pdf.get_y())
    pdf.set_y(pdf.get_y() + 8)

    # == PARTIES ==
    party_w = W / 2 - 5
    party_y = pdf.get_y()

    # Seller
    pdf.set_fill_color(248, 247, 255)
    pdf.set_draw_color(232, 229, 245)
    pdf.rect(LEFT, party_y, party_w, 42, "DF")

    pdf.set_xy(LEFT + 4, party_y + 3)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(party_w - 8, 4, "DODAVATEL", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(LEFT + 4)
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(party_w - 8, 5, SELLER["name"], new_x="LMARGIN", new_y="NEXT")

    seller_lines = [
        f"I\u010cO: {SELLER['ico']}",
        SELLER["street"],
        f"{SELLER['zip']} {SELLER['city']}",
        SELLER["email"],
        SELLER["web"],
    ]
    for line in seller_lines:
        pdf.set_x(LEFT + 4)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(75, 85, 99)
        pdf.cell(party_w - 8, 4, line, new_x="LMARGIN", new_y="NEXT")

    # Buyer
    buyer_x = LEFT + party_w + 10
    pdf.set_fill_color(240, 253, 244)
    pdf.set_draw_color(209, 250, 229)
    pdf.rect(buyer_x, party_y, party_w, 42, "DF")

    pdf.set_xy(buyer_x + 4, party_y + 3)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(party_w - 8, 4, "ODB\u011aRATEL", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(buyer_x + 4)
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(26, 26, 46)
    display_name = buyer_name or buyer_email or "\u2014"
    pdf.cell(party_w - 8, 5, display_name, new_x="LMARGIN", new_y="NEXT")

    buyer_details = []
    if buyer_ico:
        buyer_details.append(f"I\u010cO: {buyer_ico}")
    if buyer_dic:
        buyer_details.append(f"DI\u010c: {buyer_dic}")
    if buyer_street:
        buyer_details.append(buyer_street)
    if buyer_city or buyer_zip:
        buyer_details.append(f"{buyer_zip} {buyer_city}".strip())
    if buyer_email:
        buyer_details.append(buyer_email)

    for line in buyer_details[:5]:
        pdf.set_x(buyer_x + 4)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(75, 85, 99)
        pdf.cell(party_w - 8, 4, line, new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(party_y + 42 + 8)

    # == DATES ==
    dates_y = pdf.get_y()
    pdf.set_fill_color(250, 251, 252)
    pdf.set_draw_color(229, 231, 235)
    pdf.rect(LEFT, dates_y, W, 10, "DF")

    date_items = [
        ("Datum vystaven\u00ed:", fmt_date(issue_date)),
        ("DUZP:", fmt_date(issue_date)),
        ("Datum splatnosti:", fmt_date(issue_date)),
    ]
    col_w = W / len(date_items)
    for i, (label, value) in enumerate(date_items):
        x = LEFT + i * col_w + 4
        pdf.set_xy(x, dates_y + 2)
        pdf.set_font("DejaVu", "", 7)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(col_w / 2 - 2, 5, label)
        pdf.set_font("DejaVu", "B", 8)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(col_w / 2, 5, value)

    pdf.set_y(dates_y + 10 + 8)

    # == ITEMS TABLE ==
    col_widths = [W * 0.6, W * 0.15, W * 0.25]
    headers = ["Popis slu\u017eby", "Mno\u017estv\u00ed", "Cena"]
    aligns = ["L", "C", "R"]

    pdf.set_fill_color(30, 27, 75)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 8)
    for hdr, cw, al in zip(headers, col_widths, aligns):
        pdf.cell(cw, 8, hdr, align=al, fill=True)
    pdf.ln()

    pdf.set_text_color(26, 26, 46)
    pdf.set_font("DejaVu", "", 9)
    pdf.cell(col_widths[0], 7, plan_desc[:65], new_x="RIGHT")
    pdf.set_font("DejaVu", "", 9)
    pdf.cell(col_widths[1], 7, "1 ks", align="C", new_x="RIGHT")
    pdf.set_font("DejaVu", "B", 9)
    pdf.cell(col_widths[2], 7, _fmt_amount(amount), align="R")
    pdf.ln()

    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(col_widths[0], 5, f"Objedn\u00e1vka: {order_number}")
    pdf.ln()

    pdf.set_draw_color(229, 231, 235)
    pdf.set_line_width(0.3)
    pdf.line(LEFT, pdf.get_y() + 1, LEFT + W, pdf.get_y() + 1)
    pdf.set_y(pdf.get_y() + 6)

    # == TOTAL ==
    total_w = 70
    total_x = LEFT + W - total_w
    total_y = pdf.get_y()

    pdf.set_fill_color(124, 58, 237)
    pdf.rect(total_x, total_y, total_w, 20, "F")

    pdf.set_xy(total_x, total_y + 2)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(total_w, 5, "CELKEM K \u00dAHRAD\u011a", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(total_x)
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(total_w, 10, _fmt_amount(amount), align="C")

    pdf.set_y(total_y + 20 + 10)

    # == PAYMENT INFO ==
    pay_y = pdf.get_y()
    pdf.set_fill_color(248, 247, 255)
    pdf.set_draw_color(232, 229, 245)
    pdf.rect(LEFT, pay_y, W, 20, "DF")

    pdf.set_xy(LEFT + 4, pay_y + 2)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(W, 4, "PLATEBN\u00cd \u00daDAJE", new_x="LMARGIN", new_y="NEXT")

    vs_display = variable_symbol or "---"
    pay_items = [
        (f"\u010c\u00edslo \u00fa\u010dtu: {SELLER['bank_account']}",
         f"Banka: {SELLER['bank_name']}"),
        (f"VS: {vs_display}",
         f"IBAN: {SELLER['iban']}"),
    ]
    for left, right in pay_items:
        pdf.set_x(LEFT + 4)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(75, 85, 99)
        pdf.cell(W / 2 - 4, 5, left, new_x="RIGHT")
        pdf.cell(W / 2 - 4, 5, right, new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    pdf_bytes = buf.getvalue()

    logger.info(f"Invoice PDF generated: {invoice_number}, {len(pdf_bytes)} bytes")
    return pdf_bytes, invoice_number


def build_invoice_email_html(
    invoice_number: str,
    order_number: str,
    plan: str,
    amount: int,
) -> str:
    """Build HTML email body for invoice delivery (PDF is attached separately)."""
    from backend.outbound.payment_emails import _email_wrapper, PLAN_NAMES as PN

    plan_name = PN.get(plan, plan.upper())
    fmt_amount = f"{amount:,} K\u010d".replace(",", "\u00a0")

    content = f"""
    <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:800;color:#ffffff;">
        Faktura {invoice_number}
    </h1>
    <p style="margin:0 0 24px 0;font-size:14px;color:#94a3b8;">
        V p\u0159\u00edloze p\u0159ikl\u00e1d\u00e1me fakturu k objedn\u00e1vce
        <strong style="color:#ffffff;">{order_number}</strong>.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
        style="background:rgba(124,58,237,0.06);border:1px solid rgba(124,58,237,0.2);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:20px 24px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;width:40%;">Faktura \u010d.:</td>
            <td style="padding:6px 0;font-size:13px;color:#ffffff;font-weight:600;">{invoice_number}</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Slu\u017eba:</td>
            <td style="padding:6px 0;font-size:13px;color:#ffffff;font-weight:600;">{plan_name}</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">\u010c\u00e1stka:</td>
            <td style="padding:6px 0;font-size:16px;color:#22c55e;font-weight:800;">{fmt_amount}</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Stav:</td>
            <td style="padding:6px 0;font-size:13px;color:#22c55e;font-weight:700;">Zaplaceno</td>
        </tr>
        </table>
    </td></tr>
    </table>

    <p style="margin:0 0 24px 0;font-size:13px;color:#94a3b8;line-height:1.7;">
        Faktura ve form\u00e1tu PDF je p\u0159ilo\u017eena k tomuto emailu.
        Dokument m\u016f\u017eete pou\u017e\u00edt jako da\u0148ov\u00fd doklad
        pro va\u0161e \u00fa\u010detnictv\u00ed.
    </p>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:8px 0;">
        <a href="https://aishield.cz/dashboard"
           style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#7c3aed,#d946ef);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;">
            P\u0159ej\u00edt na Dashboard
        </a>
    </td></tr>
    </table>
    """

    return _email_wrapper(content)
