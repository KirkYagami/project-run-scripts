"""Gets the text out of the PDFs and does nothing else with it."""
import os

from pypdf import PdfReader


def extract_text_from_directory(docs_directory):
    """Read every PDF in the folder once, in file-name order."""
    file_names = sorted(name for name in os.listdir(docs_directory)
                        if name.lower().endswith(".pdf")
                        and os.path.isfile(os.path.join(docs_directory, name)))
    entries = []
    for file_name in file_names:
        reader = PdfReader(os.path.join(docs_directory, file_name))
        page_texts = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                raise ValueError(f"No text can be read from page {page_number} of {file_name}")
            page_texts.append(page_text)
        entries.append({"document_name": file_name, "document_text": "\n".join(page_texts)})
    return entries
