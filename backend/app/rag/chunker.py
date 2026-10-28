"""Text chunking engine with metadata preservation and sliding window overlap."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from backend.app.rag.extractors import ExtractedDocument


@dataclass
class DocumentChunk:
    id: str
    document_id: str
    user_id: int
    filename: str
    page_number: Optional[int]
    chunk_index: int
    text: str
    metadata: Dict[str, object] = field(default_factory=dict)


class TextChunker:
    """Chunks documents into overlapping text segments with rich metadata."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        extracted_doc: ExtractedDocument,
        document_id: str,
        user_id: int
    ) -> List[DocumentChunk]:
        """Split an extracted document into structured, overlapping chunks."""
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in extracted_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Split page text into overlapping segments
            page_chunks = self._split_text(page_text)
            for seg in page_chunks:
                chunk_id = f"{document_id}_{global_chunk_idx}"
                meta = {
                    "document_id": str(document_id),
                    "user_id": int(user_id),
                    "filename": str(extracted_doc.filename),
                    "page_number": int(page.page_number) if page.page_number else 1,
                    "chunk_index": int(global_chunk_idx),
                    "char_count": len(seg),
                }
                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        user_id=user_id,
                        filename=extracted_doc.filename,
                        page_number=page.page_number,
                        chunk_index=global_chunk_idx,
                        text=seg,
                        metadata=meta
                    )
                )
                global_chunk_idx += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Split text into segments of length up to chunk_size with overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)
        step = self.chunk_size - self.chunk_overlap

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end]

            # If not at the end of the text, try to break cleanly at paragraph or sentence
            if end < text_len:
                # Look for paragraph break
                para_break = chunk.rfind("\n\n")
                if para_break > self.chunk_size // 3:
                    chunk = chunk[:para_break]
                    end = start + para_break + 2
                else:
                    # Look for sentence boundary (. ! ?)
                    match = re.search(r"[\.!?]\s+[A-Z]", chunk[::-1])
                    if match:
                        cut = len(chunk) - match.start()
                        if cut > self.chunk_size // 3:
                            chunk = chunk[:cut]
                            end = start + cut
                    else:
                        # Fallback: break at last whitespace
                        space_break = chunk.rfind(" ")
                        if space_break > self.chunk_size // 3:
                            chunk = chunk[:space_break]
                            end = start + space_break + 1

            chunk_clean = chunk.strip()
            if chunk_clean:
                chunks.append(chunk_clean)

            if end >= text_len:
                break
            
            # Advance start with step or aligned with cut point minus overlap
            start = max(start + step, end - self.chunk_overlap)
            if start >= text_len:
                break

        return chunks
