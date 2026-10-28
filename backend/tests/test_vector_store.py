"""Tests for ChromaDB vector store, user isolation, and semantic search."""

import pytest
from backend.app.rag.chunker import DocumentChunk
from backend.app.rag.vector_store import VectorStore
from backend.app.rag.embeddings import embedding_service


def test_vector_store_add_search_and_isolation(tmp_path):
    # Create isolated ChromaDB instance
    vs = VectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test_isolation")

    chunk_u1 = DocumentChunk(
        id="doc1_0",
        document_id="doc1",
        user_id=10,
        filename="alice_secrets.txt",
        page_number=1,
        chunk_index=0,
        text="Alice's confidential project code name is Project Neptune.",
        metadata={"document_id": "doc1", "user_id": 10, "filename": "alice_secrets.txt", "page_number": 1, "chunk_index": 0}
    )

    chunk_u2 = DocumentChunk(
        id="doc2_0",
        document_id="doc2",
        user_id=20,
        filename="bob_notes.txt",
        page_number=1,
        chunk_index=0,
        text="Bob's project code name is Project Jupiter.",
        metadata={"document_id": "doc2", "user_id": 20, "filename": "bob_notes.txt", "page_number": 1, "chunk_index": 0}
    )

    # Embed and add
    emb1 = embedding_service.embed_documents([chunk_u1.text])
    emb2 = embedding_service.embed_documents([chunk_u2.text])
    vs.add_chunks([chunk_u1], emb1)
    vs.add_chunks([chunk_u2], emb2)

    # Search as User 10 for "project code name"
    query_emb = embedding_service.embed_query("What is the project code name?")
    results_u1 = vs.search(query_emb, user_id=10, top_k=5, similarity_threshold=0.1)

    assert len(results_u1) == 1
    assert results_u1[0].user_id == 10
    assert "Neptune" in results_u1[0].text
    assert "Jupiter" not in results_u1[0].text  # Critical: Bob's data must NEVER be returned to Alice

    # Search as User 20
    results_u2 = vs.search(query_emb, user_id=20, top_k=5, similarity_threshold=0.1)
    assert len(results_u2) == 1
    assert results_u2[0].user_id == 20
    assert "Jupiter" in results_u2[0].text

    # Test document deletion
    deleted_count = vs.delete_document_chunks("doc1", user_id=10)
    assert deleted_count >= 1

    # Search again for User 10 after deletion
    results_u1_after = vs.search(query_emb, user_id=10, top_k=5, similarity_threshold=0.1)
    assert len(results_u1_after) == 0
