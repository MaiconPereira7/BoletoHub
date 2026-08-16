from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "strongpassword1", "full_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body


async def test_register_duplicate_email(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": test_user.email, "password": "anotherpassword1"},
    )
    assert response.status_code == 400


async def test_login_success(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "supersecret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_me_with_valid_token(client: AsyncClient, auth_headers: dict[str, str], test_user: User) -> None:
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


async def test_me_with_invalid_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


async def test_me_without_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401
