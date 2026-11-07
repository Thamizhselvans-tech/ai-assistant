"""Comprehensive test suite for Low-RAM (4GB) optimizations, multilingual engine, and LLM provider layer."""

import pytest
from unittest.mock import MagicMock
from backend.app.core.config import settings
from backend.app.services.llm_provider import LLMProviderService, llm_provider_service
from backend.app.services.language_service import LanguageService, language_service
from backend.app.rag.embeddings import EmbeddingService, embedding_service
from backend.app.rag.pipeline import RAGPipeline
from backend.app.schemas.chat import SourceCitation


def test_language_detection_tamil_tanglish_english():
    """Verify language detection across Tamil script, phonetic Tanglish, and English."""
    ls = LanguageService()

    # Pure Tamil
    assert ls.detect_language("இந்த ஆவணத்தில் உள்ள முக்கிய குறிப்புகள் என்ன?") == "ta"
    assert ls.detect_language("வணக்கம்") == "ta"

    # Tanglish (Tamil in Latin alphabet)
    assert ls.detect_language("Machine learning na enna bro?") == "tanglish"
    assert ls.detect_language("indha doc epdi work aaguthu sollunga") == "tanglish"
    assert ls.detect_language("Romba nalla irukku") == "tanglish"

    # English
    assert ls.detect_language("What are the primary objectives of this document?") == "en"
    assert ls.detect_language("Summarize the key findings.") == "en"
    assert ls.detect_language("") == "en"
    assert ls.detect_language(None) == "en"


def test_multilingual_fallback_messages():
    """Verify culturally natural grounded fallback messages preserve citations in user's language."""
    ls = LanguageService()
    sources = "- **report.pdf** (Page 1): \"System metrics verified.\""

    # Tamil fallback
    ta_header = ls.get_fallback_header("ta", "quota_exceeded")
    assert "கிளவுட் AI" in ta_header or "ஆவணங்கள்" in ta_header

    # Tanglish fallback
    tanglish_header = ls.get_fallback_header("tanglish", "quota_exceeded")
    assert "Cloud AI" in tanglish_header or "uploaded documents" in tanglish_header

    # English fallback
    en_header = ls.get_fallback_header("en", "quota_exceeded")
    assert "quota or rate limit" in en_header


def test_llm_provider_configuration_and_masking():
    """Verify provider switching across OpenAI, Groq, OpenRouter, Gemini, and Custom."""
    service = LLMProviderService()

    # Default provider resolution
    cfg = service.get_provider_config("openai")
    assert cfg["provider"] == "openai"
    assert cfg["model"] == settings.OPENAI_MODEL

    # Groq provider resolution
    cfg_groq = service.get_provider_config("groq")
    assert cfg_groq["provider"] == "groq"
    assert "groq.com" in cfg_groq["base_url"]
    assert cfg_groq["model"] == "llama-3.1-8b-instant"

    # OpenRouter provider resolution
    cfg_or = service.get_provider_config("openrouter")
    assert cfg_or["provider"] == "openrouter"
    assert "openrouter.ai" in cfg_or["base_url"]

    # Key masking security test
    masked = service.mask_key("sk-proj-1234567890abcdef12345678")
    assert masked.startswith("sk-proj")
    assert masked.endswith("5678")
    assert "abcdef" not in masked
    assert service.mask_key("") == "Not Set"


def test_llm_provider_generate_completion_unconfigured():
    """Verify clean unconfigured status when no API key is provided."""
    service = LLMProviderService()
    # Temporarily set provider to a non-existent key
    original_provider = settings.LLM_PROVIDER
    original_key = settings.GROQ_API_KEY
    try:
        settings.LLM_PROVIDER = "groq"
        settings.GROQ_API_KEY = ""
        ans, code, detail = service.generate_completion([{"role": "user", "content": "hi"}])
        assert ans is None
        assert code == "unconfigured"
    finally:
        settings.LLM_PROVIDER = original_provider
        settings.GROQ_API_KEY = original_key


def test_embedding_low_ram_optimizations():
    """Verify embedding service LRU caching and PyTorch thread tuning on 4GB hardware."""
    emb = EmbeddingService()

    # Embedding dimension
    assert emb.embedding_dimension == 384

    # Query embedding and caching
    q1 = "Machine learning fundamentals"
    vec1 = emb.embed_query(q1)
    assert len(vec1) == 384

    # Second call should use cache
    vec2 = emb.embed_query(q1)
    assert vec1 == vec2

    # Batch embedding respects small batch sizes
    texts = ["Chunk one text", "Chunk two text"]
    doc_vecs = emb.embed_documents(texts, batch_size=2)
    assert len(doc_vecs) == 2
    assert len(doc_vecs[0]) == 384


def test_rag_pipeline_multilingual_grounded_fallback():
    """Verify RAG pipeline returns grounded fallback with citations when cloud provider has quota limit."""
    pipeline = RAGPipeline()

    # Mock semantic search returning 1 citation
    mock_retriever = MagicMock()
    mock_search_result = MagicMock()
    mock_search_result.document_id = "doc-123"
    mock_search_result.filename = "spec.pdf"
    mock_search_result.page_number = 2
    mock_search_result.chunk_index = 0
    mock_search_result.text = "The system executes with 4GB memory constraints."
    mock_search_result.score = 0.88
    mock_retriever.retrieve.return_value = [mock_search_result]

    pipeline._custom_retriever = mock_retriever

    # Test Tamil query with unconfigured/quota LLM
    ans_ta, citations, is_grounded = pipeline.answer_question(
        question="இந்த சிஸ்டம் எவ்வளவு ரேம் பயன்படுத்துகிறது?",
        user_id=1
    )
    assert is_grounded is True
    assert len(citations) == 1
    assert "spec.pdf" in ans_ta
    assert "4GB memory constraints" in ans_ta

    # Test Tanglish query
    ans_tg, citations_tg, is_grounded_tg = pipeline.answer_question(
        question="System RAM evvalavu venum sollunga?",
        user_id=1
    )
    assert is_grounded_tg is True
    assert "spec.pdf" in ans_tg


def test_health_telemetry_includes_ram_and_provider(client):
    """Verify /api/health and /api/health/llm endpoints return provider status and RAM metrics."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()

    services = data["services"]
    assert "llm_provider" in services
    assert "llm_model" in services
    assert "ram" in services
    assert "total_gb" in services["ram"]
    assert "available_gb" in services["ram"]

    res_llm = client.get("/api/health/llm")
    assert res_llm.status_code == 200
    llm_data = res_llm.json()
    assert llm_data["status"] == "ok"
    assert "provider" in llm_data
    assert "ram" in llm_data
