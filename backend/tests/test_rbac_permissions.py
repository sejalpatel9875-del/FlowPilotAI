import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_unauthorized_api_access(async_client: AsyncClient):
    # Attempting to access protected endpoint without session cookie or bearer token
    res = await async_client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

@pytest.mark.asyncio
async def test_rbac_authorization_enforcement(async_client: AsyncClient):
    # Register standard user
    reg = await async_client.post("/api/v1/auth/register", json={
        "email": "standard_user@flowpilot.ai",
        "password": "UserPassword123!",
        "fullName": "Standard User"
    })
    assert reg.status_code == 201

    login = await async_client.post("/api/v1/auth/login", json={
        "email": "standard_user@flowpilot.ai",
        "password": "UserPassword123!"
    })
    assert login.status_code == 200
    token = login.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # Standard user attempts to call ADMIN-restricted endpoint -> 403 Forbidden
    admin_res = await async_client.get("/api/v1/auth/admin/test-rbac", headers=headers)
    assert admin_res.status_code == 403
    assert "Required role: ADMIN" in admin_res.json()["detail"]
