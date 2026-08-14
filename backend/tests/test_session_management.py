import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_session_listing_and_logout_all(async_client: AsyncClient):
    # Register user
    await async_client.post("/api/v1/auth/register", json={
        "email": "session_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Multi Session User"
    })

    # First session login
    login1 = await async_client.post("/api/v1/auth/login", json={
        "email": "session_user@flowpilot.ai",
        "password": "Password123!"
    })
    token1 = login1.cookies["flowpilot_session"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # List active sessions
    sessions_res = await async_client.get("/api/v1/auth/sessions", headers=headers1)
    assert sessions_res.status_code == 200
    sessions_list = sessions_res.json()
    assert len(sessions_list) >= 1
    assert sessions_list[0]["isCurrentSession"] == True

    # Logout all sessions
    logout_all_res = await async_client.post("/api/v1/auth/logout-all", headers=headers1)
    assert logout_all_res.status_code == 200

    # Subsequent request using old token should fail with 401
    me_res = await async_client.get("/api/v1/auth/me", headers=headers1)
    assert me_res.status_code == 401
