"""Tests for RAG pipeline, grounding, citation generation, and fallbacks."""

import pytest
from unittest.mock import MagicMock
from backend.app.rag.pipeline import RAGPipeline
from backend.app.rag.chunker import DocumentChunk
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.vector_store import VectorStore


def test_rag_pipeline_with_mocked_llm(tmp_path):
    # Setup temporary vector store
    vs = VectorStore(persist_dir=str(tmp_path / "rag_chroma"), collection_name="test_rag")
    chunk = DocumentChunk(
        id="c1",
        document_id="doc_alpha",
        user_id=1,
        filename="solar_system.txt",
        page_number=1,
        chunk_index=0,
        text="The planet Mars has two small moons named Phobos and Deimos.",
        metadata={"document_id": "doc_alpha", "user_id": 1, "filename": "solar_system.txt", "page_number": 1, "chunk_index": 0}
    )
    vs.add_chunks([chunk], embedding_service.embed_documents([chunk.text]))

    # Mock OpenAI
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Mars has two moons: Phobos and Deimos."
    mock_res = MagicMock()
    mock_res.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_res

    pipeline = RAGPipeline(openai_client=mock_client)
    import backend.app.rag.vector_store as vs_module
    orig_vs = vs_module.vector_store
    vs_module.vector_store = vs

    try:
        answer, citations, grounded = pipeline.answer_question(
            question="What are the moons of Mars?",
            user_id=1
        )

        assert "Mars has two moons" in answer
        assert grounded is True
        assert len(citations) == 1
        assert citations[0].filename == "solar_system.txt"
        assert citations[0].page_number == 1
        assert "Phobos and Deimos" in citations[0].excerpt
    finally:
        vs_module.vector_store = orig_vs


def test_rag_pipeline_no_supporting_evidence(tmp_path):
    vs = VectorStore(persist_dir=str(tmp_path / "empty_chroma"), collection_name="test_empty")
    pipeline = RAGPipeline()

    import backend.app.rag.vector_store as vs_module
    orig_vs = vs_module.vector_store
    vs_module.vector_store = vs

    try:
        answer, citations, grounded = pipeline.answer_question(
            question="What is the airspeed velocity of an unladen swallow?",
            user_id=999
        )
        assert "cannot find the answer" in answer.lower()
        assert len(citations) == 0
        assert grounded is False
    finally:
        vs_module.vector_store = orig_vs
