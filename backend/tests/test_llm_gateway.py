import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.ai_service import ai_service
from app.models.ai_gateway import AIRequestLogModel, AIUsageModel
from app.models.user import UserModel
from app.core.security import hash_password

@pytest.mark.asyncio
async def test_llm_provider_abstraction(db_session: AsyncSession):
    # Register test user in DB
    user = UserModel(
        email="ai_tester@flowpilot.ai",
        password_hash=hash_password("Pass123!"),
        full_name="AI Tester"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Test AIService generate response
    res = await ai_service.generate_response(
        prompt="Explain vector search for freelancing knowledge base",
        user_id=user.id,
        db=db_session,
        provider="local",
        model="flowpilot-local-v1"
    )

    assert res.text is not None
    assert res.provider == "local"
    assert res.request_id.startswith("req_")
    assert res.usage.total_tokens > 0

    # Verify DB tracking tables
    req_res = await db_session.execute(select(AIRequestLogModel).where(AIRequestLogModel.user_id == user.id))
    requests = req_res.scalars().all()
    assert len(requests) == 1
    assert requests[0].provider == "local"

    usage_res = await db_session.execute(select(AIUsageModel).where(AIUsageModel.user_id == user.id))
    usage = usage_res.scalars().all()
    assert len(usage) == 1
    assert usage[0].total_tokens > 0

@pytest.mark.asyncio
async def test_llm_structured_output(db_session: AsyncSession):
    schema = {"suggestedAction": "string", "confidenceScore": "number"}
    out = await ai_service.structured_output(
        prompt="Generate task plan for lead qualification",
        response_schema=schema,
        user_id="user_123",
        db=db_session,
        provider="local"
    )
    assert isinstance(out, dict)
    assert "suggestedAction" in out

@pytest.mark.asyncio
async def test_ai_gateway_authenticated_api(async_client: AsyncClient):
    # 1. Unauthenticated request -> 401
    unauth_res = await async_client.post("/api/v1/ai/generate", json={"prompt": "Test prompt"})
    assert unauth_res.status_code == 401

    # 2. Register & Login
    await async_client.post("/api/v1/auth/register", json={
        "email": "gateway_user@flowpilot.ai",
        "password": "Password123!",
        "fullName": "Gateway User"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "gateway_user@flowpilot.ai",
        "password": "Password123!"
    })
    token = login_res.cookies["flowpilot_session"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Authenticated generate request -> 200
    gen_res = await async_client.post("/api/v1/ai/generate", json={
        "prompt": "Prioritize freelancing projects",
        "provider": "local",
        "model": "flowpilot-local-v1"
    }, headers=headers)
    assert gen_res.status_code == 200
    data = gen_res.json()
    assert "requestId" in data
    assert "usage" in data

    # 4. Get providers endpoint
    prov_res = await async_client.get("/api/v1/ai/providers", headers=headers)
    assert prov_res.status_code == 200
    assert "providers" in prov_res.json()

    # 5. Get usage stats endpoint
    usage_res = await async_client.get("/api/v1/ai/usage", headers=headers)
    assert usage_res.status_code == 200
    assert usage_res.json()["totalRequests"] >= 1
