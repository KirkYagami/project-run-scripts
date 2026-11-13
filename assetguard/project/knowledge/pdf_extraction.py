"""Pulls the written text out of each maintenance document."""

import os

from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    """Every page's text, in order, joined with a blank line between pages."""
    page_texts = []
    for page in PdfReader(pdf_path).pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            page_texts.append(page_text)
    return "\n\n".join(page_texts)


def extract_text_from_directory(docs_directory):
    """One {document_name, document_text} record per PDF, sorted by file name."""
    document_entries = []
    for file_name in sorted(os.listdir(docs_directory)):
        if not file_name.lower().endswith(".pdf"):
            continue
        document_entries.append({
            "document_name": file_name,
            "document_text": extract_text_from_pdf(os.path.join(docs_directory, file_name)),
        })
    return document_entries
