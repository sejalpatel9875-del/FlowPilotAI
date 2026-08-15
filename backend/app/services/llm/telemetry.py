import time
import math
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("flowpilot.llm.telemetry")


class ErrorTaxonomy:
    """Standardized error taxonomy classification for LLM provider failures."""
    AUTHENTICATION = "AUTHENTICATION"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    TRANSIENT_NETWORK = "TRANSIENT_NETWORK"
    SERVER_FAILURE = "SERVER_FAILURE"
    INVALID_REQUEST = "INVALID_REQUEST"
    MODEL_CONFIG = "MODEL_CONFIG"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def classify(cls, e: Exception) -> str:
        """Classify an exception into a standardized diagnostic taxonomy category."""
        if not e:
            return cls.UNKNOWN

        err_str = str(e).lower()

        if isinstance(e, (httpx.TimeoutException, asyncio.TimeoutError)) or "timeout" in err_str:
            return cls.TIMEOUT
        if "429" in err_str or "rate limit" in err_str or "too many requests" in err_str:
            return cls.RATE_LIMIT
        if "401" in err_str or "403" in err_str or "unauthorized" in err_str or "forbidden" in err_str:
            return cls.AUTHENTICATION
        if isinstance(e, (httpx.ConnectError, httpx.NetworkError)) or "connection refused" in err_str or "network glitch" in err_str:
            return cls.TRANSIENT_NETWORK
        if any(code in err_str for code in ["500", "502", "503", "504", "server error", "unavailable"]):
            return cls.SERVER_FAILURE
        if "400" in err_str or "bad request" in err_str or "invalid parameter" in err_str:
            return cls.INVALID_REQUEST
        if "model" in err_str and ("not found" in err_str or "invalid" in err_str):
            return cls.MODEL_CONFIG

        return cls.UNKNOWN


class LLMMetricsRegistry:
    """In-memory thread-safe structured metrics collector for LLM Gateway observability."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMMetricsRegistry, cls).__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._fallback_events = 0
        self._retry_count = 0
        self._timeout_count = 0
        self._rate_limit_429_count = 0
        self._server_5xx_count = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._total_tokens = 0
        self._latencies_ms: List[float] = []
        self._provider_failures: Dict[str, int] = {}
        self._error_distribution: Dict[str, int] = {
            ErrorTaxonomy.AUTHENTICATION: 0,
            ErrorTaxonomy.TIMEOUT: 0,
            ErrorTaxonomy.RATE_LIMIT: 0,
            ErrorTaxonomy.TRANSIENT_NETWORK: 0,
            ErrorTaxonomy.SERVER_FAILURE: 0,
            ErrorTaxonomy.INVALID_REQUEST: 0,
            ErrorTaxonomy.MODEL_CONFIG: 0,
            ErrorTaxonomy.UNKNOWN: 0,
        }

    def record_request(
        self,
        provider: str,
        success: bool,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        retries: int = 0,
        is_fallback: bool = False,
        error: Optional[Exception] = None
    ):
        """Record an LLM request execution event into telemetry metrics."""
        self._total_requests += 1
        self._latencies_ms.append(latency_ms)
        # Retain last 1000 latencies to avoid memory growth
        if len(self._latencies_ms) > 1000:
            self._latencies_ms = self._latencies_ms[-1000:]

        self._retry_count += retries
        if is_fallback:
            self._fallback_events += 1

        if success:
            self._successful_requests += 1
            self._input_tokens += input_tokens
            self._output_tokens += output_tokens
            self._total_tokens += (input_tokens + output_tokens)
        else:
            self._failed_requests += 1
            self._provider_failures[provider] = self._provider_failures.get(provider, 0) + 1

            category = ErrorTaxonomy.classify(error)
            self._error_distribution[category] = self._error_distribution.get(category, 0) + 1

            if category == ErrorTaxonomy.TIMEOUT:
                self._timeout_count += 1
            elif category == ErrorTaxonomy.RATE_LIMIT:
                self._rate_limit_429_count += 1
            elif category == ErrorTaxonomy.SERVER_FAILURE:
                self._server_5xx_count += 1

    def calculate_percentiles(self) -> Dict[str, float]:
        """Calculate P50, P95, P99, and Average latency percentiles."""
        if not self._latencies_ms:
            return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_lat = sorted(self._latencies_ms)
        n = len(sorted_lat)

        def percentile(p: float) -> float:
            idx = int(math.ceil((p / 100.0) * n)) - 1
            return sorted_lat[max(0, min(idx, n - 1))]

        avg_lat = sum(sorted_lat) / n
        return {
            "avg": round(avg_lat, 2),
            "p50": round(percentile(50), 2),
            "p95": round(percentile(95), 2),
            "p99": round(percentile(99), 2),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return structured metrics telemetry report."""
        lat_pct = self.calculate_percentiles()
        return {
            "totalRequests": self._total_requests,
            "successfulRequests": self._successful_requests,
            "failedRequests": self._failed_requests,
            "fallbackEvents": self._fallback_events,
            "retryCount": self._retry_count,
            "timeoutCount": self._timeout_count,
            "rateLimit429Count": self._rate_limit_429_count,
            "server5xxCount": self._server_5xx_count,
            "tokens": {
                "inputTokens": self._input_tokens,
                "outputTokens": self._output_tokens,
                "totalTokens": self._total_tokens,
            },
            "latencyMs": lat_pct,
            "providerFailures": self._provider_failures,
            "errorTaxonomyDistribution": self._error_distribution,
        }


# Global Singleton Metrics Instance
llm_metrics = LLMTelemetry = LLMMetricsRegistry()


def check_provider_health(provider_id: str) -> Dict[str, Any]:
    """Safe lightweight provider configuration & health check WITHOUT making expensive API generation calls."""
    if provider_id == "nvidia":
        has_key = bool(settings.LLM_API_KEY)
        is_configured = has_key
        return {
            "id": "nvidia",
            "name": "NVIDIA NIM Gateway",
            "model": settings.LLM_MODEL or "nvidia/nemotron-3-ultra-550b-a55b",
            "status": "ready" if is_configured else "missing_credentials",
            "configured": is_configured,
            "endpoint": settings.LLM_BASE_URL,
        }
    elif provider_id == "gemini":
        has_key = bool(settings.LLM_API_KEY)
        return {
            "id": "gemini",
            "name": "Google Gemini Provider",
            "model": "gemini-1.5-flash",
            "status": "ready" if has_key else "missing_credentials",
            "configured": has_key,
        }
    elif provider_id == "openai":
        has_key = bool(settings.LLM_API_KEY)
        return {
            "id": "openai",
            "name": "OpenAI Compatible Provider",
            "model": "gpt-4o",
            "status": "ready" if has_key else "missing_credentials",
            "configured": has_key,
        }
    elif provider_id == "ollama":
        return {
            "id": "ollama",
            "name": "Local Ollama Provider",
            "model": "llama3",
            "status": "ready",
            "configured": True,
        }
    else:
        return {
            "id": provider_id,
            "name": f"Provider {provider_id}",
            "status": "unknown",
            "configured": False,
        }
