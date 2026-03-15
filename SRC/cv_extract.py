from __future__ import annotations
from io import BytesIO
from typing import Tuple
import io



def extract_text_from_upload(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    name = (filename or "").lower().strip()

    if name.endswith(".pdf"):
        return _extract_pdf(file_bytes), "pdf"

    if name.endswith(".docx"):
        return _extract_docx(file_bytes), "docx"

    if name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore"), "txt"

    # fallback
    try:
        return file_bytes.decode("utf-8", errors="ignore"), "unknown"
    except Exception:
        return "", "unknown"


def _extract_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(BytesIO(file_bytes))
    parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(parts).strip()


def _extract_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            texts.append(t)
    return "\n".join(texts).strip()