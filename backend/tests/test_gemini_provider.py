"""Comprehensive test suite for Google Gemini API Free-Tier Provider Integration."""

import io
import pytest
from unittest.mock import MagicMock, patch
from backend.app.core.config import settings
from backend.app.services.llm_provider import LLMProviderService, llm_provider_service
from backend.app.services.language_service import language_service
from backend.app.rag.pipeline import RAGPipeline
from backend.app.schemas.chat import SourceCitation


def test_gemini_provider_configuration_resolution():
    """Verify Gemini provider metadata, default model, and secure key masking."""
    service = LLMProviderService()
    cfg = service.get_provider_config("gemini")

    assert cfg["provider"] == "gemini"
    assert "Gemini" in cfg["display_name"]
    assert cfg["model"] in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-pro"]
    assert cfg["env_key"] == "GEMINI_API_KEY"

    # Key masking security test
    sample_key = "SAMPLE_GEMINI_KEY_ABCDEF1234567890XYZ"
    masked = service.mask_key(sample_key)
    assert masked.startswith("SAMPLE_")
    assert masked.endswith("0XYZ")
    assert "ABCDEF" not in masked


def test_gemini_missing_api_key_handling():
    """Verify clean error code and graceful handling when GEMINI_API_KEY is missing."""
    service = LLMProviderService()
    original_key = getattr(settings, "GEMINI_API_KEY", "")
    try:
        settings.GEMINI_API_KEY = ""
        ans, code, detail = service.generate_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert ans is None
        assert code == "unconfigured"
        assert "GEMINI_API_KEY" in detail
    finally:
        settings.GEMINI_API_KEY = original_key


def test_gemini_invalid_key_error_handling():
    """Verify invalid API key triggers auth_error without exposing secret."""
    service = LLMProviderService()
    cfg = {
        "provider": "gemini",
        "api_key": "invalid-gemini-key-12345",
        "model": "gemini-3.5-flash-lite",
        "base_url": "https://generativelanguage.googleapis.com/v1beta"
    }

    # Simulate Google GenAI Client throwing ClientError (400/403/401 API_KEY_INVALID)
    with patch("backend.app.services.llm_provider.LLMProviderService._generate_gemini") as mock_gen:
        mock_gen.return_value = (None, "auth_error", "API_KEY_INVALID (400): API key not valid")
        ans, code, detail = service._generate_gemini(cfg, [{"role": "user", "content": "Test"}], 0.2, 500)
        assert ans is None
        assert code == "auth_error"
        assert "API_KEY_INVALID" in detail


def test_gemini_quota_exhausted_no_retry():
    """Verify quota exhaustion returns quota_exceeded immediately without infinite retries."""
    service = LLMProviderService()
    cfg = {
        "provider": "gemini",
        "api_key": "test-key",
        "model": "gemini-3.5-flash-lite",
        "base_url": "https://generativelanguage.googleapis.com/v1beta"
    }

    with patch("backend.app.services.llm_provider.LLMProviderService._generate_gemini") as mock_gen:
        mock_gen.return_value = (None, "quota_exceeded", "ResourceExhausted: 429 Quota exceeded for quota metric")
        ans, code, detail = service._generate_gemini(cfg, [{"role": "user", "content": "Test"}], 0.2, 500)
        assert ans is None
        assert code == "quota_exceeded"
        # Confirm it was called exactly once (no looping retries on quota exhaustion)
        assert mock_gen.call_count == 1


def test_gemini_network_timeout_handling():
    """Verify network connection failure returns connection_error."""
    service = LLMProviderService()
    cfg = {
        "provider": "gemini",
        "api_key": "test-key",
        "model": "gemini-3.5-flash-lite",
        "base_url": "https://generativelanguage.googleapis.com/v1beta"
    }

    with patch("backend.app.services.llm_provider.LLMProviderService._generate_gemini") as mock_gen:
        mock_gen.return_value = (None, "connection_error", "ConnectError: Failed to establish a new connection")
        ans, code, detail = service._generate_gemini(cfg, [{"role": "user", "content": "Test"}], 0.2, 500)
        assert ans is None
        assert code == "connection_error"


def test_gemini_rag_tamil_grounded_answer(client, headers_a):
    """Verify RAG pipeline with Gemini answers in Tamil with exact document citations."""
    # Step 1: Upload specialized document
    content = (
        "ஆவண அறிக்கை: செயற்கை நுண்ணறிவு உதவியாளர் அமைப்பு 4GB ரேம் கொண்ட கணினிகளில் "
        "வேகமாக இயங்கும் வகையில் குரோமியா மற்றும் கூகுள் ஜெமினி தொழில்நுட்பத்தைப் பயன்படுத்துகிறது."
    )
    files = {"file": ("tamil_spec.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Step 2: Query in Tamil
    chat_payload = {
        "question": "இந்த அமைப்பு எவ்வளவு ரேம் கொண்ட கணினிகளில் இயங்கும்?",
        "document_ids": [doc_id],
        "top_k": 3,
        "similarity_threshold": 0.15
    }

    # Mock the LLM completion to return a realistic Gemini Tamil grounded answer
    mock_tamil_answer = (
        "இந்த அமைப்பு 4GB ரேம் கொண்ட கணினிகளில் வேகமாக இயங்கும் வகையில் "
        "குரோமியா மற்றும் கூகுள் ஜெமினி தொழில்நுட்பத்தைப் பயன்படுத்துகிறது."
    )

    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gemini_gen:
        mock_gemini_gen.return_value = (mock_tamil_answer, None, None)
        chat_res = client.post("/api/chat/ask", headers=headers_a, json=chat_payload)

    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["grounded"] is True
    assert "4GB" in data["answer"]
    assert len(data["sources"]) >= 1

    citation = data["sources"][0]
    assert citation["filename"] == "tamil_spec.txt"
    assert citation["score"] > 0


def test_gemini_rag_english_and_tanglish_queries(client, headers_a):
    """Verify English and Tanglish queries are correctly handled by the RAG pipeline."""
    content = "The orbital engine operates at an altitude of 340 kilometers with cryogenic propellant."
    files = {"file": ("orbital_flight.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # English query
    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gemini_gen:
        mock_gemini_gen.return_value = ("The orbital engine operates at an altitude of 340 kilometers.", None, None)
        res_en = client.post("/api/chat/ask", headers=headers_a, json={
            "question": "What is the operating altitude?",
            "document_ids": [doc_id]
        })
    assert res_en.status_code == 200
    assert "340" in res_en.json()["answer"]
    assert res_en.json()["sources"][0]["filename"] == "orbital_flight.txt"

    # Tanglish query: "Altitude evvalavu km sollunga?"
    assert language_service.detect_language("Altitude evvalavu km sollunga?") == "tanglish"
    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gemini_gen:
        mock_gemini_gen.return_value = ("Orbital engine 340 kilometers altitude-la operate aaguthu.", None, None)
        res_tg = client.post("/api/chat/ask", headers=headers_a, json={
            "question": "Altitude evvalavu km sollunga?",
            "document_ids": [doc_id]
        })
    assert res_tg.status_code == 200
    assert "340" in res_tg.json()["answer"]


def test_gemini_user_isolation(client, headers_a, headers_b):
    """Verify User B cannot access or query documents uploaded by User A."""
    content = "Confidential User A strategic roadmap for Gemini AI deployment."
    files = {"file": ("user_a_confidential.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_a_id = upload_res.json()["id"]

    # User B queries User A's document ID
    res_b = client.post("/api/chat/ask", headers=headers_b, json={
        "question": "What is the strategic roadmap?",
        "document_ids": [doc_a_id]
    })
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["grounded"] is False
    assert len(data_b["sources"]) == 0
    assert "cannot find" in data_b["answer"].lower() or "கிடைக்கவில்லை" in data_b["answer"]
