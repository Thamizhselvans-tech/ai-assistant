"""Tests for user authentication, registration, JWT handling, and route protection."""

import pytest


def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "securepassword123"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "charlie"
    assert data["email"] == "charlie@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client, user_a):
    res = client.post("/api/auth/register", json={
        "username": "another_alice",
        "email": user_a.email,
        "password": "securepassword123"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_register_duplicate_username(client, user_a):
    res = client.post("/api/auth/register", json={
        "username": user_a.username,
        "email": "new_alice@example.com",
        "password": "securepassword123"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_login_success_with_username(client, user_a):
    res = client.post("/api/auth/login", json={
        "username_or_email": user_a.username,
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == user_a.username


def test_login_success_with_email(client, user_a):
    res = client.post("/api/auth/login", json={
        "username_or_email": user_a.email,
        "password": "password123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_invalid_password(client, user_a):
    res = client.post("/api/auth/login", json={
        "username_or_email": user_a.username,
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    assert "Incorrect" in res.json()["detail"]


def test_login_nonexistent_user(client):
    res = client.post("/api/auth/login", json={
        "username_or_email": "nonexistent_person",
        "password": "password123"
    })
    assert res.status_code == 401


def test_protected_route_with_valid_token(client, headers_a, user_a):
    res = client.get("/api/auth/me", headers=headers_a)
    assert res.status_code == 200
    assert res.json()["username"] == user_a.username


def test_protected_route_without_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert "missing" in res.json()["detail"].lower()


def test_protected_route_with_invalid_token(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()
