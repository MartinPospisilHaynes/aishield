"""
AIshield.cz — PDF generátor
Úkol 18: Konverze HTML šablon → PDF pomocí WeasyPrint.
"""

import io
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _fix_orphaned_headings(html: str) -> str:
    """
    Post-processing: obalí každý <h2>/<h3> + první následující element
    do <div style="break-inside:avoid"> aby nadpis nezůstal sám na konci stránky.
    """
    import re
    # Pattern: h2 or h3 tag, then optional whitespace, then next block element
    # We wrap the heading + next element in a no-break div
    pattern = r'(<h[23][^>]*>.*?</h[23]>)(\s*)(<(?:table|p|ul|ol|div|dl)[^>]*>.*?</(?:table|p|ul|ol|div|dl)>)'
    
    def _wrap(m):
        return f'<div style="break-inside:avoid;page-break-inside:avoid">{m.group(1)}{m.group(2)}{m.group(3)}</div>'
    
    result = re.sub(pattern, _wrap, html, flags=re.DOTALL)
    
    # Count wraps for logging
    wraps = result.count('break-inside:avoid;page-break-inside:avoid')
    if wraps > 0:
        logger.info(f"Orphan fix: {wraps} headings wrapped with next element")
    
    return result


def html_to_pdf(html_content: str) -> bytes:
    """
    Konvertuje HTML string na PDF bytes.
    Používá WeasyPrint pro věrný rendering včetně CSS.
    """
    try:
        from weasyprint import HTML
        html_content = _fix_orphaned_headings(html_content)
        pdf_bytes = HTML(string=html_content).write_pdf()
        logger.info(f"PDF vygenerováno: {len(pdf_bytes)} bytes")
        return pdf_bytes
    except ImportError:
        logger.warning("WeasyPrint není nainstalován — fallback na HTML-only")
        raise ImportError(
            "WeasyPrint není nainstalován. Nainstalujte: pip install weasyprint"
        )


def save_to_supabase_storage(
    file_bytes: bytes,
    filename: str,
    client_id: str,
    bucket: str = "documents",
    content_type: str = "application/pdf",
) -> str:
    """
    Uloží soubor do Supabase Storage a vrátí veřejný URL.
    Cesta: documents/{client_id}/{filename}
    Podporuje PDF, HTML, PPTX a další formáty.
    """
    from backend.database import get_supabase

    supabase = get_supabase()
    storage_path = f"{client_id}/{filename}"

    try:
        # Smazat starý soubor, pokud existuje (update)
        try:
            supabase.storage.from_(bucket).remove([storage_path])
        except Exception:
            pass  # Soubor neexistuje — OK

        # Upload souboru
        supabase.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )

        # Získat veřejný URL
        url = supabase.storage.from_(bucket).get_public_url(storage_path)
        logger.info(f"PDF uloženo: {storage_path} → {url}")
        return url

    except Exception as e:
        logger.error(f"Chyba při ukládání do Supabase Storage: {e}")
        # Fallback — vrátit prázdný URL, soubor je stále dostupný jako bytes
        return ""


# Backward-compatible alias
save_pdf_to_supabase = save_to_supabase_storage


def generate_document_pdf(
    template_key: str,
    data: dict,
    client_id: str,
) -> dict:
    """
    Generuje jeden dokument: šablona → HTML → PDF → Supabase.
    Vrací dict s metadaty.
    """
    from backend.documents.templates import TEMPLATE_RENDERERS, TEMPLATE_NAMES

    if template_key not in TEMPLATE_RENDERERS:
        raise ValueError(f"Neznámá šablona: {template_key}")

    renderer = TEMPLATE_RENDERERS[template_key]
    template_name = TEMPLATE_NAMES[template_key]

    # 1. Render HTML
    html_content = renderer(data)

    # 2. Convert to PDF
    try:
        pdf_bytes = html_to_pdf(html_content)
        has_pdf = True
    except ImportError:
        pdf_bytes = html_content.encode("utf-8")
        has_pdf = False

    # 3. Uložit do Supabase Storage
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{template_key}_{timestamp}.pdf" if has_pdf else f"{template_key}_{timestamp}.html"
    download_url = save_to_supabase_storage(pdf_bytes, filename, client_id)

    return {
        "template_key": template_key,
        "template_name": template_name,
        "filename": filename,
        "download_url": download_url,
        "size_bytes": len(pdf_bytes),
        "format": "pdf" if has_pdf else "html",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
