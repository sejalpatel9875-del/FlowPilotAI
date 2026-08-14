import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.outreach import OutreachMessageModel
from app.models.lead import LeadModel
from app.models.governance import AuditLogModel
from app.models.crm import LeadActivityModel

@pytest.mark.asyncio
async def test_outreach_engine_and_approval_inbox_flow(async_client: AsyncClient):
    # 1. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "outreach_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Outreach Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "outreach_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest Lead
    lead_res = await async_client.post("/api/v1/leads", json={
        "name": "Sarah Connor",
        "company": "Cyberdyne Systems",
        "email": "sarah@cyberdyne.io",
        "industry": "Artificial Intelligence",
        "serviceFit": "High"
    }, headers=headers)
    lead_id = lead_res.json()["id"]

    # 3. Generate Draft for Email
    gen_res = await async_client.post("/api/v1/outreach/generate", json={
        "leadId": lead_id,
        "channel": "Email",
        "customInstructions": "Offer a 15-min AI demo call."
    }, headers=headers)

    assert gen_res.status_code == 200
    msg_id = gen_res.json()["id"]
    assert gen_res.json()["status"] == "REVIEW"
    assert gen_res.json()["channel"] == "Email"

    # 4. List messages in Pending Review
    list_res = await async_client.get("/api/v1/outreach?status=REVIEW", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["totalMessages"] >= 1

    # 5. Edit Draft
    patch_res = await async_client.patch(f"/api/v1/outreach/{msg_id}", json={
        "subject": "Customized Subject Line",
        "draftBody": "Updated message body text for Sarah."
    }, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["subject"] == "Customized Subject Line"

    # 6. Approve Message
    app_res = await async_client.post(f"/api/v1/outreach/{msg_id}/approve", headers=headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"
    assert "approvedAt" in app_res.json()

    # 7. Send Message
    send_res = await async_client.post(f"/api/v1/outreach/{msg_id}/send", headers=headers)
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "SENT"
    assert "sentAt" in send_res.json()

    # 8. Verify lead stage updated to "Contacted"
    lead_detail = await async_client.get(f"/api/v1/leads/{lead_id}", headers=headers)
    assert lead_detail.json()["status"] == "Contacted"

@pytest.mark.asyncio
async def test_outreach_rejection_flow(async_client: AsyncClient):
    # Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "outreach_rej@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Outreach Rejection Manager"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "outreach_rej@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ingest Lead
    lead_res = await async_client.post("/api/v1/leads", json={
        "name": "John Doe",
        "company": "Nexus Corp",
        "email": "john@nexus.io"
    }, headers=headers)
    lead_id = lead_res.json()["id"]

    # Generate Draft for LinkedIn connection note
    gen_res = await async_client.post("/api/v1/outreach/generate", json={
        "leadId": lead_id,
        "channel": "LinkedIn connection note"
    }, headers=headers)
    msg_id = gen_res.json()["id"]

    # Reject / Cancel Message
    rej_res = await async_client.post(f"/api/v1/outreach/{msg_id}/reject", headers=headers)
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "CANCELLED"
