from pathlib import Path
from pypdf import PdfReader
from config import config as c


def extract_document_text(file_path):
    pages = PdfReader(file_path).pages
    texts = [p.extract_text() for p in pages]
    if not texts or any(not t or not t.strip() for t in texts):
        raise ValueError(f"{file_path}: page without text")
    return "\n".join(texts)


def extract_text_from_directory(docs_directory):
    paths = sorted(
        p
        for p in Path(docs_directory).iterdir()
        if p.is_file() and p.suffix.lower() == c.PDF_FILE_SUFFIX
    )
    if not paths:
        raise ValueError(f"{docs_directory}: no PDFs")
    return [
        dict(document_name=p.name, document_text=extract_document_text(str(p)))
        for p in paths
    ]
