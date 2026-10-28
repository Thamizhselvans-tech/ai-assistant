"""Tests for document upload, listing, retrieval, deletion, and cross-user isolation."""

import io
import pytest


def test_upload_txt_document(client, headers_a):
    file_content = b"Artificial Intelligence and Machine Learning are transforming modern data processing."
    files = {"file": ("ai_overview.txt", io.BytesIO(file_content), "text/plain")}

    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "ai_overview.txt"
    assert data["file_type"] == "txt"
    assert data["status"] == "completed"
    assert data["chunk_count"] >= 1


def test_upload_empty_document(client, headers_a):
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_upload_unsupported_extension(client, headers_a):
    files = {"file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")}
    res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower()


def test_list_and_get_document(client, headers_a):
    # Upload doc
    files = {"file": ("spec.txt", io.BytesIO(b"System specifications for testing."), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    doc_id = upload_res.json()["id"]

    # List
    list_res = client.get("/api/documents", headers=headers_a)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # Get single
    get_res = client.get(f"/api/documents/{doc_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id


def test_cross_user_document_isolation(client, headers_a, headers_b):
    # User A uploads a document
    files = {"file": ("alice_private.txt", io.BytesIO(b"Classified data for Alice only."), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    alice_doc_id = upload_res.json()["id"]

    # User B attempts to access Alice's document -> 404
    get_res = client.get(f"/api/documents/{alice_doc_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B attempts to delete Alice's document -> 404
    del_res = client.delete(f"/api/documents/{alice_doc_id}", headers=headers_b)
    assert del_res.status_code == 404

    # Document should still exist when queried by Alice
    verify_res = client.get(f"/api/documents/{alice_doc_id}", headers=headers_a)
    assert verify_res.status_code == 200


def test_delete_document(client, headers_a):
    files = {"file": ("to_delete.txt", io.BytesIO(b"Temporary file to delete."), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    doc_id = upload_res.json()["id"]

    del_res = client.delete(f"/api/documents/{doc_id}", headers=headers_a)
    assert del_res.status_code == 200
    assert del_res.json()["id"] == doc_id

    # Verify not found after deletion
    get_res = client.get(f"/api/documents/{doc_id}", headers=headers_a)
    assert get_res.status_code == 404
