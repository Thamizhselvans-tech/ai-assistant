"""Compatibility wrapper for TextChunker aliasing DocumentTextSplitter."""

from typing import List, Optional
from backend.app.rag.document_loader import LoadedDocument
from backend.app.rag.text_splitter import DocumentChunk, DocumentTextSplitter


class TextChunker(DocumentTextSplitter):
    """Backwards-compatible wrapper supporting chunk_document method."""

    def chunk_document(
        self,
        extracted_doc: LoadedDocument,
        document_id: str,
        user_id: int
    ) -> List[DocumentChunk]:
        return self.split_document(
            document=extracted_doc,
            document_id=document_id,
            user_id=user_id
        )


__all__ = ["DocumentChunk", "TextChunker", "DocumentTextSplitter"]
