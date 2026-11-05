"""Comprehensive test suite for composer attachment (+) document upload feature and RAG retrieval."""

import io
import os
import tempfile
import fitz
import docx
import pytest
from frontend.components.chat_ui import extract_chat_input
from frontend.config import MAX_UPLOAD_SIZE_MB


def test_extract_chat_input_helper():
    """Verify extract_chat_input properly handles text, files, dicts, and objects."""
    # String only
    text, files = extract_chat_input("Test prompt")
    assert text == "Test prompt"
    assert files == []

    # Dict representation
    text, files = extract_chat_input({"text": "Hello RAG", "files": ["f1.pdf"]})
    assert text == "Hello RAG"
    assert files == ["f1.pdf"]

    # None / Empty
    text, files = extract_chat_input(None)
    assert text == ""
    assert files == []


def test_composer_upload_txt(client, headers_a):
    """1. Upload TXT document."""
    content = b"The AI Knowledge Assistant features an inline document attachment button inside the ChatGPT capsule composer."
    files = {"file": ("composer_guide.txt", io.BytesIO(content), "text/plain")}

    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "composer_guide.txt"
    assert data["file_type"] == "txt"
    assert data["status"] == "completed"
    assert data["chunk_count"] >= 1


def test_composer_upload_pdf(client, headers_a):
    """2. Upload PDF document."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name
    try:
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((72, 72), "Composer PDF Document: Key features include inline upload and vector indexing.")
        doc.save(pdf_path)
        doc.close()

        with open(pdf_path, "rb") as f:
            res = client.post(
                "/api/documents/upload",
                headers=headers_a,
                files={"file": ("composer_features.pdf", f, "application/pdf")}
            )
        assert res.status_code == 201
        data = res.json()
        assert data["filename"] == "composer_features.pdf"
        assert data["file_type"] == "pdf"
        assert data["page_count"] == 1
        assert data["chunk_count"] >= 1
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_composer_upload_docx(client, headers_a):
    """3. Upload DOCX document."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        docx_path = tmp.name
    try:
        doc = docx.Document()
        doc.add_heading("Composer DOCX Architecture", level=1)
        doc.add_paragraph("This document details the left-side attachment icon for Streamlit chat composer.")
        doc.save(docx_path)

        with open(docx_path, "rb") as f:
            res = client.post(
                "/api/documents/upload",
                headers=headers_a,
                files={"file": ("composer_arch.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        assert res.status_code == 201
        data = res.json()
        assert data["filename"] == "composer_arch.docx"
        assert data["file_type"] == "docx"
        assert data["chunk_count"] >= 1
    finally:
        if os.path.exists(docx_path):
            os.unlink(docx_path)


def test_composer_upload_invalid_extension(client, headers_a):
    """4. Invalid file rejection."""
    files = {"file": ("malicious_script.exe", io.BytesIO(b"MZBINARY"), "application/octet-stream")}
    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower()


def test_composer_upload_oversized_file(client, headers_a):
    """5. Oversized file rejection."""
    oversized_bytes = b"X" * ((MAX_UPLOAD_SIZE_MB + 1) * 1024 * 1024)
    files = {"file": ("huge_file.txt", io.BytesIO(oversized_bytes), "text/plain")}
    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 400
    assert "exceeds" in res.json()["detail"].lower()


def test_composer_upload_unauthenticated(client):
    """6. Upload API authentication requirement."""
    files = {"file": ("unauth.txt", io.BytesIO(b"Test content"), "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 401


def test_composer_upload_success_and_error_states(client, headers_a):
    """7. Upload success and empty error state validation."""
    # Empty file
    empty_res = client.post(
        "/api/documents/upload",
        headers=headers_a,
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    )
    assert empty_res.status_code == 400
    assert "empty" in empty_res.json()["detail"].lower()

    # Valid file success
    valid_res = client.post(
        "/api/documents/upload",
        headers=headers_a,
        files={"file": ("valid.txt", io.BytesIO(b"Grounded retrieval verified."), "text/plain")}
    )
    assert valid_res.status_code == 201
    assert valid_res.json()["status"] == "completed"


def test_composer_send_question_and_retrieve_from_uploaded_doc(client, headers_a, mock_openai):
    """8 & 9. Send question after uploading and verify AI retrieves information from uploaded document."""
    # Step 1: Upload specialized factual document
    doc_content = b"The Falcon-99 engine operates at an optimal core temperature of exactly 342.5 Kelvin with cryogenic helium shielding."
    files = {"file": ("falcon99_specs.txt", io.BytesIO(doc_content), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Step 2: Query the RAG pipeline about the document
    chat_payload = {
        "question": "What is the optimal core temperature of the Falcon-99 engine?",
        "document_ids": [doc_id],
        "top_k": 3,
        "similarity_threshold": 0.15
    }
    chat_res = client.post("/api/chat/ask", headers=headers_a, json=chat_payload)
    assert chat_res.status_code == 200
    data = chat_res.json()

    # Verify response structure and citations
    assert "answer" in data
    assert data["grounded"] is True
    assert len(data["sources"]) >= 1

    top_source = data["sources"][0]
    assert top_source["filename"] == "falcon99_specs.txt"
    assert "342.5" in top_source["excerpt"]
