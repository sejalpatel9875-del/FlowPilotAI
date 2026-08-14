import pytest
from httpx import AsyncClient
from app.core.config import Settings
from app.models.agent_engine import AgentMessageModel, ToolCallModel


@pytest.mark.asyncio
async def test_migration_and_lead_tenant_isolation_verification(async_client: AsyncClient):
    """Section 2: Lead Tenant Isolation (User A & User B inverse HTTP verification)."""
    # 1. User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "verif_lead_a@flowpilot.ai", "password": "Password123!", "fullName": "Verif Lead A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "verif_lead_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # 2. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "verif_lead_b@flowpilot.ai", "password": "Password123!", "fullName": "Verif Lead B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "verif_lead_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]

    # 3. User A creates Lead A
    res_a = await async_client.post(
        "/api/v1/leads",
        json={"name": "Lead A Contact", "company": "User A Company", "email": "leada@usera.com"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200
    lead_a_id = res_a.json()["id"]

    # 4. User B creates Lead B
    res_b = await async_client.post(
        "/api/v1/leads",
        json={"name": "Lead B Contact", "company": "User B Company", "email": "leadb@userb.com"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b.status_code == 200
    lead_b_id = res_b.json()["id"]

    # --- USER A TESTS ---
    # User A can list Lead A, cannot see Lead B
    list_a = await async_client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token_a}"})
    ids_a = [l["id"] for l in list_a.json()["leads"]]
    assert lead_a_id in ids_a
    assert lead_b_id not in ids_a

    # User A can view Lead A, cannot view Lead B
    view_a_a = await async_client.get(f"/api/v1/leads/{lead_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert view_a_a.status_code == 200
    view_a_b = await async_client.get(f"/api/v1/leads/{lead_b_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert view_a_b.status_code == 404

    # User A can update Lead A, cannot update Lead B
    patch_a_a = await async_client.patch(f"/api/v1/leads/{lead_a_id}", json={"notes": "A's note"}, headers={"Authorization": f"Bearer {token_a}"})
    assert patch_a_a.status_code == 200
    patch_a_b = await async_client.patch(f"/api/v1/leads/{lead_b_id}", json={"notes": "Spoofed note"}, headers={"Authorization": f"Bearer {token_a}"})
    assert patch_a_b.status_code == 404

    # User A cannot delete Lead B
    del_a_b = await async_client.delete(f"/api/v1/leads/{lead_b_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_a_b.status_code == 404

    # --- USER B INVERSE TESTS ---
    # User B can list Lead B, cannot see Lead A
    list_b = await async_client.get("/api/v1/leads", headers={"Authorization": f"Bearer {token_b}"})
    ids_b = [l["id"] for l in list_b.json()["leads"]]
    assert lead_b_id in ids_b
    assert lead_a_id not in ids_b

    # User B view/patch/delete Lead A -> all 404
    assert (await async_client.get(f"/api/v1/leads/{lead_a_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404
    assert (await async_client.patch(f"/api/v1/leads/{lead_a_id}", json={"notes": "B's edit"}, headers={"Authorization": f"Bearer {token_b}"})).status_code == 404
    assert (await async_client.delete(f"/api/v1/leads/{lead_a_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404


@pytest.mark.asyncio
async def test_project_tenant_isolation_verification(async_client: AsyncClient):
    """Section 3: Project Tenant Isolation (Unauthenticated rejection & User A/B inverse verification)."""
    # 1. Unauthenticated request -> 401
    unauth = await async_client.get("/api/v1/projects")
    assert unauth.status_code in [401, 403]

    # 2. User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "verif_proj_a@flowpilot.ai", "password": "Password123!", "fullName": "Verif Proj A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "verif_proj_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # 3. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "verif_proj_b@flowpilot.ai", "password": "Password123!", "fullName": "Verif Proj B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "verif_proj_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]

    # 4. User A creates Project A
    res_a = await async_client.post(
        "/api/v1/projects",
        json={"title": "Project A Web App", "clientName": "Client A", "status": "in_progress", "deadline": "2026-12-31", "progressPercent": 10, "hourlyRate": 120.0},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 201
    proj_a_id = res_a.json()["id"]

    # 5. User B creates Project B
    res_b = await async_client.post(
        "/api/v1/projects",
        json={"title": "Project B Mobile App", "clientName": "Client B", "status": "in_progress", "deadline": "2026-12-31", "progressPercent": 20, "hourlyRate": 140.0},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert res_b.status_code == 201
    proj_b_id = res_b.json()["id"]

    # User A accesses A, cannot access/delete B
    assert proj_a_id in [p["id"] for p in (await async_client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token_a}"})).json()]
    assert proj_b_id not in [p["id"] for p in (await async_client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token_a}"})).json()]
    assert (await async_client.get(f"/api/v1/projects/{proj_b_id}", headers={"Authorization": f"Bearer {token_a}"})).status_code == 404
    assert (await async_client.delete(f"/api/v1/projects/{proj_b_id}", headers={"Authorization": f"Bearer {token_a}"})).status_code == 404

    # User B accesses B, cannot access/delete A
    assert proj_b_id in [p["id"] for p in (await async_client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token_b}"})).json()]
    assert proj_a_id not in [p["id"] for p in (await async_client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token_b}"})).json()]
    assert (await async_client.get(f"/api/v1/projects/{proj_a_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404
    assert (await async_client.delete(f"/api/v1/projects/{proj_a_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404


@pytest.mark.asyncio
async def test_agent_run_and_log_isolation_verification(async_client: AsyncClient):
    """Section 4: Agent Run Isolation & Action Approve/Reject Verification."""
    # 1. User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "verif_agent_a@flowpilot.ai", "password": "Password123!", "fullName": "Verif Agent A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "verif_agent_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # 2. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "verif_agent_b@flowpilot.ai", "password": "Password123!", "fullName": "Verif Agent B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "verif_agent_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]

    # 3. User A triggers agent task requiring approval
    res_a = await async_client.post(
        "/api/v1/agents/run",
        json={"query": "Draft cold outreach email for User A", "agentName": "OutreachAgent"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert res_a.status_code == 200
    run_a_id = res_a.json()["runId"]

    # User B cannot list run A, view run A, approve run A, or reject run A
    b_runs = (await async_client.get("/api/v1/agents/runs", headers={"Authorization": f"Bearer {token_b}"})).json()["runs"]
    assert run_a_id not in [r["runId"] for r in b_runs]
    assert (await async_client.get(f"/api/v1/agents/runs/{run_a_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404
    assert (await async_client.post(f"/api/v1/agents/runs/{run_a_id}/approve", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404
    assert (await async_client.post(f"/api/v1/agents/runs/{run_a_id}/reject", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404


@pytest.mark.asyncio
async def test_client_supplied_user_id_spoofing_prevention(async_client: AsyncClient):
    """Section 5: Client-Supplied user_id Spoofing Prevention."""
    # User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "spoof_user_a@flowpilot.ai", "password": "Password123!", "fullName": "Spoof User A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "spoof_user_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # User B ID
    user_b_id = "user_b_fake_uuid_12345"

    # User A sends request containing user_id = USER_B_ID
    create_lead_res = await async_client.post(
        "/api/v1/leads",
        json={"name": "Spoof Lead", "company": "Spoof Corp", "email": "spoof@corp.com", "user_id": user_b_id},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_lead_res.status_code == 200
    lead_id = create_lead_res.json()["id"]

    # Verify that the lead belongs to User A, NOT User B
    lead_detail = await async_client.get(f"/api/v1/leads/{lead_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert lead_detail.status_code == 200
