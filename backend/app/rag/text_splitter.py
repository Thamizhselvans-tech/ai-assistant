"""Text splitting engine preserving page-level metadata and using LangChain RecursiveCharacterTextSplitter."""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    class RecursiveCharacterTextSplitter:  # type: ignore
        """Resilient native fallback text splitter when langchain_text_splitters is unavailable."""
        def __init__(
            self,
            chunk_size: int = 1000,
            chunk_overlap: int = 200,
            separators: Optional[List[str]] = None,
            keep_separator: bool = True
        ):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
            self.keep_separator = keep_separator

        def split_text(self, text: str) -> List[str]:
            if not text:
                return []
            chunks: List[str] = []
            step = max(1, self.chunk_size - self.chunk_overlap)
            for i in range(0, len(text), step):
                chunk = text[i:i + self.chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
                if i + self.chunk_size >= len(text):
                    break
            return chunks

from backend.app.rag.document_loader import LoadedDocument


@dataclass
class DocumentChunk:
    """Represents a text chunk with complete provenance metadata."""
    id: str
    document_id: str
    user_id: int
    filename: str
    page_number: Optional[int] = None
    chunk_index: int = 0
    text: str = ""
    file_type: str = "txt"
    upload_timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now(timezone.utc).isoformat()
        if not self.metadata:
            self.metadata = {
                "document_id": str(self.document_id),
                "user_id": int(self.user_id),
                "filename": str(self.filename),
                "file_type": str(self.file_type),
                "chunk_index": int(self.chunk_index),
                "upload_timestamp": str(self.upload_timestamp),
                "char_count": len(self.text),
            }
            if self.page_number is not None:
                self.metadata["page_number"] = int(self.page_number)
        else:
            self.metadata.setdefault("document_id", str(self.document_id))
            self.metadata.setdefault("user_id", int(self.user_id))
            self.metadata.setdefault("filename", str(self.filename))
            self.metadata.setdefault("file_type", str(self.file_type))
            self.metadata.setdefault("chunk_index", int(self.chunk_index))
            self.metadata.setdefault("upload_timestamp", str(self.upload_timestamp))
            self.metadata.setdefault("char_count", len(self.text))
            if self.page_number is not None:
                self.metadata.setdefault("page_number", int(self.page_number))


class DocumentTextSplitter:
    """Chunks documents into overlapping segments with metadata preservation."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )

    def split_document(
        self,
        document: LoadedDocument,
        document_id: str,
        user_id: int,
        upload_timestamp: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Split a LoadedDocument into structured chunks.
        Splits page-by-page to guarantee original page metadata is never lost.
        """
        timestamp = upload_timestamp or datetime.now(timezone.utc).isoformat()
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in document.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Split text on this specific page
            page_segments = self.splitter.split_text(page_text)

            for seg in page_segments:
                seg_clean = seg.strip()
                if not seg_clean:
                    continue

                chunk_id = f"{document_id}_{global_chunk_idx}"
                meta: Dict[str, Any] = {
                    "document_id": str(document_id),
                    "user_id": int(user_id),
                    "filename": str(document.filename),
                    "file_type": str(document.file_type),
                    "chunk_index": int(global_chunk_idx),
                    "upload_timestamp": str(timestamp),
                    "char_count": len(seg_clean),
                }
                if page.page_number is not None:
                    meta["page_number"] = int(page.page_number)

                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        user_id=user_id,
                        filename=document.filename,
                        file_type=document.file_type,
                        page_number=page.page_number,
                        chunk_index=global_chunk_idx,
                        text=seg_clean,
                        upload_timestamp=timestamp,
                        metadata=meta
                    )
                )
                global_chunk_idx += 1

        return chunks
