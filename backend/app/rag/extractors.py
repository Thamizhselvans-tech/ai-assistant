"""Document text extraction engine supporting PDF, DOCX, and TXT files."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz
import docx


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class ExtractedDocument:
    filename: str
    file_type: str
    total_pages: int
    pages: List[ExtractedPage] = field(default_factory=list)
    is_scanned: bool = False
    warning_message: Optional[str] = None

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def normalize_text(text: str) -> str:
    """Normalize extracted text without destroying meaningful paragraph formatting."""
    if not text:
        return ""
    # Replace non-breaking spaces and zero-width spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace excessive tabs and spaces on individual lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    # Collapse 3+ consecutive newlines to 2 (preserving paragraph breaks)
    collapsed = "\n".join(lines)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    return collapsed.strip()


class DocumentExtractor:
    """Unified extractor for PDF, DOCX, and TXT files with safety and validation."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    @classmethod
    def validate_file(cls, file_path: str, max_size_bytes: int) -> str:
        """Validate file existence, extension, and size. Returns extension."""
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: {', '.join(cls.SUPPORTED_EXTENSIONS)}")

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise ValueError("The uploaded file is empty (0 bytes).")
        
        if file_size > max_size_bytes:
            max_mb = max_size_bytes / (1024 * 1024)
            raise ValueError(f"File size exceeds maximum allowed limit of {max_mb:.1f} MB.")

        return ext

    @classmethod
    def extract(cls, file_path: str, original_filename: Optional[str] = None) -> ExtractedDocument:
        """Extract text and metadata from the document."""
        path = Path(file_path)
        ext = path.suffix.lower()
        display_name = original_filename or path.name

        if ext == ".pdf":
            return cls._extract_pdf(path, display_name)
        elif ext == ".docx":
            return cls._extract_docx(path, display_name)
        elif ext == ".txt":
            return cls._extract_txt(path, display_name)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @classmethod
    def _extract_pdf(cls, path: Path, filename: str) -> ExtractedDocument:
        pages: List[ExtractedPage] = []
        total_chars = 0
        warning: Optional[str] = None
        is_scanned = False

        try:
            doc = fitz.open(str(path))
        except Exception as e:
            raise ValueError(f"Failed to open or parse PDF file (possibly corrupt): {str(e)}")

        total_pages = len(doc)
        if total_pages == 0:
            doc.close()
            raise ValueError("PDF contains 0 pages.")

        try:
            for idx, page in enumerate(doc):
                raw_text = page.get_text("text")
                cleaned = normalize_text(raw_text)
                if cleaned:
                    total_chars += len(cleaned)
                pages.append(ExtractedPage(page_number=idx + 1, text=cleaned))
        finally:
            doc.close()

        # Heuristic for scanned/image-only PDFs
        avg_chars_per_page = total_chars / total_pages if total_pages > 0 else 0
        if total_chars == 0 or avg_chars_per_page < 15:
            is_scanned = True
            warning = (
                "Scanned or image-only PDF detected: no readable text could be extracted. "
                "Optical Character Recognition (OCR) is required for scanned documents."
            )

        return ExtractedDocument(
            filename=filename,
            file_type="pdf",
            total_pages=total_pages,
            pages=pages,
            is_scanned=is_scanned,
            warning_message=warning
        )

    @classmethod
    def _extract_docx(cls, path: Path, filename: str) -> ExtractedDocument:
        try:
            doc = docx.Document(str(path))
        except Exception as e:
            raise ValueError(f"Failed to open or parse Word DOCX file: {str(e)}")

        # Extract text from paragraphs and tables
        parts: List[str] = []
        for p in doc.paragraphs:
            text = normalize_text(p.text)
            if text:
                parts.append(text)

        for table in doc.tables:
            for row in table.rows:
                row_cells = [normalize_text(cell.text) for cell in row.cells if cell.text.strip()]
                if row_cells:
                    parts.append(" | ".join(row_cells))

        full_doc_text = "\n\n".join(parts)
        if not full_doc_text.strip():
            return ExtractedDocument(
                filename=filename,
                file_type="docx",
                total_pages=1,
                pages=[ExtractedPage(page_number=1, text="")],
                warning_message="DOCX document contains no text."
            )

        return ExtractedDocument(
            filename=filename,
            file_type="docx",
            total_pages=1,
            pages=[ExtractedPage(page_number=1, text=full_doc_text)]
        )

    @classmethod
    def _extract_txt(cls, path: Path, filename: str) -> ExtractedDocument:
        raw_bytes = path.read_bytes()
        text = ""
        # Try UTF-8 first, fallback to common encodings
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        cleaned = normalize_text(text)
        if not cleaned:
            return ExtractedDocument(
                filename=filename,
                file_type="txt",
                total_pages=1,
                pages=[ExtractedPage(page_number=1, text="")],
                warning_message="Text file is empty or contains only whitespace."
            )

        return ExtractedDocument(
            filename=filename,
            file_type="txt",
            total_pages=1,
            pages=[ExtractedPage(page_number=1, text=cleaned)]
        )
