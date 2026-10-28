"""Tests for document chunking and metadata preservation."""

import pytest
from backend.app.rag.chunker import TextChunker, DocumentChunk
from backend.app.rag.extractors import ExtractedDocument, ExtractedPage


def test_chunker_overlap_validation():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=500, chunk_overlap=500)


def test_chunking_short_document():
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    doc = ExtractedDocument(
        filename="short.txt",
        file_type="txt",
        total_pages=1,
        pages=[ExtractedPage(page_number=1, text="Short text that fits in one chunk.")]
    )
    chunks = chunker.chunk_document(doc, document_id="doc-123", user_id=1)
    assert len(chunks) == 1
    assert chunks[0].id == "doc-123_0"
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata["filename"] == "short.txt"
    assert chunks[0].metadata["user_id"] == 1


def test_chunking_multipage_preserves_page_numbers():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    doc = ExtractedDocument(
        filename="multipage.pdf",
        file_type="pdf",
        total_pages=2,
        pages=[
            ExtractedPage(page_number=1, text="Page 1 content about machine learning models and supervised algorithms."),
            ExtractedPage(page_number=2, text="Page 2 content about deep neural networks and attention mechanisms.")
        ]
    )
    chunks = chunker.chunk_document(doc, document_id="doc-456", user_id=2)
    assert len(chunks) >= 2
    # Verify page numbers match source pages
    page1_chunks = [c for c in chunks if c.page_number == 1]
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(page1_chunks) > 0
    assert len(page2_chunks) > 0
    assert "machine learning" in page1_chunks[0].text
    assert "neural networks" in page2_chunks[0].text
