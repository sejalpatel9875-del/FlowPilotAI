import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.time_management import TimeBlockModel

@pytest.mark.asyncio
async def test_time_management_planner_workflow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "time_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Time Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "time_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Trigger AI Daily Planner
    plan_res = await async_client.post("/api/v1/time/plan-day", headers=headers)
    assert plan_res.status_code == 200
    assert len(plan_res.json()["topPriorities"]) == 3
    assert plan_res.json()["totalBlocksScheduled"] >= 1

    # 3. Retrieve Schedule for Today
    sched_res = await async_client.get("/api/v1/time/schedule?view=today", headers=headers)
    assert sched_res.status_code == 200
    blocks = sched_res.json()["timeBlocks"]
    assert len(blocks) >= 1
    block_id = blocks[0]["id"]

    # 4. Trigger Quick 60-Minute Plan ("I only have 60 min")
    quick_res = await async_client.post("/api/v1/time/quick-plan", json={"minutes": 60}, headers=headers)
    assert quick_res.status_code == 200
    assert quick_res.json()["timeBudgetMinutes"] == 60
    assert "aiQuickPlan" in quick_res.json()

    # 5. Trigger Intelligent Missed Task Recalculation
    recalc_res = await async_client.post("/api/v1/time/recalculate-missed", headers=headers)
    assert recalc_res.status_code == 200
    assert "aiRecalculation" in recalc_res.json()

    # 6. Apply TimeBlock Actions (COMPLETE, SPLIT, REDUCE_SCOPE)
    act_res = await async_client.post(f"/api/v1/time/blocks/{block_id}/action", json={"action": "COMPLETE"}, headers=headers)
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "COMPLETED"

    split_res = await async_client.post(f"/api/v1/time/blocks/{block_id}/action", json={"action": "SPLIT"}, headers=headers)
    assert split_res.status_code == 200
    assert "Split" in split_res.json()["title"]
