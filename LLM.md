# FlowPilot AI — Production LLM Gateway Specification

## 1. Overview & Architecture

FlowPilot AI implements a provider-independent, multi-tenant LLM Gateway (`LLMService`). Application code calls `LLMService` rather than directly binding to vendor SDKs.

```
Frontend (AI Playground / Command Center / Agents)
       ↓
API Layer (/api/v1/ai/generate, /stream, /structured, /usage)
       ↓
LLMService (Sanitization, Validation, Retries, Failover)
       ↓
LLMProviderRegistry
 ├── GeminiProvider (Google Gemini API)
 ├── OpenAIProvider (OpenAI / Compatible API)
 └── OllamaProvider (Local Ollama API)
       ↓
AIRequestModel (SQL Usage Tracking & Audit Metrics)
```

---

## 2. Configuration Settings

| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_PROVIDER` | `str` | `gemini` | Primary LLM adapter (`gemini`, `openai`, `ollama`) |
| `LLM_MODEL` | `str` | `gemini-1.5-flash` | Primary model identifier |
| `LLM_API_KEY` | `Optional[str]` | `None` | Vendor API key (redacted from logs) |
| `LLM_BASE_URL` | `Optional[str]` | `None` | Base URL for OpenAI or Ollama endpoints |
| `LLM_TIMEOUT` | `float` | `30.0` | HTTP request timeout |
| `LLM_MAX_RETRIES` | `int` | `3` | Maximum backoff retry attempts |
| `LLM_FALLBACK_ENABLED` | `bool` | `False` | Enable automatic provider failover |
| `LLM_FALLBACK_PROVIDER` | `Optional[str]` | `ollama` | Fallback adapter name |
| `LLM_FALLBACK_MODEL` | `Optional[str]` | `llama3` | Fallback model name |

---

## 3. Request Pipeline & Security Controls

Every AI request follows a 9-stage pipeline:
1. **Authentication**: User authenticated via HTTP-Only session token (`get_current_user`).
2. **Authorization**: Tenant isolation check enforced.
3. **Input Sanitization**: Sensitive data filter redacts passwords, session tokens, and API keys.
4. **Prompt Injection Protection**: Heuristic injection detection scans prompt text.
5. **Context Construction**: Tenant-isolated data builder gathers user's own tasks, leads, and projects.
6. **Provider Dispatch**: `LLMService` dispatches request to `LLMProviderRegistry`.
7. **Exponential Backoff Retries**: Up to `LLM_MAX_RETRIES` attempts before triggering fallback adapter.
8. **Output Validation**: Redacts sensitive info from output text and validates JSON schemas for structured requests.
9. **Usage Tracking**: Logs token consumption (`input_tokens`, `output_tokens`, `total_tokens`), latency (`latency_ms`), and status in `ai_gateway_requests` SQL table.

---

## 4. Privacy & Fallback Behavior

- Raw API keys and passwords are **never logged** or stored in database tables.
- Automatic fallback provider failover occurs **only when explicitly enabled** via `LLM_FALLBACK_ENABLED=true`.
- System prompts and hidden reasoning/chain-of-thought are not returned in API responses.
