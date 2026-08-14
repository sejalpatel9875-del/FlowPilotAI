import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_leads_crud(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "test_leads_crud@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Leads Tester"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "test_leads_crud@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Fetch empty leads
    res = await async_client.get("/api/v1/leads", headers=headers)
    assert res.status_code == 200
    assert res.json()["totalLeads"] == 0

    # 3. Create new lead
    payload = {
        "name": "Acme Corp",
        "company": "Acme Industries",
        "email": "contact@acme.com",
        "serviceFit": "High",
        "status": "New",
        "source": "Inbound"
    }
    create_res = await async_client.post("/api/v1/leads", json=payload, headers=headers)
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["company"] == "Acme Industries"
    assert "id" in created_data

    # 4. Verify lead is now in list
    list_res = await async_client.get("/api/v1/leads", headers=headers)
    assert list_res.status_code == 200
    leads = list_res.json()["leads"]
    assert len(leads) == 1
    assert leads[0]["email"] == "contact@acme.com"
