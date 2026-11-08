"""Comprehensive verification suite for production deployment readiness.

Validates:
1. FastAPI startup & lifespan events
2. Public /health & /api/health endpoints
3. User registration, login, and JWT validation
4. Document upload & extraction via multipart form
5. Vector store embedding generation & ChromaDB retrieval
6. Database persistence across session lifecycle
7. Production CORS origin filtering (wildcard, specific, and Streamlit Cloud regex)
8. Frontend dynamic URL resolution via environment & st.secrets
9. Render dynamic PORT assignment
10. Render Persistent Disk DATA_DIR directory creation & path anchoring
"""

import os
import io
import tempfile
import pytest
from starlette.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.core.config import Settings
from frontend.config import get_backend_url
from frontend.api_client import APIClient


@pytest.fixture(scope="module")
def prod_client():
    """Test client for FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(prod_client):
    """Register and login a clean test user to obtain Bearer headers."""
    username = "deploy_tester"
    email = "deploy_tester@example.com"
    password = "SecurePassword123!"

    # Register (ignore if already exists from earlier runs)
    prod_client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    # Login
    res = prod_client.post("/api/auth/login", json={
        "username_or_email": username,
        "password": password
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. FastAPI Startup & Root/Health Endpoints
# =============================================================================

def test_fastapi_root_endpoint(prod_client):
    """Verify root endpoint responds with API metadata and docs link."""
    res = prod_client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert data["health"] == "/health"
    assert "/docs" in data["docs"]


def test_public_health_endpoint(prod_client):
    """Verify /health endpoint works for Render health check."""
    res = prod_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data["services"]
    assert "vector_store" in data["services"]


def test_api_health_endpoint(prod_client):
    """Verify /api/health endpoint works identically."""
    res = prod_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "ram" in data["services"]
    assert "llm_provider" in data["services"]


# =============================================================================
# 2. Authentication & JWT Security
# =============================================================================

def test_jwt_auth_workflow(prod_client, auth_headers):
    """Verify JWT bearer token protects authenticated endpoints."""
    # /api/auth/me with valid token
    me_res = prod_client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "deploy_tester"

    # Reject request without token
    unauth_res = prod_client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # Reject request with malformed token
    bad_res = prod_client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert bad_res.status_code == 401


# =============================================================================
# 3. Document Upload & RAG Ingestion
# =============================================================================

def test_document_upload_and_indexing(prod_client, auth_headers):
    """Verify document upload, text extraction, and ChromaDB chunk indexing."""
    content = b"Quantum Distributed Key Agreement Protocol Alpha operates over 150km fiber lines."
    files = {"file": ("protocol_alpha.txt", io.BytesIO(content), "text/plain")}

    res = prod_client.post("/api/documents/upload", headers=auth_headers, files=files)
    assert res.status_code == 201
    doc_data = res.json()
    assert "id" in doc_data
    assert doc_data["chunk_count"] >= 1
    assert doc_data["status"] == "completed"

    doc_id = doc_data["id"]

    # Verify document listing
    list_res = prod_client.get("/api/documents", headers=auth_headers)
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)


# =============================================================================
# 4. RAG Chat & Retrieval
# =============================================================================

def test_chat_retrieval_with_citations(prod_client, auth_headers):
    """Verify RAG question answering retrieves stored chunks with citations."""
    q_payload = {
        "question": "What is the operational distance of Quantum Protocol Alpha?",
        "top_k": 3
    }
    res = prod_client.post("/api/chat/ask", headers=auth_headers, json=q_payload)
    assert res.status_code == 200
    ans_data = res.json()
    assert "answer" in ans_data
    assert "conversation_id" in ans_data
    assert len(ans_data["citations"]) >= 1
    assert "150km" in ans_data["citations"][0]["excerpt"] or "Alpha" in ans_data["citations"][0]["excerpt"]


# =============================================================================
# 5. SQLite & ChromaDB Storage Persistence
# =============================================================================

def test_database_persistence_across_sessions():
    """Verify SQLite database persistence across independent connection lifecycles."""
    from backend.app.database.session import SessionLocal
    from backend.app.models.user import User

    # Query in fresh session
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "deploy_tester").first()
        assert user is not None
        assert user.email == "deploy_tester@example.com"


def test_chroma_vector_store_persistence():
    """Verify ChromaDB collection persists records across client instantiations."""
    import backend.app.rag.vector_store as vs_module
    from backend.app.rag.vector_store import VectorStore

    current_count = vs_module.vector_store.count()
    assert current_count > 0

    # Instantiate brand new VectorStore referencing same persist directory and collection
    fresh_vs = VectorStore(
        persist_dir=vs_module.vector_store.persist_dir,
        collection_name=vs_module.vector_store.collection_name
    )
    assert fresh_vs.count() == current_count


# =============================================================================
# 6. Production CORS Verification
# =============================================================================

def test_cors_streamlit_community_cloud_origin(prod_client):
    """Verify Streamlit Community Cloud origins (*.streamlit.app) receive matching CORS headers."""
    origin = "https://ai-knowledge-assistant-production.streamlit.app"
    res = prod_client.get("/health", headers={"Origin": origin})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == origin
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_cors_localhost_origin(prod_client):
    """Verify local development frontend origin receives matching CORS headers."""
    origin = "http://localhost:8501"
    res = prod_client.get("/health", headers={"Origin": origin})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == origin


# =============================================================================
# 7. Frontend Dynamic Backend URL Resolution
# =============================================================================

def test_frontend_get_backend_url_with_streamlit_secrets():
    """Verify frontend resolves BACKEND_API_URL from st.secrets."""
    mock_secrets = {"BACKEND_API_URL": "https://custom-render-app.onrender.com"}
    with patch("frontend.config.st") as mock_st:
        mock_st.secrets = mock_secrets
        resolved = get_backend_url()
        assert resolved == "https://custom-render-app.onrender.com"


def test_frontend_get_backend_url_with_env_var():
    """Verify frontend resolves BACKEND_API_URL from environment variable."""
    with patch.dict(os.environ, {"BACKEND_API_URL": "https://env-backend.onrender.com"}):
        with patch("frontend.config.st") as mock_st:
            mock_st.secrets = {}
            resolved = get_backend_url()
            assert resolved == "https://env-backend.onrender.com"


def test_frontend_api_client_dynamic_url():
    """Verify APIClient dynamically picks up updated backend URL."""
    client = APIClient()
    with patch.dict(os.environ, {"BACKEND_API_URL": "https://dynamic-render.onrender.com"}):
        with patch("frontend.config.st") as mock_st:
            mock_st.secrets = {}
            assert client.base_url == "https://dynamic-render.onrender.com"


# =============================================================================
# 8. Render Dynamic PORT & Persistent DATA_DIR Configuration
# =============================================================================

def test_render_port_environment_override():
    """Verify Render's PORT environment variable overrides API_PORT."""
    with patch.dict(os.environ, {"PORT": "10000"}):
        s = Settings()
        assert s.API_PORT == 10000


def test_render_persistent_disk_data_dir_anchor():
    """Verify DATA_DIR anchors database, ChromaDB, and uploads directory paths."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.dict(os.environ, {"DATA_DIR": tmp_dir}, clear=False):
            # Clear explicit path overrides if any
            env_clean = {k: v for k, v in os.environ.items() if k not in ["DATABASE_URL", "CHROMA_PERSIST_DIRECTORY", "UPLOAD_DIR"]}
            env_clean["DATA_DIR"] = tmp_dir
            with patch.dict(os.environ, env_clean, clear=True):
                s = Settings()
                assert s.DATA_DIR == tmp_dir
                assert tmp_dir in s.DATABASE_URL
                assert tmp_dir in s.CHROMA_PERSIST_DIRECTORY
                assert tmp_dir in s.UPLOAD_DIR
                s.ensure_directories()
                assert os.path.exists(s.UPLOAD_DIR)
                assert os.path.exists(s.CHROMA_PERSIST_DIRECTORY)
