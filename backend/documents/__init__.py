"""
AIshield.cz — Documents modul
Generování AI Act Compliance Kitu:
  - 7 HTML šablon dokumentů (templates.py)
  - PDF generátor pomocí WeasyPrint (pdf_generator.py)
  - Orchestrační pipeline (pipeline.py)
"""

from backend.documents.templates import TEMPLATE_RENDERERS, TEMPLATE_NAMES
from backend.documents.pipeline import generate_compliance_kit, generate_single_document
from backend.documents.pdf_generator import html_to_pdf, generate_document_pdf

__all__ = [
    "TEMPLATE_RENDERERS",
    "TEMPLATE_NAMES",
    "generate_compliance_kit",
    "generate_single_document",
    "html_to_pdf",
    "generate_document_pdf",
]
