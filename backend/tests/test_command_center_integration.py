import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.command_center import CommandRecommendationModel

@pytest.mark.asyncio
async def test_command_center_what_should_i_do_next_workflow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "command_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Command Operator"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "command_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Trigger "What should I do next?" Endpoint
    what_res = await async_client.post("/api/v1/command/what-should-i-do-next", headers=headers)
    assert what_res.status_code == 200
    data = what_res.json()
    assert "recommendationId" in data
    rec_id = data["recommendationId"]
    assert len(data["topRecommendations"]) == 3

    # Check top recommendation structure
    top_rec = data["topRecommendations"][0]
    assert "title" in top_rec
    assert "reason" in top_rec
    assert "estimatedTime" in top_rec
    assert "priority" in top_rec
    assert "relatedObject" in top_rec
    assert "suggestedAction" in top_rec

    # 3. Apply User Actions (ACCEPT, DISMISS, RESCHEDULE, START_FOCUS)
    act_res = await async_client.post(f"/api/v1/command/recommendations/{rec_id}/action", json={"action": "ACCEPT"}, headers=headers)
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACCEPT"

    focus_res = await async_client.post(f"/api/v1/command/recommendations/{rec_id}/action", json={"action": "START_FOCUS"}, headers=headers)
    assert focus_res.status_code == 200
    assert focus_res.json()["status"] == "START_FOCUS"
