"""Pytest configuration and test fixtures."""

import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure environment uses test configurations
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-long-min"

from backend.app.core.config import settings
from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.rag.vector_store import VectorStore
import backend.app.rag.vector_store as vs_module
import backend.app.rag.pipeline as rag_module
from backend.app.services.auth_service import auth_service
from backend.app.schemas.auth import UserRegisterRequest


# Use in-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Create and clean up temporary test directories."""
    test_dir = tempfile.mkdtemp(prefix="ai_assistant_test_")
    test_chroma = os.path.join(test_dir, "chroma")
    test_uploads = os.path.join(test_dir, "uploads")
    os.makedirs(test_chroma, exist_ok=True)
    os.makedirs(test_uploads, exist_ok=True)

    settings.CHROMA_PERSIST_DIRECTORY = test_chroma
    settings.UPLOAD_DIR = test_uploads
    settings.OPENAI_API_KEY = "test-mock-key"

    # Initialize isolated VectorStore
    test_vs = VectorStore(persist_dir=test_chroma, collection_name="test_collection")
    vs_module.vector_store = test_vs
    rag_module.vector_store = test_vs

    yield test_dir

    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def db_session():
    """Provide a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_a(db_session):
    """Fixture creating user A."""
    req = UserRegisterRequest(
        username="user_alice",
        email="alice@example.com",
        password="password123"
    )
    return auth_service.register_user(db_session, req)


@pytest.fixture
def user_b(db_session):
    """Fixture creating user B."""
    req = UserRegisterRequest(
        username="user_bob",
        email="bob@example.com",
        password="password123"
    )
    return auth_service.register_user(db_session, req)


@pytest.fixture
def token_a(client, user_a):
    """Auth token for user A."""
    res = client.post("/api/auth/login", json={
        "username_or_email": user_a.username,
        "password": "password123"
    })
    return res.json()["access_token"]


@pytest.fixture
def token_b(client, user_b):
    """Auth token for user B."""
    res = client.post("/api/auth/login", json={
        "username_or_email": user_b.username,
        "password": "password123"
    })
    return res.json()["access_token"]


@pytest.fixture
def headers_a(token_a):
    return {"Authorization": f"Bearer {token_a}"}


@pytest.fixture
def headers_b(token_b):
    return {"Authorization": f"Bearer {token_b}"}


@pytest.fixture
def mock_openai():
    """Mock OpenAI chat completions for deterministic RAG tests."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Based on the provided documents, the primary architecture uses FastAPI and Streamlit."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    original_client = rag_module.rag_pipeline._custom_client
    rag_module.rag_pipeline._custom_client = mock_client
    yield mock_client
    rag_module.rag_pipeline._custom_client = original_client
