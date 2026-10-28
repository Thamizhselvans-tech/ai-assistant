"""End-to-End integration tests for AI Knowledge Assistant."""

import io
import pytest


def test_health_check_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "services" in data


def test_full_rag_lifecycle_e2e(client, mock_openai):
    # Step 1: User Registration
    reg_res = client.post("/api/auth/register", json={
        "username": "david_e2e",
        "email": "david@example.com",
        "password": "Password123!"
    })
    assert reg_res.status_code == 201

    # Step 2: Login
    login_res = client.post("/api/auth/login", json={
        "username_or_email": "david@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Upload Document
    doc_text = (
        "Project Apollo was the third United States human spaceflight program carried out by NASA. "
        "It succeeded in landing the first humans on the Moon in 1969. "
        "Commander Neil Armstrong and lunar module pilot Buzz Aldrin formed the American crew."
    )
    upload_res = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("apollo_mission.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain")}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]
    assert upload_res.json()["status"] == "completed"

    # Step 4: Ask Question Grounded in Document
    chat_res = client.post(
        "/api/chat/ask",
        headers=headers,
        json={"question": "Who were the astronauts on the first Moon landing?"}
    )
    assert chat_res.status_code == 200
    ans_data = chat_res.json()
    assert "answer" in ans_data
    assert len(ans_data["sources"]) > 0
    assert ans_data["sources"][0]["filename"] == "apollo_mission.txt"
    conv_id = ans_data["conversation_id"]

    # Step 5: Ask question with no evidence in documents
    no_ev_res = client.post(
        "/api/chat/ask",
        headers=headers,
        json={
            "question": "What is the capital city of ancient Atlantis in year 4000 BC?",
            "conversation_id": conv_id
        }
    )
    assert no_ev_res.status_code == 200
    assert "cannot find the answer" in no_ev_res.json()["answer"].lower()

    # Step 6: Verify Conversation History
    hist_res = client.get(f"/api/chat/history/{conv_id}", headers=headers)
    assert hist_res.status_code == 200
    messages = hist_res.json()["messages"]
    assert len(messages) == 4  # 2 user queries + 2 assistant answers

    # Step 7: Delete Document and Vector Records
    del_doc_res = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert del_doc_res.status_code == 200

    # Step 8: Delete Conversation
    del_conv_res = client.delete(f"/api/chat/history/{conv_id}", headers=headers)
    assert del_conv_res.status_code == 200
