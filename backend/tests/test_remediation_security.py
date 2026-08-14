import pytest
from httpx import AsyncClient
from app.core.config import Settings


@pytest.mark.asyncio
async def test_lead_cross_tenant_isolation(async_client: AsyncClient):
    """VULN-001 Tests 1-3: Verify User A cannot read, update, or delete User B's CRM leads."""
    # 1. User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "lead_user_a@flowpilot.ai", "password": "Password123!", "fullName": "Lead Owner A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "lead_user_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # 2. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "lead_user_b@flowpilot.ai", "password": "Password123!", "fullName": "Lead Owner B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "lead_user_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]

    # 3. User A creates a lead
    create_res = await async_client.post(
        "/api/v1/leads",
        json={"name": "Alice Lead", "company": "Acme User A Corp", "email": "alice@acmea.com"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_res.status_code == 200
    lead_a_id = create_res.json()["id"]

    # 4. User B attempts to list leads -> Lead A MUST NOT be present
    b_list = await async_client.get(
        "/api/v1/leads",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_list.status_code == 200
    b_lead_ids = [l["id"] for l in b_list.json()["leads"]]
    assert lead_a_id not in b_lead_ids, "VULN-001 Failure: User B listed User A's lead!"

    # 5. User B attempts GET lead A by ID -> 404
    b_get = await async_client.get(
        f"/api/v1/leads/{lead_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_get.status_code == 404, "VULN-001 Failure: User B read User A's lead detail!"

    # 6. User B attempts PATCH lead A -> 404
    b_patch = await async_client.patch(
        f"/api/v1/leads/{lead_a_id}",
        json={"notes": "Malicious edit by User B"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_patch.status_code == 404, "VULN-001 Failure: User B edited User A's lead!"

    # 7. User B attempts DELETE lead A -> 404
    b_delete = await async_client.delete(
        f"/api/v1/leads/{lead_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_delete.status_code == 404, "VULN-001 Failure: User B deleted User A's lead!"


@pytest.mark.asyncio
async def test_project_unauthenticated_and_cross_tenant_security(async_client: AsyncClient):
    """VULN-002 Tests 4-7: Verify unauthenticated project requests return 401 and cross-tenant access is blocked."""
    # 1. Unauthenticated GET /api/v1/projects -> 401
    unauth_res = await async_client.get("/api/v1/projects")
    assert unauth_res.status_code in [401, 403], "VULN-002 Failure: Unauthenticated access to /api/v1/projects allowed!"

    # 2. User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "proj_user_a@flowpilot.ai", "password": "Password123!", "fullName": "Project Owner A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "proj_user_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # 3. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "proj_user_b@flowpilot.ai", "password": "Password123!", "fullName": "Project Owner B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "proj_user_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]

    # 4. User A creates a project
    proj_res = await async_client.post(
        "/api/v1/projects",
        json={"title": "User A Private Web App", "clientName": "Acme Corp", "status": "in_progress", "deadline": "2026-12-31", "progressPercent": 50, "hourlyRate": 150.0},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert proj_res.status_code == 201
    proj_id_a = proj_res.json()["id"]

    # 5. User B lists projects -> Project A MUST NOT be present
    b_list = await async_client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_list.status_code == 200
    b_proj_ids = [p["id"] for p in b_list.json()]
    assert proj_id_a not in b_proj_ids, "VULN-002 Failure: User B listed User A's project!"

    # 6. User B GET project by ID -> 404
    b_get = await async_client.get(
        f"/api/v1/projects/{proj_id_a}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_get.status_code == 404, "VULN-002 Failure: User B read User A's project detail!"

    # 7. User B DELETE project -> 404
    b_del = await async_client.delete(
        f"/api/v1/projects/{proj_id_a}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_del.status_code == 404, "VULN-002 Failure: User B deleted User A's project!"


@pytest.mark.asyncio
async def test_agent_run_isolation(async_client: AsyncClient):
    """VULN-003 Tests 8-9: Verify agent run execution logs are strictly isolated by tenant."""
    # 1. User A Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "agent_user_a@flowpilot.ai", "password": "Password123!", "fullName": "Agent Owner A"})
    login_a = await async_client.post("/api/v1/auth/login", json={"email": "agent_user_a@flowpilot.ai", "password": "Password123!"})
    token_a = login_a.cookies["flowpilot_session"]

    # 2. User B Register & Login
    await async_client.post("/api/v1/auth/register", json={"email": "agent_user_b@flowpilot.ai", "password": "Password123!", "fullName": "Agent Owner B"})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": "agent_user_b@flowpilot.ai", "password": "Password123!"})
    token_b = login_b.cookies["flowpilot_session"]

    # 3. User A triggers agent task
    run_res = await async_client.post(
        "/api/v1/agents/run",
        json={"query": "Research target market strategy for User A"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert run_res.status_code == 200
    run_id_a = run_res.json()["runId"]

    # 4. User B lists agent runs -> Run A MUST NOT be present
    b_runs = await async_client.get(
        "/api/v1/agents/runs",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_runs.status_code == 200
    b_run_ids = [r["runId"] for r in b_runs.json()["runs"]]
    assert run_id_a not in b_run_ids, "VULN-003 Failure: User B listed User A's agent run!"

    # 5. User B GET run detail by ID -> 404
    b_detail = await async_client.get(
        f"/api/v1/agents/runs/{run_id_a}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_detail.status_code == 404, "VULN-003 Failure: User B read User A's agent run detail!"


def test_production_secret_key_validation():
    """VULN-004 Tests 10-12: Verify production mode fails closed on insecure or default SECRET_KEY."""
    # Test 10 & 11: Production startup with insecure default SECRET_KEY fails
    insecure_keys = [
        "production-secret-key-change-me-in-prod",
        "secret",
        "change-me",
        "short_key_123"
    ]
    for key in insecure_keys:
        with pytest.raises(ValueError, match="Production configuration error: Insecure or default SECRET_KEY configured."):
            Settings(ENVIRONMENT="production", SECRET_KEY=key)

    # Test 12: Valid production SECRET_KEY starts successfully
    valid_key = "a_super_secure_random_64_character_production_secret_key_998877"
    valid_settings = Settings(ENVIRONMENT="production", SECRET_KEY=valid_key)
    assert valid_settings.SECRET_KEY == valid_key
