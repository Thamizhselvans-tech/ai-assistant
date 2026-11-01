"""Phase 3 API Integration Test Suite: Auth, Documents, Chat, Admin, and End-to-End Workflows."""

import io
import os
import tempfile
import pytest
import docx

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from backend.app.core.security import create_access_token, create_refresh_token
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.schemas.auth import UserRegisterRequest
from backend.app.services.auth_service import auth_service
from backend.app.rag.prompts import INSUFFICIENT_EVIDENCE_ANSWER


# =====================================================================
# Fixtures for Admin and Additional Test Users
# =====================================================================

@pytest.fixture
def admin_user(db_session):
    """Create an administrator user."""
    req = UserRegisterRequest(
        username="admin_super",
        email="admin@example.com",
        password="AdminPassword123!"
    )
    user = auth_service.register_user(db_session, req, is_admin=True, role="admin")
    return user


@pytest.fixture
def admin_token(client, admin_user):
    res = client.post("/api/auth/login", json={
        "username_or_email": admin_user.username,
        "password": "AdminPassword123!"
    })
    return res.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# =====================================================================
# 1. AUTHENTICATION & REFRESH TOKEN TESTS
# =====================================================================

def test_auth_refresh_token_flow(client, user_a):
    # 1. Login to get access and refresh tokens
    login_res = client.post("/api/auth/login", json={
        "username_or_email": user_a.username,
        "password": "password123"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    refresh_token = tokens["refresh_token"]

    # 2. Call /api/auth/refresh
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refreshed = refresh_res.json()
    assert "access_token" in refreshed
    assert "refresh_token" in refreshed
    assert refreshed["user_id"] == user_a.id

    # 3. Verify new access token works against /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {refreshed['access_token']}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == user_a.email

    # 4. Attempt to use refresh token directly as a Bearer access token -> must fail 401
    bad_bearer = client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert bad_bearer.status_code == 401

    # 5. Invalid refresh token -> 401
    invalid_refresh = client.post("/api/auth/refresh", json={"refresh_token": "not_a_valid_jwt"})
    assert invalid_refresh.status_code == 401


# =====================================================================
# 2. DOCUMENT MANAGEMENT TESTS (PDF, DOCX, TXT)
# =====================================================================

def test_document_pdf_docx_txt_upload_and_lifecycle(client, headers_a):
    # --- 1. PDF Upload ---
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
    try:
        pdf_doc = fitz.open()
        p1 = pdf_doc.new_page()
        p1.insert_text((72, 72), "Deep Learning Architectures: Transformers and Attention Mechanisms.")
        pdf_doc.save(pdf_path)
        pdf_doc.close()

        with open(pdf_path, "rb") as pf:
            res_pdf = client.post(
                "/api/documents/upload",
                headers=headers_a,
                files={"file": ("deep_learning.pdf", pf, "application/pdf")}
            )
        assert res_pdf.status_code == 201
        pdf_data = res_pdf.json()
        assert pdf_data["file_type"] == "pdf"
        assert pdf_data["page_count"] == 1
        assert pdf_data["chunk_count"] >= 1
        pdf_id = pdf_data["id"]
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

    # --- 2. DOCX Upload ---
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        docx_path = f.name
    try:
        doc_obj = docx.Document()
        doc_obj.add_paragraph("Enterprise RAG deployment on Kubernetes clusters.")
        doc_obj.save(docx_path)

        with open(docx_path, "rb") as df:
            res_docx = client.post(
                "/api/documents/upload",
                headers=headers_a,
                files={"file": ("k8s_deploy.docx", df, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        assert res_docx.status_code == 201
        docx_data = res_docx.json()
        assert docx_data["file_type"] == "docx"
        assert docx_data["chunk_count"] >= 1
        docx_id = docx_data["id"]
    finally:
        if os.path.exists(docx_path):
            os.unlink(docx_path)

    # --- 3. Document Listing ---
    list_res = client.get("/api/documents", headers=headers_a)
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    doc_ids = [d["id"] for d in docs]
    assert pdf_id in doc_ids
    assert docx_id in doc_ids

    # --- 4. Document Detail ---
    detail_res = client.get(f"/api/documents/{pdf_id}", headers=headers_a)
    assert detail_res.status_code == 200
    assert detail_res.json()["filename"] == "deep_learning.pdf"

    # --- 5. Clean up via Delete ---
    del_res = client.delete(f"/api/documents/{pdf_id}", headers=headers_a)
    assert del_res.status_code == 200
    del_res2 = client.delete(f"/api/documents/{docx_id}", headers=headers_a)
    assert del_res2.status_code == 200


# =====================================================================
# 3. CHAT API, PAGINATION, AND GROUNDING TESTS
# =====================================================================

def test_chat_ask_and_pagination(client, headers_a, mock_openai):
    # Upload context document
    txt_content = b"The Mars rover Perseverance landed in Jezero Crater in February 2021."
    files = {"file": ("mars_perseverance.txt", io.BytesIO(txt_content), "text/plain")}
    client.post("/api/documents/upload", headers=headers_a, files=files)

    # 1. Ask grounded question
    ask_res = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "Where did the Perseverance rover land?"
    })
    assert ask_res.status_code == 200
    data = ask_res.json()
    assert "answer" in data
    assert "conversation_id" in data
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["filename"] == "mars_perseverance.txt"
    # Also verify citations alias is populated
    assert "citations" in data
    assert len(data["citations"]) == len(data["sources"])
    conv_id = data["conversation_id"]

    # 2. Ask follow-up question in the same conversation
    ask_res_2 = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "When did it land?",
        "conversation_id": conv_id
    })
    assert ask_res_2.status_code == 200
    assert ask_res_2.json()["conversation_id"] == conv_id

    # 3. Retrieve conversation history
    hist_res = client.get(f"/api/chat/history/{conv_id}", headers=headers_a)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist["messages"]) == 4  # 2 user questions + 2 assistant answers

    # 4. Conversation listing with pagination
    paged_res = client.get("/api/chat/history?skip=0&limit=1", headers=headers_a)
    assert paged_res.status_code == 200
    paged_data = paged_res.json()
    assert len(paged_data["conversations"]) == 1
    assert paged_data["total"] >= 1


def test_chat_ask_no_supporting_context_no_llm_call(client, headers_a):
    # Ask about a topic completely absent from indexed documents
    res = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "What is the secret recipe for authentic Neapolitan pizza dough?"
    })
    assert res.status_code == 200
    data = res.json()
    assert INSUFFICIENT_EVIDENCE_ANSWER in data["answer"]
    assert len(data["sources"]) == 0
    assert data["grounded"] is False


def test_cross_user_conversation_isolation(client, headers_a, headers_b):
    # User A creates a conversation
    ask_res = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "Hello from Alice!"
    })
    conv_id = ask_res.json()["conversation_id"]

    # User B attempts to access Alice's conversation -> 404
    res_b = client.get(f"/api/chat/history/{conv_id}", headers=headers_b)
    assert res_b.status_code == 404

    # User B attempts to delete Alice's conversation -> 404
    del_b = client.delete(f"/api/chat/history/{conv_id}", headers=headers_b)
    assert del_b.status_code == 404

    # User B attempts to append message to Alice's conversation -> 404
    append_b = client.post("/api/chat/ask", headers=headers_b, json={
        "question": "Sneaky message",
        "conversation_id": conv_id
    })
    assert append_b.status_code == 404


# =====================================================================
# 4. ADMIN APIS AND ACCESS CONTROL TESTS
# =====================================================================

def test_admin_access_control(client, headers_a, admin_headers):
    # Non-admin User A attempts to access admin endpoints -> 403 Forbidden
    assert client.get("/api/admin/dashboard", headers=headers_a).status_code == 403
    assert client.get("/api/admin/users", headers=headers_a).status_code == 403
    assert client.get("/api/admin/documents", headers=headers_a).status_code == 403
    assert client.get("/api/admin/system-health", headers=headers_a).status_code == 403

    # Unauthenticated user -> 401 Unauthorized
    assert client.get("/api/admin/dashboard").status_code == 401

    # Admin user -> 200 OK
    dash_res = client.get("/api/admin/dashboard", headers=admin_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "total_users" in dash_data
    assert "total_documents" in dash_data
    assert "document_status_breakdown" in dash_data
    assert dash_data["system_status"] == "healthy"


def test_admin_users_and_documents_lists(client, admin_headers, user_a):
    # 1. Admin users list
    users_res = client.get("/api/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    users_data = users_res.json()
    assert users_data["total"] >= 1
    # Verify no password hashes are exposed
    for u in users_data["users"]:
        assert "hashed_password" not in u
        assert "password" not in u
        assert "email" in u

    # 2. Admin documents list
    docs_res = client.get("/api/admin/documents", headers=admin_headers)
    assert docs_res.status_code == 200
    assert "documents" in docs_res.json()


def test_admin_system_health(client, admin_headers):
    health_res = client.get("/api/admin/system-health", headers=admin_headers)
    assert health_res.status_code == 200
    h_data = health_res.json()
    assert h_data["overall_status"] in ("healthy", "degraded")
    assert h_data["database"]["status"] == "connected"
    assert h_data["vector_store"]["status"] == "healthy"
    assert h_data["embedding_engine"]["dimension"] == 384
    # Security: Verify raw OpenAI API key is NOT exposed
    assert "OPENAI_API_KEY" not in h_data["llm_service"]
    assert "api_key" not in h_data["llm_service"]
    assert "api_key_configured" in h_data["llm_service"]


# =====================================================================
# 5. FULL END-TO-END WORKFLOW INTEGRATION TEST
# =====================================================================

def test_full_rag_integration_lifecycle(client, mock_openai):
    # Step 1: Register new user
    reg_res = client.post("/api/auth/register", json={
        "username": "integrator",
        "email": "integrator@example.com",
        "password": "IntegrationPassword123!"
    })
    assert reg_res.status_code == 201

    # Step 2: Login to obtain JWT and refresh token
    login_res = client.post("/api/auth/login", json={
        "username_or_email": "integrator",
        "password": "IntegrationPassword123!"
    })
    assert login_res.status_code == 200
    jwt_token = login_res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {jwt_token}"}

    # Step 3: Upload a PDF document
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
    try:
        pdf_doc = fitz.open()
        p = pdf_doc.new_page()
        p.insert_text((50, 50), "Antigravity RAG Platform: Engineered for high-throughput enterprise knowledge search.")
        pdf_doc.save(pdf_path)
        pdf_doc.close()

        with open(pdf_path, "rb") as pf:
            upload_res = client.post(
                "/api/documents/upload",
                headers=user_headers,
                files={"file": ("antigravity_platform.pdf", pf, "application/pdf")}
            )
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["id"]
        assert upload_res.json()["status"] == "completed"

        # Step 4: Ask question
        ask_res = client.post("/api/chat/ask", headers=user_headers, json={
            "question": "What is the Antigravity platform engineered for?"
        })
        assert ask_res.status_code == 200
        answer_data = ask_res.json()
        assert answer_data["grounded"] is True
        assert len(answer_data["sources"]) >= 1
        conv_id = answer_data["conversation_id"]

        # Step 5: Verify history
        hist_res = client.get(f"/api/chat/history/{conv_id}", headers=user_headers)
        assert hist_res.status_code == 200
        assert len(hist_res.json()["messages"]) == 2

        # Step 6: Delete document
        del_res = client.delete(f"/api/documents/{doc_id}", headers=user_headers)
        assert del_res.status_code == 200

        # Verify document is gone
        assert client.get(f"/api/documents/{doc_id}", headers=user_headers).status_code == 404

    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
