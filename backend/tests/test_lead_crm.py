import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.lead_crm_service import LeadCRMService, PIPELINE_STAGES
from app.models.lead import LeadModel
from app.models.crm import LeadActivityModel
from app.models.user import UserModel

@pytest.mark.asyncio
async def test_transparent_lead_scoring_algorithm():
    score_data = LeadCRMService.calculate_transparent_score(
        service_fit="High",
        industry="SaaS Engineering",
        has_contact_info=True,
        status="New"
    )
    assert score_data["totalScore"] >= 70
    assert "serviceFitScore" in score_data["breakdown"]
    assert "contactInfoScore" in score_data["breakdown"]

@pytest.mark.asyncio
async def test_lead_crm_api_workflow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "crm_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "CRM Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "crm_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Lead
    create_res = await async_client.post("/api/v1/leads", json={
        "name": "Alex Rivera",
        "company": "Acme SaaS Solutions",
        "email": "alex@acmesaassolutions.io",
        "industry": "Software / SaaS",
        "serviceFit": "High",
        "status": "New"
    }, headers=headers)

    assert create_res.status_code == 200
    lead_id = create_res.json()["id"]
    assert create_res.json()["status"] == "New"
    assert create_res.json()["leadScore"] > 50

    # 3. Verify all 11 pipeline stages listed
    list_res = await async_client.get("/api/v1/leads", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["pipelineStages"]) == 11

    # 4. Patch stage to "Qualified"
    patch_res = await async_client.patch(f"/api/v1/leads/{lead_id}", json={
        "status": "Qualified",
        "nextAction": "Draft custom proposal"
    }, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["currentStatus"] == "Qualified"

    # 5. Execute AI Action ("analyze")
    ai_res = await async_client.post(f"/api/v1/leads/{lead_id}/ai-action", json={
        "actionType": "analyze"
    }, headers=headers)
    assert ai_res.status_code == 200
    assert "aiOutput" in ai_res.json()

    # 6. Verify Lead Detail and Activity Timeline
    detail_res = await async_client.get(f"/api/v1/leads/{lead_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["activities"]) >= 2
