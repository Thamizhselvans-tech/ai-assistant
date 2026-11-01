"""Compatibility wrapper for DocumentExtractor aliasing DocumentLoader."""

from backend.app.rag.document_loader import (
    DocumentPage as ExtractedPage,
    LoadedDocument as ExtractedDocument,
    DocumentLoader as DocumentExtractor,
    normalize_text,
)

__all__ = ["ExtractedPage", "ExtractedDocument", "DocumentExtractor", "normalize_text"]
