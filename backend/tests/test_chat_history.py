"""Tests for chat history persistence, conversation management, and cross-user isolation."""

import io
import pytest


def test_ask_creates_conversation_and_messages(client, headers_a, mock_openai):
    # Upload document first
    content = b"The primary backend server is written in Python using FastAPI."
    client.post("/api/documents/upload", headers=headers_a, files={"file": ("tech.txt", io.BytesIO(content), "text/plain")})

    # Ask question
    res = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "What language and framework is the backend written in?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "conversation_id" in data
    conv_id = data["conversation_id"]

    # Retrieve conversation history
    hist_res = client.get(f"/api/chat/history/{conv_id}", headers=headers_a)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["messages"]) == 2
    assert hist_data["messages"][0]["role"] == "user"
    assert hist_data["messages"][1]["role"] == "assistant"
    assert len(hist_data["messages"][1]["sources"]) > 0


def test_cross_user_conversation_isolation(client, headers_a, headers_b, mock_openai):
    # User A asks question
    res_a = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "Confidential question from Alice."
    })
    conv_id = res_a.json()["conversation_id"]

    # User B attempts to access Alice's conversation -> 404
    hist_b = client.get(f"/api/chat/history/{conv_id}", headers=headers_b)
    assert hist_b.status_code == 404

    # User B attempts to delete Alice's conversation -> 404
    del_b = client.delete(f"/api/chat/history/{conv_id}", headers=headers_b)
    assert del_b.status_code == 404

    # User B conversation list should be empty
    list_b = client.get("/api/chat/history", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0


def test_delete_conversation(client, headers_a, mock_openai):
    res = client.post("/api/chat/ask", headers=headers_a, json={
        "question": "Test question to be deleted."
    })
    conv_id = res.json()["conversation_id"]

    del_res = client.delete(f"/api/chat/history/{conv_id}", headers=headers_a)
    assert del_res.status_code == 200

    # Verify not found after deletion
    hist_res = client.get(f"/api/chat/history/{conv_id}", headers=headers_a)
    assert hist_res.status_code == 404
