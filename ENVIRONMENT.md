# FlowPilot AI - Environment Configuration Specification

This document details all required and optional environment variables for **FlowPilot AI**.

> [!CAUTION]
> **Zero Secrets Policy**: Never commit actual production passwords, API keys, or JWT secret keys to version control. Always use environment variable files (`.env.production`) managed via secret managers (e.g. AWS Secrets Manager, HashiCorp Vault, Doppler, or GitHub Secrets).

---

## 1. Environment Variable Reference Table

| Variable Name | Required | Default / Example Value | Description |
| :--- | :--- | :--- | :--- |
| **`ENVIRONMENT`** | Yes | `production` / `development` | Active application execution mode |
| **`PROJECT_NAME`** | Yes | `FlowPilot AI` | Application branding name |
| **`SECRET_KEY`** | Yes | `YOUR_SECURE_64_CHAR_HEX_SECRET_KEY` | Secret key used for session cookie signing & encryption |
| **`API_V1_STR`** | No | `/api/v1` | Root API route prefix |
| **`DATABASE_URL`** | Yes | `sqlite+aiosqlite:///./flowpilot.db` | Async DB connection URL |
| **`REDIS_URL`** | No | `redis://localhost:6379/0` | Redis event bus URL |
| **`CORS_ORIGINS`** | Yes | `["http://localhost:3000"]` | JSON array of permitted CORS client origin URLs |
| **`LLM_PROVIDER`** | Yes | `gemini` / `openai` / `ollama` | Active primary LLM provider |
| **`LLM_MODEL`** | Yes | `gemini-1.5-flash` / `gpt-4o` / `llama3` | Active primary model name |
| **`LLM_API_KEY`** | Conditional | `YOUR_SECURE_LLM_PROVIDER_API_KEY` | API Key for primary provider (Gemini, OpenAI) |
| **`LLM_BASE_URL`** | No | `http://localhost:11434` | Custom endpoint for Ollama or OpenAI-compatible hosts |
| **`LLM_TIMEOUT`** | No | `30.0` | HTTP request timeout in seconds |
| **`LLM_MAX_RETRIES`** | No | `3` | Maximum exponential backoff retry attempts |
| **`LLM_FALLBACK_ENABLED`** | No | `false` | Enable fallback provider on primary failure |
| **`LLM_FALLBACK_PROVIDER`** | No | `ollama` | Fallback provider adapter name |
| **`LLM_FALLBACK_MODEL`** | No | `llama3` | Fallback provider model name |

---

## 2. Production `.env.production` Example Template

```ini
# Application Configuration
ENVIRONMENT=production
PROJECT_NAME=FlowPilot AI
SECRET_KEY=e8b7c3d9a1f4e2b0c5d8e1f4a7b2c9d0e3f6a9b2c5d8e1f4a7b2c9d0e3f6a9b2
API_V1_STR=/api/v1

# Database & Cache Credentials
DATABASE_URL=postgresql+asyncpg://flowpilot_app:YOUR_PRODUCTION_DB_PASSWORD@localhost:5432/flowpilot_prod
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@localhost:6379/0

# Security & CORS Origins
CORS_ORIGINS=["https://app.flowpilot.ai"]

# LLM Gateway Configuration
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
LLM_API_KEY=YOUR_GEMINI_PRODUCTION_API_KEY
LLM_TIMEOUT=30.0
LLM_MAX_RETRIES=3
LLM_FALLBACK_ENABLED=true
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=llama3
```
