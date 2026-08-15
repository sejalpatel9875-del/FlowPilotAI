import os
import json
import asyncio
import pytest
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.llm.base_provider import LLMRequest, LLMResponse, LLMUsage, LLMProvider
from app.services.llm.nvidia_provider import NvidiaProvider
from app.services.llm.provider_registry import llm_provider_registry
from app.services.llm_service import LLMService


class MockFailingProvider(LLMProvider):
    def __init__(self, name: str, error_to_raise: Exception):
        self._name = name
        self.error_to_raise = error_to_raise
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def default_model(self) -> str:
        return "mock-model"

    async def generate(self, req: LLMRequest) -> LLMResponse:
        self.call_count += 1
        raise self.error_to_raise

    async def stream(self, req: LLMRequest) -> AsyncGenerator[str, None]:
        raise self.error_to_raise
        yield ""

    async def structured_output(self, req: LLMRequest, schema: Dict[str, Any]) -> LLMResponse:
        raise self.error_to_raise

    async def embed(self, text: str) -> List[float]:
        raise self.error_to_raise


class MockSuccessProvider(LLMProvider):
    def __init__(self, name: str, text: str = "Fallback provider response OK"):
        self._name = name
        self.text = text

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def default_model(self) -> str:
        return "mock-success-model"

    async def generate(self, req: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text=self.text,
            usage=LLMUsage(input_tokens=10, output_tokens=10, total_tokens=20),
            provider=self.provider_name,
            model=self.default_model
        )

    async def stream(self, req: LLMRequest) -> AsyncGenerator[str, None]:
        yield self.text

    async def structured_output(self, req: LLMRequest, schema: Dict[str, Any]) -> LLMResponse:
        return await self.generate(req)

    async def embed(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_scenario_a_transient_failure_and_retry():
    """Scenario A: Primary provider fails transiently twice, succeeds on retry 3."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.provider_name = "nvidia"
    
    success_resp = LLMResponse(
        text="Recovered response",
        usage=LLMUsage(input_tokens=5, output_tokens=5, total_tokens=10),
        provider="nvidia",
        model="nvidia/nemotron-3-ultra-550b-a55b"
    )
    mock_provider.generate = AsyncMock(side_effect=[
        RuntimeError("Transient network glitch 1"),
        RuntimeError("Transient network glitch 2"),
        success_resp
    ])

    req = LLMRequest(prompt="Test transient retry")
    res = await LLMService._execute_with_retry(mock_provider, req, max_retries=3)

    assert res.text == "Recovered response"
    assert mock_provider.generate.call_count == 3


@pytest.mark.asyncio
async def test_scenario_b_provider_timeout_and_fallback(db_session: AsyncSession):
    """Scenario B: Primary provider times out, triggers configured fallback provider successfully."""
    timeout_err = RuntimeError("NVIDIA API Timeout: Connection attempt timed out after 30s")
    failing_primary = MockFailingProvider("nvidia", timeout_err)
    fallback_succ = MockSuccessProvider("gemini", "Gemini Fallback After Timeout OK")

    with patch.object(llm_provider_registry, "get_provider", side_effect=lambda name: failing_primary if name == "nvidia" else fallback_succ):
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True):
            with patch.object(settings, "LLM_FALLBACK_PROVIDER", "gemini"):
                with patch.object(settings, "LLM_MAX_RETRIES", 1):
                    req = LLMRequest(prompt="Test timeout fallback")
                    res = await LLMService.generate(req, user_id="user_resilience_test", db=db_session, provider_name="nvidia")

                    assert res.provider == "gemini"
                    assert "Gemini Fallback After Timeout OK" in res.text
                    assert failing_primary.call_count == 1


@pytest.mark.asyncio
async def test_scenario_c_provider_rate_limit_429(db_session: AsyncSession):
    """Scenario C: Primary provider returns HTTP 429 Rate Limit error."""
    rate_limit_err = RuntimeError("NVIDIA API Error (429): Too Many Requests - Rate limit exceeded")
    failing_primary = MockFailingProvider("nvidia", rate_limit_err)
    fallback_succ = MockSuccessProvider("gemini", "Gemini Fallback After 429 OK")

    with patch.object(llm_provider_registry, "get_provider", side_effect=lambda name: failing_primary if name == "nvidia" else fallback_succ):
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True):
            with patch.object(settings, "LLM_FALLBACK_PROVIDER", "gemini"):
                with patch.object(settings, "LLM_MAX_RETRIES", 1):
                    req = LLMRequest(prompt="Test 429 rate limit")
                    res = await LLMService.generate(req, user_id="user_resilience_test", db=db_session, provider_name="nvidia")

                    assert res.provider == "gemini"
                    assert "Gemini Fallback After 429 OK" in res.text


@pytest.mark.asyncio
async def test_scenario_d_provider_5xx_server_error(db_session: AsyncSession):
    """Scenario D: Primary provider returns HTTP 503 Service Unavailable."""
    server_err = RuntimeError("NVIDIA API Error (503): Service Unavailable")
    failing_primary = MockFailingProvider("nvidia", server_err)
    fallback_succ = MockSuccessProvider("openai", "OpenAI Fallback After 503 OK")

    with patch.object(llm_provider_registry, "get_provider", side_effect=lambda name: failing_primary if name == "nvidia" else fallback_succ):
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True):
            with patch.object(settings, "LLM_FALLBACK_PROVIDER", "openai"):
                with patch.object(settings, "LLM_MAX_RETRIES", 1):
                    req = LLMRequest(prompt="Test 503 fallback")
                    res = await LLMService.generate(req, user_id="user_resilience_test", db=db_session, provider_name="nvidia")

                    assert res.provider == "openai"
                    assert "OpenAI Fallback After 503 OK" in res.text


@pytest.mark.asyncio
async def test_scenario_e_all_providers_fail(db_session: AsyncSession):
    """Scenario E: Primary and fallback providers both fail; returns sanitized error with zero secret leakage."""
    err_primary = RuntimeError("Primary failure (Secret: nvapi-secret-key-12345)")
    err_fallback = RuntimeError("Fallback failure (Secret: nvapi-secret-key-12345)")

    failing_primary = MockFailingProvider("nvidia", err_primary)
    failing_fallback = MockFailingProvider("gemini", err_fallback)

    with patch.object(llm_provider_registry, "get_provider", side_effect=lambda name: failing_primary if name == "nvidia" else failing_fallback):
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True):
            with patch.object(settings, "LLM_FALLBACK_PROVIDER", "gemini"):
                with patch.object(settings, "LLM_MAX_RETRIES", 1):
                    req = LLMRequest(prompt="Test total provider failure")
                    with pytest.raises(RuntimeError) as exc_info:
                        await LLMService.generate(req, user_id="user_resilience_test", db=db_session, provider_name="nvidia")

                    err_msg = str(exc_info.value)
                    assert "Both primary 'nvidia' and fallback 'gemini' failed" in err_msg


@pytest.mark.asyncio
async def test_database_failure_resilience():
    """Verify that a DB persistence failure after successful generation does not crash the request or drop the response."""
    success_provider = MockSuccessProvider("nvidia", "Successful output despite DB error")
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.commit = AsyncMock(side_effect=Exception("Database lock error"))
    mock_db.rollback = AsyncMock()

    with patch.object(llm_provider_registry, "get_provider", return_value=success_provider):
        req = LLMRequest(prompt="DB failure resilience test")
        res = await LLMService.generate(req, user_id="user_db_test", db=mock_db, provider_name="nvidia")

        assert res.text == "Successful output despite DB error"
        assert res.provider == "nvidia"


@pytest.mark.asyncio
async def test_concurrency_load_safety():
    """Safe concurrency test verifying concurrent requests do not corrupt state, misroute providers, or leak data."""
    success_provider = MockSuccessProvider("nvidia", "Concurrent response OK")

    with patch.object(llm_provider_registry, "get_provider", return_value=success_provider):
        reqs = [LLMRequest(prompt=f"Concurrent prompt {i}") for i in range(10)]
        mock_dbs = [AsyncMock(spec=AsyncSession) for _ in range(10)]
        tasks = [LLMService.generate(r, user_id=f"user_conc_{i}", db=mock_dbs[i], provider_name="nvidia") for i, r in enumerate(reqs)]

        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        for r in results:
            assert r.provider == "nvidia"
            assert r.text == "Concurrent response OK"


@pytest.mark.asyncio
async def test_nvidia_provider_secret_redaction():
    """Verify that NvidiaProvider redacts API key from safe error messages."""
    provider = NvidiaProvider(api_key="nvapi-super-secret-token-xyz")
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized request with key nvapi-super-secret-token-xyz"
        mock_post.return_value = mock_resp

        req = LLMRequest(prompt="Test key redaction")
        with pytest.raises(RuntimeError) as exc_info:
            await provider.generate(req)

        err_text = str(exc_info.value)
        assert "nvapi-super-secret-token-xyz" not in err_text
        assert "[REDACTED_API_KEY]" in err_text
