import os
import json
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.services.llm.telemetry import llm_metrics


async def _get_auth_token(async_client: AsyncClient, email: str) -> str:
    """Helper to register/login test user and extract session token."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "fullName": "Phase5 Smoke Tester"}
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    assert login_res.status_code == 200
    token = login_res.cookies.get("flowpilot_session") or login_res.json().get("access_token", "")
    return token


@pytest.mark.asyncio
async def test_phase5_health_probes(async_client: AsyncClient):
    """1. Health Verification: /health, /ready, /version."""
    res_health = await async_client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "active"

    res_ready = await async_client.get("/ready")
    assert res_ready.status_code in [200, 503]
    if res_ready.status_code == 200:
        assert res_ready.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_phase5_live_nvidia_generation_smoke_test(async_client: AsyncClient):
    """
    2. Live API Smoke Test against NVIDIA NIM provider.
    Prompt: 'Reply with exactly: PRODUCTION NVIDIA SMOKE TEST OK'
    """
    token = await _get_auth_token(async_client, "phase5_user1@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    prompt = "Reply with exactly: PRODUCTION NVIDIA SMOKE TEST OK"
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

    # Response assertions
    assert "text" in data
    assert len(data["text"].strip()) > 0
    assert data["provider"] == "nvidia"
    assert data["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert "usage" in data
    assert data["usage"]["inputTokens"] > 0
    assert data["usage"]["outputTokens"] > 0

    # Redaction audit
    raw_key = os.getenv("LLM_API_KEY", "")
    if raw_key:
        assert raw_key not in json.dumps(data)


@pytest.mark.asyncio
async def test_phase5_structured_output_smoke_test(async_client: AsyncClient):
    """3. Structured Output Smoke Test."""
    token = await _get_auth_token(async_client, "phase5_user2@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "gateway_status": {"type": "string"}
        },
        "required": ["status"]
    }

    res = await async_client.post(
        "/api/v1/ai/structured",
        json={
            "prompt": "Provide status JSON with status: OK",
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
async def test_phase5_telemetry_and_usage_persistence(async_client: AsyncClient):
    """4. Observability & DB usage tracking persistence verification."""
    token = await _get_auth_token(async_client, "phase5_user3@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Check metrics endpoint
    metrics_res = await async_client.get("/api/v1/ai/metrics", headers=headers)
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()

    assert "totalRequests" in metrics_data
    assert "successfulRequests" in metrics_data
    assert "latencyMs" in metrics_data

    # Check usage history endpoint
    usage_res = await async_client.get("/api/v1/ai/usage", headers=headers)
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert "recentRequests" in usage_data



@pytest.mark.asyncio
async def test_phase5_security_and_secrets_leak_audit(async_client: AsyncClient):
    """5. Security audit ensuring zero secret leakage across responses and providers."""
    token = await _get_auth_token(async_client, "phase5_user4@flowpilot.ai")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    providers_res = await async_client.get("/api/v1/ai/providers", headers=headers)
    assert providers_res.status_code == 200
    providers_str = json.dumps(providers_res.json())

    raw_key = os.getenv("LLM_API_KEY", "")
    if raw_key:
        assert raw_key not in providers_str
        assert "nvapi-" not in providers_str
        assert "sk-" not in providers_str
