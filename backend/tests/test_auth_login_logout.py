import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_and_logout_flow(async_client: AsyncClient):
    # 1. Register User
    reg_payload = {
        "email": "login_test@flowpilot.ai",
        "password": "CorrectPassword123!",
        "fullName": "Login Tester"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    # 2. Invalid password login attempt
    bad_login = {
        "email": "login_test@flowpilot.ai",
        "password": "WrongPassword!"
    }
    bad_res = await async_client.post("/api/v1/auth/login", json=bad_login)
    assert bad_res.status_code == 401

    # 3. Correct login attempt
    good_login = {
        "email": "login_test@flowpilot.ai",
        "password": "CorrectPassword123!"
    }
    good_res = await async_client.post("/api/v1/auth/login", json=good_login)
    assert good_res.status_code == 200
    assert "flowpilot_session" in good_res.cookies
    token = good_res.cookies["flowpilot_session"]

    headers = {"Authorization": f"Bearer {token}"}

    # 4. Fetch authenticated user profile using token header
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["fullName"] == "Login Tester"

    # 5. Logout
    logout_res = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # 6. Verify subsequent requests fail
    post_logout_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert post_logout_res.status_code == 401
