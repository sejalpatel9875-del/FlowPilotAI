import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent_orchestrator import agent_orchestrator
from app.services.agents.agent_implementations import LearningAgent, OutreachAgent
from app.models.user import UserModel
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_agent_permission_enforcement():
    agent = LearningAgent()

    # Allowed tools should pass check
    agent.check_permission("knowledge_search")
    agent.check_permission("task_creation")

    # Strictly denied tools must raise PermissionError
    with pytest.raises(PermissionError) as exc1:
        agent.check_permission("external_message_send")
    assert "DENIED" in str(exc1.value)

    with pytest.raises(PermissionError) as exc2:
        agent.check_permission("database_delete")
    assert "DENIED" in str(exc2.value)

@pytest.mark.asyncio
async def test_agent_orchestrator_routing(db_session: AsyncSession):
    user = UserModel(email="orchestrator_user@flowpilot.ai", password_hash=hash_password("Pass123!"), full_name="Orchestrator User")
    db_session.add(user)
    await db_session.commit()

    # Query routing
    res_lead = await agent_orchestrator.execute_agent_task("Score lead for TechCorp", user_id=user.id, db=db_session)
    assert res_lead["agentName"] == "LeadAgent"

    res_outreach = await agent_orchestrator.execute_agent_task("Send cold email outreach to VP", user_id=user.id, db=db_session)
    assert res_outreach["agentName"] == "OutreachAgent"
    assert res_outreach["status"] == "needs_approval"

@pytest.mark.asyncio
async def test_agent_approval_api_workflow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "agent_approver@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Approver User"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "agent_approver@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Run OutreachAgent (Requires approval)
    run_res = await async_client.post("/api/v1/agents/run", json={
        "query": "Send email outreach proposal",
        "agentName": "OutreachAgent"
    }, headers=headers)

    assert run_res.status_code == 200
    data = run_res.json()
    assert data["status"] == "needs_approval"
    run_id = data["runId"]

    # 3. Get run detail
    detail_res = await async_client.get(f"/api/v1/agents/runs/{run_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "needs_approval"

    # 4. Approve action
    app_res = await async_client.post(f"/api/v1/agents/runs/{run_id}/approve", headers=headers)
    assert app_res.status_code == 200

    # 5. Verify status updated to completed
    detail_after = await async_client.get(f"/api/v1/agents/runs/{run_id}", headers=headers)
    assert detail_after.json()["status"] == "completed"
