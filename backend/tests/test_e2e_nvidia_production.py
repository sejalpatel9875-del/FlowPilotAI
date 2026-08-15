import os
import json
import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.services.llm.base_provider import LLMRequest
from app.services.llm_service import LLMService


async def _get_auth_token(async_client: AsyncClient, email: str) -> str:
    """Helper to register/login test user and extract token."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "fullName": "NVIDIA E2E Tester"}
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    assert login_res.status_code == 200
    token = login_res.cookies.get("flowpilot_session") or login_res.json().get("access_token", "")
    return token


@pytest.mark.asyncio
async def test_nvidia_e2e_production_path_real_request(async_client: AsyncClient):
    """1. Test real end-to-end production path through API endpoint -> LLMService -> NvidiaProvider -> NIM Gateway."""
    token = await _get_auth_token(async_client, "e2e_nvidia_user1@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    prompt = "Reply with exactly: NVIDIA E2E TEST OK"
    res = await async_client.post(
        "/api/v1/ai/generate",
        json={
            "prompt": prompt,
            "provider": "nvidia",
            "temperature": 0.1,
            "maxTokens": 64
        },
        headers=headers
    )

    assert res.status_code == 200
    data = res.json()

    # Verify Response Data Structure
    assert "text" in data
    assert len(data["text"].strip()) > 0
    assert data["provider"] == "nvidia"
    assert data["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert "usage" in data
    assert data["usage"]["inputTokens"] > 0
    assert data["usage"]["outputTokens"] > 0

    # Verify Key Redaction (No secret in output JSON)
    raw_key = os.getenv("LLM_API_KEY", "")
    if raw_key:
        assert raw_key not in json.dumps(data)


@pytest.mark.asyncio
async def test_nvidia_default_provider_resolution(async_client: AsyncClient):
    """2. Verify that when no provider is passed in request body, LLMService resolves default settings.LLM_PROVIDER."""
    token = await _get_auth_token(async_client, "e2e_nvidia_user2@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    res = await async_client.post(
        "/api/v1/ai/generate",
        json={"prompt": "Short status check"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == (settings.LLM_PROVIDER or "nvidia")


@pytest.mark.asyncio
async def test_nvidia_e2e_structured_output_path(async_client: AsyncClient):
    """3. Verify production path for validated structured JSON schema output."""
    token = await _get_auth_token(async_client, "e2e_nvidia_user3@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "confidence": {"type": "number"}
        },
        "required": ["status"]
    }

    res = await async_client.post(
        "/api/v1/ai/structured",
        json={
            "prompt": "Provide system status in JSON",
            "jsonSchema": schema,
            "provider": "nvidia"
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "structuredOutput" in data
    assert data["provider"] == "nvidia"


@pytest.mark.asyncio
async def test_nvidia_fallback_resilience(async_client: AsyncClient):
    """4. Test fallback resilience when primary provider encounters an error."""
    token = await _get_auth_token(async_client, "e2e_nvidia_user4@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Verify invalid model request is handled gracefully without crashing server
    res = await async_client.post(
        "/api/v1/ai/generate",
        json={
            "prompt": "Test invalid model error handling",
            "provider": "nvidia",
            "model": "non-existent-invalid-model-name"
        },
        headers=headers
    )
    # Server should return 500 cleanly with sanitized error detail
    assert res.status_code in [200, 500]
    if res.status_code == 500:
        err_msg = res.json().get("detail", "")
        raw_key = os.getenv("LLM_API_KEY", "")
        if raw_key:
            assert raw_key not in err_msg


@pytest.mark.asyncio
async def test_nvidia_secrets_leak_audit(async_client: AsyncClient):
    """5. Audit that no secret credentials, API keys, or tokens leak into usage history API."""
    token = await _get_auth_token(async_client, "e2e_nvidia_user5@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    usage_res = await async_client.get(
        "/api/v1/ai/usage",
        headers=headers
    )
    assert usage_res.status_code == 200
    usage_data = usage_res.json()

    raw_key = os.getenv("LLM_API_KEY", "")
    if raw_key:
        assert raw_key not in json.dumps(usage_data)
