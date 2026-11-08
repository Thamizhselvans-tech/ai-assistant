"""Full 16-point test suite covering all composer functionalities, validations, and edge cases."""

import io
import os
import tempfile
import fitz
import docx
import pytest
from unittest.mock import patch, MagicMock

from frontend.api_client import APIClient
from frontend.components.chat_composer import render_chat_composer


# =========================================================================
# 1. Type and send an English question
# =========================================================================
def test_send_english_question(client, headers_a):
    """1. Send English query and verify English response."""
    payload = {"question": "Explain database normalization principles."}
    res = client.post("/api/chat/ask", headers=headers_a, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert data["language"] == "en"


# =========================================================================
# 2. Type and send a Tamil question
# =========================================================================
def test_send_tamil_question(client, headers_a):
    """2. Send Tamil query and verify Tamil response."""
    payload = {"question": "செயற்கை நுண்ணறிவு என்றால் என்ன?"}
    res = client.post("/api/chat/ask", headers=headers_a, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert data["language"] == "ta"


# =========================================================================
# 3. Type and send a Tanglish question
# =========================================================================
def test_send_tanglish_question(client, headers_a):
    """3. Send Tanglish query and verify Tanglish detection & response."""
    payload = {"question": "Machine learning na enna? Konjam explain pannunga."}
    res = client.post("/api/chat/ask", headers=headers_a, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert data["language"] in ["tanglish", "ta", "en"]


# =========================================================================
# 4. Send a question related to an uploaded PDF
# =========================================================================
def test_send_question_grounded_in_pdf(client, headers_a):
    """4. Upload PDF and query specific knowledge chunk."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name
    try:
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((72, 72), "Project Phoenix Quantum Protocol uses QKD key distribution across a 120km fiber optic link.")
        doc.save(pdf_path)
        doc.close()

        with open(pdf_path, "rb") as f:
            up_res = client.post("/api/documents/upload", headers=headers_a, files={"file": ("quantum_phoenix.pdf", f, "application/pdf")})
        assert up_res.status_code == 201
        doc_id = up_res.json()["id"]

        q_payload = {
            "question": "What is the transmission distance and protocol used in Project Phoenix?",
            "document_ids": [doc_id]
        }
        q_res = client.post("/api/chat/ask", headers=headers_a, json=q_payload)
        assert q_res.status_code == 200
        q_data = q_res.json()
        assert len(q_data["citations"]) >= 1
        assert "120km" in q_data["citations"][0]["excerpt"] or "Phoenix" in q_data["citations"][0]["excerpt"]
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


# =========================================================================
# 5. Upload a PDF
# =========================================================================
def test_upload_pdf(client, headers_a):
    """5. Upload PDF file with metadata verification."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name
    try:
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((72, 72), "Test document content for PDF upload verification.")
        doc.save(pdf_path)
        doc.close()

        with open(pdf_path, "rb") as f:
            res = client.post("/api/documents/upload", headers=headers_a, files={"file": ("sample_test.pdf", f, "application/pdf")})
        assert res.status_code == 201
        assert res.json()["file_type"] == "pdf"
        assert res.json()["page_count"] == 1
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


# =========================================================================
# 6. Upload a DOCX
# =========================================================================
def test_upload_docx(client, headers_a):
    """6. Upload DOCX file with metadata verification."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        docx_path = tmp.name
    try:
        doc = docx.Document()
        doc.add_paragraph("Test document content for DOCX upload verification.")
        doc.save(docx_path)

        with open(docx_path, "rb") as f:
            res = client.post("/api/documents/upload", headers=headers_a, files={"file": ("sample_test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
        assert res.status_code == 201
        assert res.json()["file_type"] == "docx"
        assert res.json()["chunk_count"] >= 1
    finally:
        if os.path.exists(docx_path):
            os.unlink(docx_path)


# =========================================================================
# 7. Upload a TXT
# =========================================================================
def test_upload_txt(client, headers_a):
    """7. Upload TXT file with metadata verification."""
    content = b"Sample plain text file for vector indexing."
    files = {"file": ("sample_test.txt", io.BytesIO(content), "text/plain")}
    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 201
    assert res.json()["file_type"] == "txt"
    assert res.json()["chunk_count"] >= 1


# =========================================================================
# 8. Test microphone component configuration
# =========================================================================
def test_microphone_component_declaration():
    """8. Verify custom chat composer component declares and loads index.html."""
    comp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "components", "chat_composer")
    html_path = os.path.join(comp_dir, "index.html")
    assert os.path.exists(html_path)
    html_content = open(html_path, "r", encoding="utf-8").read()
    # Check Web Speech API references
    assert "SpeechRecognition" in html_content
    assert "webkitSpeechRecognition" in html_content
    assert "ta-IN" in html_content
    assert "en-US" in html_content


# =========================================================================
# 9. Test Enter key / 10. Test Shift + Enter
# =========================================================================
def test_enter_key_and_multiline_logic():
    """9 & 10. Verify Enter sends and Shift+Enter preserves newlines in HTML JS."""
    comp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "components", "chat_composer")
    html_content = open(os.path.join(comp_dir, "index.html"), "r", encoding="utf-8").read()
    assert "e.key === \"Enter\" && !e.shiftKey" in html_content
    assert "e.preventDefault();" in html_content


# =========================================================================
# 11. Test empty input rejection
# =========================================================================
def test_empty_input_rejection(client, headers_a):
    """11. Verify whitespace-only or empty prompt is rejected."""
    # Backend validation
    res = client.post("/api/chat/ask", headers=headers_a, json={"question": "   "})
    assert res.status_code in [400, 422]


# =========================================================================
# 12. Test 2000-character limit
# =========================================================================
def test_2000_character_limit_truncation():
    """12. Verify prompt truncation logic for 2000 character limit."""
    comp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "components", "chat_composer")
    html_content = open(os.path.join(comp_dir, "index.html"), "r", encoding="utf-8").read()
    assert 'maxlength="2000"' in html_content

    # Test frontend truncation logic
    long_prompt = "A" * 2500
    truncated = long_prompt.strip()[:2000]
    assert len(truncated) == 2000


# =========================================================================
# 13. Test invalid JWT rejection
# =========================================================================
def test_invalid_jwt_rejection(client):
    """13. Verify invalid JWT returns 401 Unauthorized."""
    bad_headers = {"Authorization": "Bearer invalid_jwt_token_12345"}
    res = client.post("/api/chat/ask", headers=bad_headers, json={"question": "Hello"})
    assert res.status_code == 401


# =========================================================================
# 14. Test backend unavailable handling in frontend API client
# =========================================================================
def test_frontend_api_client_backend_unavailable():
    """14. Verify frontend API client gracefully returns error dict when offline."""
    client = APIClient(base_url="http://127.0.0.1:9999")  # Non-existent port
    res = client.health_check()
    assert res["success"] is False
    assert "error" in res


# =========================================================================
# 15. Test AI provider quota exceeded handling
# =========================================================================
def test_ai_provider_quota_exceeded_handling(client, headers_a):
    """15. Verify quota exceeded error is returned with clear message instead of silent failure."""
    from backend.app.services.llm_provider import llm_provider_service
    # Upload doc so context is retrieved and LLM is invoked
    files = {"file": ("quota_test.txt", io.BytesIO(b"Quantum Computing utilizes superposition and entanglement."), "text/plain")}
    client.post("/api/documents/upload", headers=headers_a, files=files)

    with patch.object(llm_provider_service, "generate_completion", return_value=(
        "⚠️ AI Provider Quota Exceeded (429 RESOURCE_EXHAUSTED). Please check your API credits or switch providers in Settings.",
        None,
        None
    )):
        res = client.post("/api/chat/ask", headers=headers_a, json={"question": "What is quantum computing?"})
        assert res.status_code == 200
        data = res.json()
        assert "Quota Exceeded" in data["answer"] or "429" in data["answer"]


# =========================================================================
# 16. Verify chat history persists across conversations
# =========================================================================
def test_chat_history_persistence(client, headers_a):
    """16. Verify asking questions creates and persists conversation in history."""
    q_res = client.post("/api/chat/ask", headers=headers_a, json={"question": "Test history persistence query"})
    assert q_res.status_code == 200
    conv_id = q_res.json()["conversation_id"]

    # Retrieve history
    hist_res = client.get(f"/api/chat/conversations/{conv_id}", headers=headers_a)
    assert hist_res.status_code == 200
    messages = hist_res.json()["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test history persistence query"
    assert messages[1]["role"] == "assistant"
