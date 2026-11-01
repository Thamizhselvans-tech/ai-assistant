"""Comprehensive Phase 2 Test Suite: Document Ingestion, Chunking, Embeddings, ChromaDB, Retriever, and Prompts."""

import io
import os
import math
import tempfile
import pytest
import docx

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from backend.app.rag.document_loader import DocumentLoader, DocumentPage, LoadedDocument, normalize_text
from backend.app.rag.text_splitter import DocumentTextSplitter, DocumentChunk
from backend.app.rag.embeddings import EmbeddingService, embedding_service
from backend.app.rag.vector_store import VectorStore, SearchResult
from backend.app.rag.retriever import SemanticRetriever
from backend.app.rag.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    INSUFFICIENT_EVIDENCE_ANSWER,
    format_context,
    build_rag_prompt,
)


# ==========================================
# 1. DOCUMENT LOADING TESTS
# ==========================================

def test_document_loader_pdf_multipage_and_pages():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text((72, 72), "First page: Retrieval-Augmented Generation architectures in enterprise software.")
        p2 = doc.new_page()
        p2.insert_text((72, 72), "Second page: Dense vector embeddings and approximate nearest neighbor search.")
        doc.save(pdf_path)
        doc.close()

        loaded = DocumentLoader.load(pdf_path, original_filename="rag_paper.pdf")
        assert loaded.file_type == "pdf"
        assert loaded.total_pages == 2
        assert len(loaded.pages) == 2
        assert loaded.pages[0].page_number == 1
        assert loaded.pages[1].page_number == 2
        assert "Retrieval-Augmented Generation" in loaded.pages[0].text
        assert "nearest neighbor" in loaded.pages[1].text
        assert loaded.is_scanned is False
        assert loaded.warning_message is None
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_document_loader_pdf_scanned_detection():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        # Create a PDF with empty pages simulating image-only scanned document
        doc = fitz.open()
        _ = doc.new_page()
        doc.save(pdf_path)
        doc.close()

        loaded = DocumentLoader.load(pdf_path, original_filename="scanned_report.pdf")
        assert loaded.is_scanned is True
        assert loaded.warning_message is not None
        assert "OCR" in loaded.warning_message
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_document_loader_docx_paragraphs_and_tables():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        docx_path = f.name

    try:
        doc_obj = docx.Document()
        doc_obj.add_heading("Section 1: Architecture", level=1)
        doc_obj.add_paragraph("The application backend uses FastAPI for API routing and SQLite for persistence.")

        tbl = doc_obj.add_table(rows=2, cols=2)
        tbl.rows[0].cells[0].text = "Module"
        tbl.rows[0].cells[1].text = "Technology"
        tbl.rows[1].cells[0].text = "VectorDB"
        tbl.rows[1].cells[1].text = "ChromaDB"
        doc_obj.save(docx_path)

        loaded = DocumentLoader.load(docx_path, original_filename="architecture.docx")
        assert loaded.file_type == "docx"
        assert len(loaded.pages) == 1
        # Crucial requirement: DOCX does not have physical PDF page numbers; page_number is None
        assert loaded.pages[0].page_number is None
        assert "Architecture" in loaded.full_text
        assert "FastAPI" in loaded.full_text
        assert "VectorDB | ChromaDB" in loaded.full_text
        assert loaded.is_scanned is False
    finally:
        if os.path.exists(docx_path):
            os.unlink(docx_path)


def test_document_loader_txt_encodings():
    with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as f:
        # Test UTF-8 with BOM
        f.write(b"\xef\xbb\xbfQuantum computing leverages superposition and entanglement.")
        txt_path = f.name

    try:
        loaded = DocumentLoader.load(txt_path, original_filename="quantum.txt")
        assert loaded.file_type == "txt"
        assert loaded.pages[0].page_number is None
        assert "Quantum computing" in loaded.full_text
        assert "superposition" in loaded.full_text
    finally:
        if os.path.exists(txt_path):
            os.unlink(txt_path)


# ==========================================
# 2. TEXT SPLITTER & METADATA TESTS
# ==========================================

def test_text_splitter_chunking_and_metadata_preservation():
    splitter = DocumentTextSplitter(chunk_size=200, chunk_overlap=40)

    # Multi-page loaded document
    doc = LoadedDocument(
        filename="distributed_systems.pdf",
        file_type="pdf",
        total_pages=2,
        pages=[
            DocumentPage(
                page_number=1,
                text="The CAP theorem states that a distributed data store can only simultaneously provide at most two of the following three guarantees: Consistency, Availability, and Partition tolerance."
            ),
            DocumentPage(
                page_number=2,
                text="Consensus algorithms such as Raft and Paxos ensure state machine replication across a cluster of nodes even in the presence of network partitions and node crashes."
            )
        ]
    )

    chunks = splitter.split_document(doc, document_id="doc_dist_01", user_id=42)
    assert len(chunks) >= 2

    for chunk in chunks:
        assert chunk.document_id == "doc_dist_01"
        assert chunk.user_id == 42
        assert chunk.filename == "distributed_systems.pdf"
        assert chunk.file_type == "pdf"
        assert chunk.page_number in (1, 2)
        assert isinstance(chunk.chunk_index, int)
        assert chunk.upload_timestamp != ""
        assert "char_count" in chunk.metadata
        assert chunk.metadata["char_count"] == len(chunk.text)
        assert chunk.metadata["document_id"] == "doc_dist_01"
        assert chunk.metadata["user_id"] == 42


def test_text_splitter_docx_none_page_number():
    splitter = DocumentTextSplitter(chunk_size=150, chunk_overlap=30)
    doc = LoadedDocument(
        filename="notes.docx",
        file_type="docx",
        total_pages=1,
        pages=[
            DocumentPage(
                page_number=None,
                text="Meeting notes regarding project roadmap and Q3 deliverables. All milestones are currently on track."
            )
        ]
    )

    chunks = splitter.split_document(doc, document_id="doc_docx_01", user_id=7)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.page_number is None
        assert "page_number" not in chunk.metadata  # Ensure not artificially added


def test_text_splitter_invalid_overlap():
    with pytest.raises(ValueError):
        DocumentTextSplitter(chunk_size=500, chunk_overlap=500)

    with pytest.raises(ValueError):
        DocumentTextSplitter(chunk_size=300, chunk_overlap=400)


# ==========================================
# 3. EMBEDDING SERVICE TESTS
# ==========================================

def test_embedding_service_dimensions_and_normalization():
    service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
    assert service.embedding_dimension == 384

    # Test single query embedding
    q_vec = service.embed_query("What is semantic search?")
    assert len(q_vec) == 384
    # Check L2 normalization (norm should be ~1.0)
    norm = math.sqrt(sum(x * x for x in q_vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-3)

    # Test batch document embeddings
    texts = [
        "First document about artificial neural networks.",
        "Second document regarding vector database indexing.",
        "Third document on transformer self-attention mechanisms."
    ]
    doc_vectors = service.embed_documents(texts, batch_size=2)
    assert len(doc_vectors) == 3
    for vec in doc_vectors:
        assert len(vec) == 384
        v_norm = math.sqrt(sum(x * x for x in vec))
        assert math.isclose(v_norm, 1.0, rel_tol=1e-3)

    # Test empty handling
    assert service.embed_query("") == []
    assert service.embed_documents([]) == []


# ==========================================
# 4. CHROMADB VECTOR STORE TESTS
# ==========================================

def test_chromadb_operations_and_isolation(tmp_path):
    persist_dir = str(tmp_path / "chroma_test")
    vs = VectorStore(persist_dir=persist_dir, collection_name="test_phase2_collection")

    chunk_a = DocumentChunk(
        id="chunk_a1",
        document_id="doc_a",
        user_id=100,
        filename="alice_confidential.txt",
        file_type="txt",
        page_number=None,
        chunk_index=0,
        text="Alice's secret code is Project Emerald Horizon.",
        metadata={"document_id": "doc_a", "user_id": 100, "filename": "alice_confidential.txt"}
    )

    chunk_b = DocumentChunk(
        id="chunk_b1",
        document_id="doc_b",
        user_id=200,
        filename="bob_notes.txt",
        file_type="txt",
        page_number=None,
        chunk_index=0,
        text="Bob is studying satellite orbits and orbital decay.",
        metadata={"document_id": "doc_b", "user_id": 200, "filename": "bob_notes.txt"}
    )

    emb_a = embedding_service.embed_documents([chunk_a.text])
    emb_b = embedding_service.embed_documents([chunk_b.text])

    # Insert chunks
    vs.add_chunks([chunk_a], emb_a)
    vs.add_chunks([chunk_b], emb_b)

    assert vs.count() == 2
    assert vs.document_exists("doc_a", user_id=100) is True
    assert vs.document_exists("doc_a", user_id=200) is False  # User 200 does not own doc_a

    # Search with user isolation: User 200 searching for Alice's secret must return NOTHING
    q_vec = embedding_service.embed_query("Project Emerald Horizon")
    results_user_b = vs.search(query_embedding=q_vec, user_id=200, top_k=5)
    assert len(results_user_b) == 0

    # User 100 searching for Alice's secret should retrieve chunk_a
    results_user_a = vs.search(query_embedding=q_vec, user_id=100, top_k=5)
    assert len(results_user_a) >= 1
    assert results_user_a[0].document_id == "doc_a"
    assert "Emerald Horizon" in results_user_a[0].text

    # Reindex document
    chunk_a_updated = DocumentChunk(
        id="chunk_a_updated_0",
        document_id="doc_a",
        user_id=100,
        filename="alice_confidential.txt",
        file_type="txt",
        page_number=None,
        chunk_index=0,
        text="Alice's updated code is Project Diamond Summit.",
        metadata={"document_id": "doc_a", "user_id": 100, "filename": "alice_confidential.txt"}
    )
    new_emb = embedding_service.embed_documents([chunk_a_updated.text])
    vs.reindex_document(document_id="doc_a", user_id=100, chunks=[chunk_a_updated], embeddings=new_emb)
    assert vs.count() == 2  # Old chunk was purged, new chunk inserted

    # Delete document doc_a
    deleted_count = vs.delete_document_chunks("doc_a", user_id=100)
    assert deleted_count == 1
    assert vs.document_exists("doc_a", user_id=100) is False
    assert vs.count() == 1  # Only chunk_b remains


# ==========================================
# 5. RETRIEVER TESTS
# ==========================================

def test_semantic_retriever(tmp_path):
    persist_dir = str(tmp_path / "chroma_retriever")
    vs = VectorStore(persist_dir=persist_dir, collection_name="test_retriever")
    retriever = SemanticRetriever(
        default_top_k=3,
        default_threshold=0.35,
        vector_store_instance=vs,
        embedding_service_instance=embedding_service
    )

    chunk1 = DocumentChunk(
        id="ret_1",
        document_id="astro_doc",
        user_id=50,
        filename="astronomy.pdf",
        file_type="pdf",
        page_number=3,
        chunk_index=0,
        text="The Hubble Space Telescope was launched into low Earth orbit in 1990.",
        metadata={"document_id": "astro_doc", "user_id": 50, "filename": "astronomy.pdf", "page_number": 3}
    )
    vs.add_chunks([chunk1], embedding_service.embed_documents([chunk1.text]))

    # Relevant query
    matches = retriever.retrieve("When was the Hubble Space Telescope launched?", user_id=50)
    assert len(matches) == 1
    assert matches[0].document_id == "astro_doc"
    assert matches[0].page_number == 3
    assert matches[0].score > 0.35

    # Completely irrelevant query filtered out by threshold
    irrelevant_matches = retriever.retrieve("How do you bake a sourdough loaf from scratch?", user_id=50)
    assert len(irrelevant_matches) == 0

    # User isolation check
    other_user_matches = retriever.retrieve("Hubble Space Telescope", user_id=99)
    assert len(other_user_matches) == 0


# ==========================================
# 6. PROMPT & CITATION FORMATTING TESTS
# ==========================================

def test_prompt_and_context_formatting():
    chunks = [
        SearchResult(
            document_id="doc_pdf",
            filename="whitepaper.pdf",
            page_number=4,
            chunk_index=2,
            text="Distributed consensus guarantees safety under partial synchrony.",
            score=0.88
        ),
        SearchResult(
            document_id="doc_docx",
            filename="notes.docx",
            page_number=None,  # No physical page number
            chunk_index=0,
            text="Team standup notes from Monday morning.",
            score=0.75
        )
    ]

    formatted_context = format_context(chunks)
    assert "[Source 1 | Document: whitepaper.pdf | Page 4 | Chunk 2" in formatted_context
    assert "[Source 2 | Document: notes.docx | Page N/A | Chunk 0" in formatted_context
    assert "Distributed consensus guarantees" in formatted_context

    prompt = build_rag_prompt("What does consensus guarantee?", chunks)
    assert "<context>" in prompt
    assert "</context>" in prompt
    assert "Question: What does consensus guarantee?" in prompt
    assert "Page 4" in prompt

    # Empty context handling
    empty_ctx = format_context([])
    assert "No relevant document excerpts" in empty_ctx
    assert INSUFFICIENT_EVIDENCE_ANSWER == "I cannot find the answer to this question in the uploaded documents."
