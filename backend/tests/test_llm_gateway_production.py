import pytest
import json
from httpx import AsyncClient
from app.services.llm.base_provider import LLMRequest, LLMResponse, LLMUsage
from app.services.llm_service import LLMService
from app.services.llm.provider_registry import llm_provider_registry


@pytest.mark.asyncio
async def test_authenticated_ai_generation_succeeds(async_client: AsyncClient):
    """1. Test authenticated AI generation endpoint."""
    await async_client.post("/api/v1/auth/register", json={"email": "llm_user1@flowpilot.ai", "password": "Password123!", "fullName": "LLM User 1"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "llm_user1@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    res = await async_client.post(
        "/api/v1/ai/generate",
        json={"prompt": "Summarize today's priority leads", "provider": "gemini"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    assert data["provider"] == "gemini"
    assert "usage" in data
    assert data["usage"]["totalTokens"] > 0


@pytest.mark.asyncio
async def test_unauthenticated_ai_request_rejected(async_client: AsyncClient):
    """2. Test unauthenticated AI generation request returns 401."""
    res = await async_client.post(
        "/api/v1/ai/generate",
        json={"prompt": "Unauthenticated prompt attempt"}
    )
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_provider_selection_adapters(async_client: AsyncClient):
    """3. Test provider adapter selection across Gemini, OpenAI, and Ollama."""
    await async_client.post("/api/v1/auth/register", json={"email": "llm_user2@flowpilot.ai", "password": "Password123!", "fullName": "LLM User 2"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "llm_user2@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    for provider_name in ["gemini", "openai", "ollama", "nvidia"]:
        res = await async_client.post(
            "/api/v1/ai/generate",
            json={"prompt": f"Test provider dispatch for {provider_name}", "provider": provider_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        assert res.json()["provider"] == provider_name


@pytest.mark.asyncio
async def test_structured_output_json_schema_validation(async_client: AsyncClient):
    """4. Test validated structured JSON schema output."""
    await async_client.post("/api/v1/auth/register", json={"email": "llm_user3@flowpilot.ai", "password": "Password123!", "fullName": "LLM User 3"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "llm_user3@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "actionRequired": {"type": "boolean"},
            "confidenceScore": {"type": "number"}
        },
        "required": ["summary", "actionRequired"]
    }

    res = await async_client.post(
        "/api/v1/ai/structured",
        json={"prompt": "Analyze lead readiness score", "jsonSchema": schema, "provider": "gemini"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "structuredOutput" in data


@pytest.mark.asyncio
async def test_usage_tracking_in_database(async_client: AsyncClient):
    """5. Test AI token usage tracking and history API."""
    await async_client.post("/api/v1/auth/register", json={"email": "llm_user4@flowpilot.ai", "password": "Password123!", "fullName": "LLM User 4"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "llm_user4@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    # Trigger 2 AI generations
    await async_client.post("/api/v1/ai/generate", json={"prompt": "Query 1"}, headers={"Authorization": f"Bearer {token}"})
    await async_client.post("/api/v1/ai/generate", json={"prompt": "Query 2"}, headers={"Authorization": f"Bearer {token}"})

    # Fetch Usage
    usage_res = await async_client.get("/api/v1/ai/usage", headers={"Authorization": f"Bearer {token}"})
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert usage_data["summaryMetrics"]["totalRequests"] >= 2
    assert usage_data["summaryMetrics"]["totalTokensConsumed"] > 0


@pytest.mark.asyncio
async def test_sensitive_data_redaction_before_llm_dispatch(async_client: AsyncClient):
    """6. Test passwords and secret keys in user prompt are redacted before sending to LLM."""
    await async_client.post("/api/v1/auth/register", json={"email": "llm_user5@flowpilot.ai", "password": "Password123!", "fullName": "LLM User 5"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "llm_user5@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    prompt_with_secret = "My secret password is Password123! and API key is sk-1234567890abcdef1234567890abcdef."
    res = await async_client.post(
        "/api/v1/ai/generate",
        json={"prompt": prompt_with_secret},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    output_text = res.json()["text"]
    assert "sk-1234567890abcdef1234567890abcdef" not in output_text


@pytest.mark.asyncio
async def test_nvidia_provider_reasoning_stripping_and_key_redaction(async_client: AsyncClient):
    """7. Test NVIDIA provider reasoning content is NEVER exposed to frontend and API key is redacted."""
    await async_client.post("/api/v1/auth/register", json={"email": "nvidia_user@flowpilot.ai", "password": "Password123!", "fullName": "Nvidia User"})
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "nvidia_user@flowpilot.ai", "password": "Password123!"})
    token = login_res.cookies["flowpilot_session"]

    res = await async_client.post(
        "/api/v1/ai/generate",
        json={"prompt": "Analyze lead readiness with reasoning", "provider": "nvidia", "enableReasoning": True},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "nvidia"
    assert "<think>" not in data["text"]
    assert "</think>" not in data["text"]
    assert "Internal Reasoning:" not in data["text"]

