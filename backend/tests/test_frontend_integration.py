"""Frontend integration and component testing suite."""

import pytest
from unittest.mock import MagicMock, patch

from frontend.config import BACKEND_API_URL, FILE_ICONS, STATUS_COLORS
from frontend.components.document_card import format_file_size
from frontend.api_client import APIClient


def test_frontend_config_constants():
    assert BACKEND_API_URL.startswith("http")
    assert "pdf" in FILE_ICONS
    assert "docx" in FILE_ICONS
    assert "txt" in FILE_ICONS
    assert "completed" in STATUS_COLORS
    assert "failed" in STATUS_COLORS


def test_format_file_size():
    assert format_file_size(500) == "500 B"
    assert "KB" in format_file_size(2048)
    assert "MB" in format_file_size(5 * 1024 * 1024)


def test_api_client_initialization_and_headers():
    client = APIClient(base_url="http://localhost:8000")
    headers = client._headers(token="test_token_xyz")
    assert headers["Authorization"] == "Bearer test_token_xyz"

    no_headers = client._headers(token=None)
    assert "Authorization" not in no_headers


@patch("requests.post")
def test_api_client_login_mock(mock_post):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "access_token": "mock_access",
        "refresh_token": "mock_refresh",
        "user_id": 1,
        "username": "alice"
    }
    mock_post.return_value = mock_res

    client = APIClient()
    result = client.login("alice", "password123")
    assert result["success"] is True
    assert result["data"]["access_token"] == "mock_access"


@patch("requests.post")
def test_api_client_ask_question_mock(mock_post):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "answer": "This is a grounded answer.",
        "conversation_id": "conv-1",
        "message_id": "msg-1",
        "sources": [{"filename": "doc.pdf", "page_number": 1, "excerpt": "Sample text", "score": 0.85}],
        "grounded": True
    }
    mock_post.return_value = mock_res

    client = APIClient()
    result = client.ask_question("What is X?", token="token_123")
    assert result["success"] is True
    assert "grounded answer" in result["data"]["answer"]
    assert len(result["data"]["sources"]) == 1


def test_frontend_module_imports():
    """Verify that all Streamlit components and pages can be imported without syntax or import errors."""
    import frontend.app
    import frontend.config
    import frontend.api_client
    import frontend.auth
    import frontend.components.sidebar
    import frontend.components.header
    import frontend.components.metrics_cards
    import frontend.components.document_card
    import frontend.components.chat_message
    import frontend.components.citation_viewer
    import frontend.components.upload_component
    import frontend.components.loading
    import frontend.components.dashboard_ui
    import frontend.components.doc_ui
    import frontend.components.chat_ui
    import frontend.components.history_ui
    import frontend.components.admin_ui
    import frontend.components.settings_ui

    assert frontend.app is not None
    assert frontend.config is not None
