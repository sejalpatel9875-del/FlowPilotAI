import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.automation import AutomationModel, AutomationRunModel

@pytest.mark.asyncio
async def test_automation_engine_and_7_stage_pipeline_flow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "auto_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Automation Engineer"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "auto_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List Automations & Pre-built Templates
    list_res = await async_client.get("/api/v1/automations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["templates"]) >= 4

    # 3. Create Custom Automation Rule
    create_res = await async_client.post("/api/v1/automations", json={
        "name": "Auto-Qualify & Draft Pitch on New Lead",
        "triggerType": "NEW_LEAD",
        "actionType": "GENERATE_DRAFT",
        "aiDecisionPrompt": "Evaluate lead score and generate pitch.",
        "requiresApproval": True
    }, headers=headers)

    assert create_res.status_code == 200
    auto_id = create_res.json()["id"]
    assert create_res.json()["triggerType"] == "NEW_LEAD"
    assert create_res.json()["actionType"] == "GENERATE_DRAFT"

    # 4. Trigger 7-Stage Execution Test Run
    test_res = await async_client.post(f"/api/v1/automations/{auto_id}/test", headers=headers)
    assert test_res.status_code == 200
    assert test_res.json()["status"] == "PENDING_APPROVAL"
    assert "aiDecisionSummary" in test_res.json()

    # 5. Retrieve Execution & Failure Audit Logs
    runs_res = await async_client.get("/api/v1/automations/runs", headers=headers)
    assert runs_res.status_code == 200
    assert runs_res.json()["totalRuns"] >= 1

    # 6. Toggle Status (Pause / Resume)
    pause_res = await async_client.post(f"/api/v1/automations/{auto_id}/status", json={"status": "PAUSED"}, headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"
    assert pause_res.json()["isActive"] == False
