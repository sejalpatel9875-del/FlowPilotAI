import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_registration(async_client: AsyncClient):
    payload = {
        "email": "developer@flowpilot.ai",
        "password": "SecurePassword123!",
        "fullName": "Jane Developer"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "developer@flowpilot.ai"
    assert data["fullName"] == "Jane Developer"
    assert "password" not in data
    assert "password_hash" not in data
    assert "USER" in data["roles"]

@pytest.mark.asyncio
async def test_duplicate_email_registration_fails(async_client: AsyncClient):
    payload = {
        "email": "duplicate@flowpilot.ai",
        "password": "SecurePassword123!",
        "fullName": "First User"
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]
