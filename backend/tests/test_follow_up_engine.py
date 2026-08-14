import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.follow_up import FollowUpSequenceModel, FollowUpModel
from app.models.lead import LeadModel

@pytest.mark.asyncio
async def test_followup_engine_workflow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "followup_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "FollowUp Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "followup_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest Lead
    lead_res = await async_client.post("/api/v1/leads", json={
        "name": "Bruce Wayne",
        "company": "Wayne Enterprises",
        "email": "bruce@wayneent.com",
        "industry": "Defense Tech",
        "serviceFit": "High"
    }, headers=headers)
    lead_id = lead_res.json()["id"]

    # 3. Start 3-Step Follow-Up Sequence
    start_res = await async_client.post("/api/v1/follow-ups/start", json={
        "leadId": lead_id
    }, headers=headers)
    assert start_res.status_code == 200
    seq_id = start_res.json()["sequenceId"]

    # 4. List Queue Items in Upcoming
    queue_res = await async_client.get("/api/v1/follow-ups?queue=upcoming", headers=headers)
    assert queue_res.status_code == 200
    items = queue_res.json()["items"]
    assert len(items) >= 1
    fu_id = items[0]["id"]

    # 5. Execute AI "Why should I follow up?"
    explain_res = await async_client.post(f"/api/v1/follow-ups/{fu_id}/explain", headers=headers)
    assert explain_res.status_code == 200
    assert "aiReasoning" in explain_res.json()

    # 6. Generate AI Follow-Up Draft
    draft_res = await async_client.post(f"/api/v1/follow-ups/{fu_id}/generate-draft", headers=headers)
    assert draft_res.status_code == 200
    assert "draftBody" in draft_res.json()

    # 7. Send Follow-Up
    send_res = await async_client.post(f"/api/v1/follow-ups/{fu_id}/send", headers=headers)
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_automatic_stop_condition_on_lead_reply(async_client: AsyncClient):
    # Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "stop_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Stop Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "stop_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ingest Lead
    lead_res = await async_client.post("/api/v1/leads", json={
        "name": "Clark Kent",
        "company": "Daily Planet",
        "email": "clark@dailyplanet.com"
    }, headers=headers)
    lead_id = lead_res.json()["id"]

    # Start Sequence
    await async_client.post("/api/v1/follow-ups/start", json={"leadId": lead_id}, headers=headers)

    # Lead replies -> Patch lead status to "Replied"
    await async_client.patch(f"/api/v1/leads/{lead_id}", json={"status": "Replied"}, headers=headers)

    # Verify queue moves item to STOPPED
    stopped_res = await async_client.get("/api/v1/follow-ups?queue=stopped", headers=headers)
    assert stopped_res.status_code == 200
    stopped_items = stopped_res.json()["items"]
    assert len(stopped_items) >= 1
    assert stopped_items[0]["company"] == "Daily Planet"
