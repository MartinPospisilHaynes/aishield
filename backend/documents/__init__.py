"""
AIshield.cz — Documents modul
Generování AI Act Compliance Kitu:
  - 11 HTML šablon dokumentů (templates.py)
  - Unified PDF generátor (unified_pdf.py)
  - PDF engine — WeasyPrint (pdf_generator.py)
  - PPTX prezentace (pptx_generator.py)
  - Orchestrační pipeline (pipeline.py)

Výstup: 1 × PDF, 1 × HTML, 1 × PPTX
"""

from backend.documents.templates import TEMPLATE_RENDERERS, TEMPLATE_NAMES
from backend.documents.pipeline import generate_compliance_kit, generate_single_document
from backend.documents.pdf_generator import html_to_pdf, generate_document_pdf
from backend.documents.unified_pdf import render_unified_pdf_html

__all__ = [
    "TEMPLATE_RENDERERS",
    "TEMPLATE_NAMES",
    "generate_compliance_kit",
    "generate_single_document",
    "html_to_pdf",
    "generate_document_pdf",
    "render_unified_pdf_html",
]
