"""Document loading engine for PDF, DOCX, and TXT files with page-level metadata and validation."""

import os
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pymupdf as fitz
except ImportError:
    import fitz

import docx

logger = logging.getLogger(__name__)


@dataclass
class DocumentPage:
    """Represents a single extracted page or section of a document."""
    page_number: Optional[int]  # 1-based for PDF, None for DOCX/TXT
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedDocument:
    """Represents a fully ingested and validated document."""
    filename: str
    file_type: str  # 'pdf', 'docx', 'txt'
    total_pages: int
    pages: List[DocumentPage] = field(default_factory=list)
    is_scanned: bool = False
    warning_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def normalize_text(text: str) -> str:
    """Normalize extracted text, fixing ligatures, whitespace, and formatting."""
    if not text:
        return ""
    # Ligature and extraction artifact cleanup
    text = text.replace("/g415", "ti").replace("/g410", "ff").replace("/g414", "th")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Clean excessive whitespace per line while preserving indentation
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    collapsed = "\n".join(lines)
    # Collapse 3+ consecutive newlines to 2 (preserving paragraph breaks)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    return collapsed.strip()


class DocumentLoader:
    """Unified document loader for PDF, DOCX, and TXT files."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/octet-stream",
    }

    @classmethod
    def validate_file(
        cls,
        file_path: str,
        max_size_bytes: int = 15 * 1024 * 1024,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Validate file existence, extension, size, and MIME type.
        Returns the lowercase extension.
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(cls.SUPPORTED_EXTENSIONS))}"
            )

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size == 0:
            raise ValueError("The uploaded file is empty (0 bytes).")

        if file_size > max_size_bytes:
            max_mb = max_size_bytes / (1024 * 1024)
            raise ValueError(f"File size exceeds maximum allowed limit of {max_mb:.1f} MB.")

        if mime_type and mime_type.lower() not in cls.SUPPORTED_MIME_TYPES:
            logger.warning(f"Uncommon MIME type '{mime_type}' for extension '{ext}'")

        return ext

    @classmethod
    def load(cls, file_path: str, original_filename: Optional[str] = None) -> LoadedDocument:
        """Load and extract text from supported file types."""
        path = Path(file_path)
        ext = path.suffix.lower()
        display_name = original_filename or path.name

        cls.validate_file(file_path)

        if ext == ".pdf":
            return cls._load_pdf(path, display_name)
        elif ext == ".docx":
            return cls._load_docx(path, display_name)
        elif ext == ".txt":
            return cls._load_txt(path, display_name)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @classmethod
    def extract(cls, file_path: str, original_filename: Optional[str] = None) -> LoadedDocument:
        """Backwards-compatible alias for load()."""
        return cls.load(file_path, original_filename=original_filename)

    @classmethod
    def _load_pdf(cls, path: Path, filename: str) -> LoadedDocument:
        """Extract text page-by-page from PDF using PyMuPDF."""
        pages: List[DocumentPage] = []
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
                raw_text = page.get_text("text") or ""
                
                # Check for tables using PyMuPDF table finder if available
                table_text = ""
                try:
                    tables = page.find_tables()
                    if tables and tables.tables:
                        for table in tables:
                            table_rows = table.extract()
                            if table_rows:
                                formatted_rows = []
                                for r in table_rows:
                                    cells = [str(c).strip() if c else "" for c in r]
                                    formatted_rows.append(" | ".join(cells))
                                table_text += "\n\nTable:\n" + "\n".join(formatted_rows)
                except Exception:
                    pass  # Non-fatal if table parsing encounters unexpected layout

                page_text = raw_text + table_text
                cleaned = normalize_text(page_text)
                if cleaned:
                    total_chars += len(cleaned)

                # Preserve physical 1-based page number even if page is empty
                pages.append(
                    DocumentPage(
                        page_number=idx + 1,
                        text=cleaned,
                        metadata={"raw_char_count": len(raw_text), "has_tables": bool(table_text)}
                    )
                )
        finally:
            doc.close()

        # Heuristic for scanned/image-only PDFs
        avg_chars_per_page = total_chars / total_pages if total_pages > 0 else 0
        if total_chars == 0 or avg_chars_per_page < 15:
            is_scanned = True
            warning = (
                "Scanned or image-only PDF detected: insufficient readable text could be extracted. "
                "Optical Character Recognition (OCR) is not yet supported."
            )

        return LoadedDocument(
            filename=filename,
            file_type="pdf",
            total_pages=total_pages,
            pages=pages,
            is_scanned=is_scanned,
            warning_message=warning,
            metadata={"file_size": path.stat().st_size, "total_chars": total_chars}
        )

    @classmethod
    def _load_docx(cls, path: Path, filename: str) -> LoadedDocument:
        """Extract text from Word DOCX preserving paragraphs and tables."""
        try:
            doc = docx.Document(str(path))
        except Exception as e:
            raise ValueError(f"Failed to open or parse Word DOCX file: {str(e)}")

        parts: List[str] = []

        # Extract paragraphs with section references
        for p_idx, p in enumerate(doc.paragraphs):
            text = normalize_text(p.text)
            if text:
                parts.append(text)

        # Extract tables
        for t_idx, table in enumerate(doc.tables):
            table_lines = []
            for row in table.rows:
                cells = [normalize_text(cell.text) for cell in row.cells if cell.text.strip()]
                if cells:
                    table_lines.append(" | ".join(cells))
            if table_lines:
                parts.append("\nTable:\n" + "\n".join(table_lines))

        full_doc_text = "\n\n".join(parts).strip()
        warning = None if full_doc_text else "DOCX document contains no readable text."

        # Do not invent PDF-style page numbers: page_number is None for DOCX
        pages = [
            DocumentPage(
                page_number=None,
                text=full_doc_text,
                metadata={"sections": len(doc.sections), "paragraph_count": len(doc.paragraphs)}
            )
        ]

        return LoadedDocument(
            filename=filename,
            file_type="docx",
            total_pages=1,
            pages=pages,
            warning_message=warning,
            metadata={"file_size": path.stat().st_size}
        )

    @classmethod
    def _load_txt(cls, path: Path, filename: str) -> LoadedDocument:
        """Extract text from TXT with multi-encoding fallback."""
        raw_bytes = path.read_bytes()
        text = ""
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        cleaned = normalize_text(text)
        warning = None
        if not cleaned:
            warning = "Text file is empty or contains only whitespace."
        elif re.match(r"^https?://[^\s]+$", cleaned.strip()):
            warning = "This document contains only a web link. The AI Knowledge Assistant indexes text directly from files and does not crawl external websites. Please paste the actual story or document text into a file before uploading."

        # TXT files do not have page numbers: page_number is None
        pages = [
            DocumentPage(
                page_number=None,
                text=cleaned,
                metadata={"encoding_fallback": True}
            )
        ]

        return LoadedDocument(
            filename=filename,
            file_type="txt",
            total_pages=1,
            pages=pages,
            warning_message=warning,
            metadata={"file_size": path.stat().st_size}
        )
