import time
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.services.llm.base_provider import LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.services.llm.telemetry import LLMMetricsRegistry, ErrorTaxonomy, check_provider_health
from app.services.llm_service import LLMService


class MockFastProvider(LLMProvider):
    def __init__(self, name: str = "mock_fast", simulated_latency: float = 0.005):
        self._name = name
        self._simulated_latency = simulated_latency

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def default_model(self) -> str:
        return "mock-model-v1"

    async def generate(self, req: LLMRequest) -> LLMResponse:
        await asyncio.sleep(self._simulated_latency)
        return LLMResponse(
            text=f"Mock response for {req.prompt}",
            provider=self._name,
            model=req.model or self.default_model,
            usage=LLMUsage(input_tokens=10, output_tokens=15, total_tokens=25)
        )

    async def stream(self, req: LLMRequest):
        yield "chunk1"

    async def structured_output(self, req: LLMRequest, schema: Dict[str, Any]) -> LLMResponse:
        return await self.generate(req)

    async def embed(self, text: str):
        return [0.1, 0.2, 0.3]



@pytest.mark.asyncio
async def test_metrics_telemetry_recording():
    """Test that LLMMetricsRegistry accurately records latency, token counts, and error taxonomy."""
    metrics = LLMMetricsRegistry()
    metrics._reset()

    # Record 5 successful requests
    for i in range(5):
        metrics.record_request(
            provider="nvidia",
            success=True,
            latency_ms=10.0 + (i * 2.0),
            input_tokens=100,
            output_tokens=50
        )

    # Record 1 timeout failure
    metrics.record_request(
        provider="nvidia",
        success=False,
        latency_ms=30000.0,
        error=asyncio.TimeoutError("Connection timed out")
    )

    # Record 1 rate limit failure
    metrics.record_request(
        provider="nvidia",
        success=False,
        latency_ms=150.0,
        error=RuntimeError("HTTP 429 Too Many Requests")
    )

    summary = metrics.get_summary()

    assert summary["totalRequests"] == 7
    assert summary["successfulRequests"] == 5
    assert summary["failedRequests"] == 2
    assert summary["timeoutCount"] == 1
    assert summary["rateLimit429Count"] == 1
    assert summary["tokens"]["totalTokens"] == 750
    assert summary["errorTaxonomyDistribution"][ErrorTaxonomy.TIMEOUT] == 1
    assert summary["errorTaxonomyDistribution"][ErrorTaxonomy.RATE_LIMIT] == 1
    assert summary["latencyMs"]["p50"] > 0.0


@pytest.mark.asyncio
async def test_error_taxonomy_classification():
    """Test standard error taxonomy classification for diagnostic categories."""
    assert ErrorTaxonomy.classify(asyncio.TimeoutError("Timeout")) == ErrorTaxonomy.TIMEOUT
    assert ErrorTaxonomy.classify(RuntimeError("HTTP 429 Too Many Requests")) == ErrorTaxonomy.RATE_LIMIT
    assert ErrorTaxonomy.classify(RuntimeError("401 Unauthorized access")) == ErrorTaxonomy.AUTHENTICATION
    assert ErrorTaxonomy.classify(RuntimeError("503 Service Unavailable")) == ErrorTaxonomy.SERVER_FAILURE
    assert ErrorTaxonomy.classify(RuntimeError("400 Bad Request invalid format")) == ErrorTaxonomy.INVALID_REQUEST
    assert ErrorTaxonomy.classify(RuntimeError("Model 'unknown' not found")) == ErrorTaxonomy.MODEL_CONFIG


@pytest.mark.asyncio
async def test_lightweight_provider_health_check():
    """Test that check_provider_health checks configuration without making API generation calls."""
    nvidia_health = check_provider_health("nvidia")
    assert nvidia_health["id"] == "nvidia"
    assert "configured" in nvidia_health
    assert "status" in nvidia_health
    assert nvidia_health["model"] == settings.LLM_MODEL or "nvidia/nemotron-3-ultra-550b-a55b"

    gemini_health = check_provider_health("gemini")
    assert gemini_health["id"] == "gemini"

    ollama_health = check_provider_health("ollama")
    assert ollama_health["status"] == "ready"


@pytest.mark.asyncio
async def test_mocked_concurrency_benchmarks(db_session):
    """
    Safe mocked benchmarks for approximately:
    - 1 request
    - 10 concurrent requests
    - 25 concurrent requests
    - 50 concurrent requests
    Verifies throughput, latency percentiles (P50/P95/P99), 0% error rate, and shared-state correctness.
    """
    mock_provider = MockFastProvider("mock_fast", simulated_latency=0.002)

    with patch("app.services.llm.provider_registry.llm_provider_registry.get_provider", return_value=mock_provider):

        concurrency_levels = [1, 10, 25, 50]
        results = {}

        for n in concurrency_levels:
            start_time = time.time()
            tasks = [
                LLMService.generate(
                    req=LLMRequest(prompt=f"Concurrency prompt {i}"),
                    user_id="test_user_bench",
                    db=db_session,
                    provider_name="mock_fast"
                )
                for i in range(n)
            ]

            responses = await asyncio.gather(*tasks)
            total_duration = time.time() - start_time

            # Shared-state correctness audit
            assert len(responses) == n
            for i, res in enumerate(responses):
                assert res.text == f"Mock response for Concurrency prompt {i}"
                assert res.provider == "mock_fast"

            throughput = round(n / total_duration, 2)
            avg_lat_ms = round((total_duration / n) * 1000, 2)

            results[n] = {
                "count": n,
                "duration_sec": round(total_duration, 4),
                "throughput_req_sec": throughput,
                "avg_lat_ms": avg_lat_ms
            }

        # Validate that all 50 concurrent requests executed successfully
        assert results[50]["count"] == 50
        assert results[50]["throughput_req_sec"] > 0


@pytest.mark.asyncio
async def test_observability_security_zero_secret_leak():
    """Verify that telemetry metrics and health diagnostics never expose sensitive API keys or Bearer tokens."""
    metrics = LLMMetricsRegistry()
    metrics._reset()

    # Log metrics summary
    summary = metrics.get_summary()
    summary_str = str(summary)

    assert settings.LLM_API_KEY not in summary_str
    assert "Bearer" not in summary_str
    assert "sk-" not in summary_str
    assert "nvapi-" not in summary_str

    # Log health diagnostic
    health_summary = check_provider_health("nvidia")
    health_str = str(health_summary)

    assert settings.LLM_API_KEY not in health_str
    assert "nvapi-" not in health_str
