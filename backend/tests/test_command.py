import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_command_process_endpoint(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json={"email": "cmd_user@flowpilot.ai", "password": "Password123!", "fullName": "Cmd User"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "cmd_user@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    payload = {"query": "What should I focus on next?"}
    response = await async_client.post(
        "/api/v1/command/process",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "suggestedAction" in data
    assert "reasoning" in data
    assert "recommendedSteps" in data
    assert isinstance(data["recommendedSteps"], list)
