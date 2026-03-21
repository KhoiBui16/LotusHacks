from __future__ import annotations

import importlib
from pathlib import Path
import re
from typing import Any, Dict

def _load_pdf_engine() -> Any:
    """Load PyMuPDF safely without hard-failing module import time."""
    try:
        pymupdf = importlib.import_module("pymupdf")
        if hasattr(pymupdf, "open"):
            return pymupdf
    except Exception:
        pass

    try:
        fitz = importlib.import_module("fitz")
        if hasattr(fitz, "open"):
            return fitz
    except Exception:
        pass

    raise RuntimeError(
        "PDF parsing requires PyMuPDF. Install with: pip uninstall -y fitz && pip install PyMuPDF"
    )


def _load_docx_engine() -> Any:
    """Load python-docx lazily to avoid module import failure when DOCX is unused."""
    try:
        docx_module = importlib.import_module("docx")
        document_cls = getattr(docx_module, "Document", None)
        if document_cls is None:
            raise RuntimeError("python-docx is installed but Document class is unavailable")
        return document_cls
    except Exception as exc:
        raise RuntimeError(
            "DOCX parsing requires python-docx. Install with: pip install python-docx"
        ) from exc


class FileReader:
    def read(self, file_path: str) -> Dict[str, object]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        suffix = path.suffix.lower()
        if suffix == ".txt":
            raw_text = self._read_txt(path)
        elif suffix == ".docx":
            raw_text = self._read_docx(path)
        elif suffix == ".pdf":
            raw_text = self._read_pdf(path)
        else:
            raise ValueError(f"Định dạng file chưa hỗ trợ: {suffix}")

        cleaned_text = self._normalize_text(raw_text)
        return {
            "file_name": path.name,
            "file_type": suffix,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "num_chars": len(cleaned_text),
        }

    def _read_txt(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _read_docx(self, path: Path) -> str:
        Document = _load_docx_engine()
        doc = Document(str(path))
        parts = []

        # Paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                parts.append(text)

        # Tables
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))

        return "\n".join(parts)

    def _read_pdf(self, path: Path) -> str:
        texts = []
        fitz = _load_pdf_engine()
        pdf = fitz.open(str(path))
        try:
            for page in pdf:
                text = page.get_text("text")
                if text.strip():
                    texts.append(text.strip())
        finally:
            pdf.close()
        return "\n".join(texts)

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        return text.strip()


def read_text_file(file_path: str) -> Dict[str, object]:
    return FileReader().read(file_path)