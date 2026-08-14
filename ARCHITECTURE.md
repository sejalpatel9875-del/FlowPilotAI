# FlowPilot AI - System Architecture & Engineering Specifications

FlowPilot AI is an AI-powered Freelancing, Growth, Productivity, and Learning Operating System built on a provider-independent LLM Gateway, multi-agent framework, RAG Knowledge Vault, Model Context Protocol (MCP) tool ecosystem, and autonomous workflow engine.

---

## 1. High-Level System Architecture

```
                                  ┌────────────────────────┐
                                  │   Next.js 14 Web UI    │
                                  │ (App Router / Vanilla) │
                                  └───────────┬────────────┘
                                              │ REST / JSON (HTTP-Only Sessions)
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend Gateway                                                                │
│                                                                                        │
│ ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────────────────┐ │
│ │ Security & Auth      │  │ LLM Gateway Service  │  │ Agent Framework                │ │
│ │ (Argon2id / OWASP)   │  │ (Gemini/OpenAI/Ollama│  │ (10 Specialist Agents)         │ │
│ └──────────────────────┘  └──────────────────────┘  └────────────────────────────────┘ │
└─────────────┬──────────────────────────┬───────────────────────────────┬───────────────┘
              │                          │                               │
              ▼                          ▼                               ▼
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│ PostgreSQL 15 Database    │ │ Redis 7 Cache & Bus       │ │ RAG Knowledge Vault       │
│ (35+ Tables / Async ORM)  │ │ (Sliding Window Limits)   │ │ (Vector Chunks / Search)  │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

---

## 2. Production LLM Gateway Architecture

FlowPilot AI abstracts AI vendor dependencies behind a unified provider gateway (`LLMService`):

- **Supported Adapters**:
  - `GeminiProvider`: Google Gemini 1.5 Flash / Pro REST API adapter.
  - `OpenAIProvider`: OpenAI GPT-4o / Compatible REST API adapter.
  - `OllamaProvider`: Local Ollama Llama 3 REST API adapter.
- **Resilience Controls**:
  - Exponential backoff retry loops (`LLM_MAX_RETRIES`).
  - Provider timeout enforcement (`LLM_TIMEOUT`).
  - Automatic fallback failover (`LLM_FALLBACK_ENABLED`).
- **Telemetry & Safety**:
  - Sensitive data filtering before LLM dispatch.
  - Structured JSON schema output validation.
  - SQL token usage logging in `ai_gateway_requests`.

---

## 3. Multi-Agent Framework (10 Specialized Agents)

FlowPilot AI delegates specialized responsibilities across 10 autonomous agents governed by an Orchestrator:

| Agent Name | Primary Responsibility | Permission Scope |
| :--- | :--- | :--- |
| **OrchestratorAgent** | Command Center routing, multi-agent task execution, recommendation ranking | Full System Read / Task Routing |
| **LeadGenAgent** | Lead discovery, prospect scoring, qualification, enrichment | Leads Database Write |
| **OutreachAgent** | High-converting cold pitch generation, A/B testing variations | Outreach Inbox (Draft Only) |
| **FollowUpAgent** | Automatic multi-touch follow-up sequence generation | Follow-Up Engine Write |
| **ProposalAgent** | Interactive scope, milestone breakdown, and proposal creation | Proposal Draft Write |
| **ClientSuccessAgent**| Onboarding task generation, project status tracking | Project & Client Database Write |
| **TimeManagementAgent**| Daily time budgeting, calendar blocking, schedule optimization | TimeBlocks Database Write |
| **LearningAgent** | AI skill roadmap generation, spaced repetition quiz scheduling | Learning Database Write |
| **CommandCenterAgent** | Real-time action ranking (Urgency, Impact, Revenue, Learning, Effort) | Command Center Data Read |
| **SecurityGuardAgent**| Prompt injection scanning, sensitive data masking, MCP governance | Security Filter Scope |

---

## 4. Automation Engine 7-Stage Workflow Pipeline

All autonomous workflows follow a 7-stage deterministic execution pipeline:

```
┌─────────┐   ┌───────────┐   ┌─────────────┐   ┌────────┐   ┌──────────┐   ┌───────────┐   ┌───────┐
│ TRIGGER │──>│ CONDITION │──>│ AI DECISION │──>│ ACTION │──>│ APPROVAL │──>│ EXECUTION │──>│ AUDIT │
└─────────┘   └───────────┘   └─────────────┘   └────────┘   └──────────┘   └───────────┘   └───────┘
```

---

## 5. Primary Database Schema (SQLAlchemy 2.0 Async ORM)

The PostgreSQL schema consists of 35+ relational tables:
- **Users & Auth**: `users`, `sessions`, `user_preferences`.
- **LLM Gateway**: `ai_gateway_requests`, `ai_requests`, `ai_usage`.
- **CRM & Outreach**: `leads`, `outreach_messages`, `follow_up_sequences`, `follow_ups`.
- **Clients & Projects**: `clients`, `projects`, `proposals`, `deliverables`.
- **Time & Learning**: `time_blocks`, `study_sessions`, `skills`, `curriculums`.
- **Agents & Automations**: `agent_activities`, `automations`, `automation_runs`, `mcp_tools`.
- **Knowledge & Audit**: `documents`, `document_chunks`, `security_events`, `audit_logs`.
