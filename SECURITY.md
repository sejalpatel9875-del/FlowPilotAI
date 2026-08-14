# FlowPilot AI - Security Architecture & Policy

> [!IMPORTANT]
> **Operational Security Disclaimer**: FlowPilot AI implements strict, empirical, and measurable security controls across all architectural layers. However, **no system is 100% secure**. Maintaining strong security posture requires continuous monitoring, regular dependency security updates, operational access controls, threat modeling, and proactive security testing.

---

## 1. Security Architecture & Controls Overview

FlowPilot AI establishes measurable security boundaries across 7 primary security domains:

```
[ Inbound HTTP Request ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ OWASP Security Headers Middleware                      │
│ (X-Frame-Options: DENY, X-Content-Type-Options, HSTS)  │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Sliding Window Rate Limiter (Redis)                    │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Argon2id Auth & Session Validation                     │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Multi-Tenant User Isolation & Role-Based Authorization │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ AI Safety & Prompt Injection Detector                  │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Human Approval Gatekeeper & MCP Permission Checks      │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│ Output Redaction Filter (API Key & Secret Masker)      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Measurable Security Domain Matrix

| Security Domain | Implemented Controls | Enforcement Point |
| :--- | :--- | :--- |
| **Authentication** | Argon2id password hashing, HTTP-Only `SameSite=Lax` cookies, immediate session invalidation on logout | `auth_service.py` |
| **Authorization & RBAC** | Role hierarchy (`ADMIN`, `DEVELOPER`, `USER`, `VIEWER`), strict row-level `user_id == current_user.id` scoping | `dependencies.py` & DB queries |
| **API & Gateway Security** | OWASP Security Headers (`nosniff`, `DENY`, `STS`), strict CORS origins list, masked internal error tracebacks | `security_middleware.py` |
| **Rate Limiting** | Sliding window Redis rate limiter (100 req/min/IP), fail-safe fallback | `rate_limiter.py` |
| **File Upload Security** | Mandatory file extension allowlist (`.pdf`, `.txt`, `.md`, `.json`, `.csv`), max 10MB payload size limit | Endpoint validation |
| **AI Safety & Guards** | `PromptInjectionDetector` pattern scanner, CoT reasoning chain masking, system prompt shielding | `security_guard_service.py` |
| **MCP Risk Governance** | Per-tool risk level classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), mandatory human approval for external actions | `mcp/execution_engine.py` |
| **Audit Logging** | 100% audit logging of security events, login attempts, role changes, and high-risk tool executions | `AuditLogModel` SQL table |

---

## 3. AI Security & Safeguards

### Prompt Injection Detection (`PromptInjectionDetector`)
All user prompts, un-trusted RAG document chunks, and agent instructions pass through regex and semantic vulnerability scanners to intercept attack vectors:
- System prompt extraction attempts ("reveal system prompt", "show hidden instructions")
- Directive override attacks ("ignore all previous instructions", "disregard prior directives")
- Safety filter bypasses ("jailbreak mode", "DAN mode")

### Sensitive Data Filtering (`SensitiveDataFilter`)
Outbound agent context, prompt strings, and API response objects are automatically redacted to prevent secret exposure:
- API Keys: OpenAI (`sk-proj-...`), GitHub (`ghp_...`), Anthropic (`sk-ant-...`)
- Passwords & Tokens: Passwords, Bearer JWT tokens, SSH Private Keys, DB connection URLs

---

## 4. MCP Risk Classification & Approval Boundaries

Every Model Context Protocol (MCP) tool registered in FlowPilot AI is classified by risk:

| Risk Level | Impact | Tool Examples | Approval Boundary |
| :--- | :--- | :--- | :--- |
| **LOW** | Read-only queries | `knowledge_search`, `lead_search`, `analytics_query` | Autonomous execution permitted |
| **MEDIUM** | Internal state edits | `task_creation`, `reminder_set`, `proposal_create` | Autonomous execution permitted |
| **HIGH** | External communications | `email_send`, `slack_post` | **REQUIRES HUMAN APPROVAL** |
| **CRITICAL** | Database deletion / Credentials | `database_delete`, `credential_access` | **REQUIRES EXPLICIT ADMIN CONFIRMATION** |

---

## 5. Security Vulnerability Disclosure Policy

We take system security seriously. If you discover a vulnerability or security flaw in FlowPilot AI, please submit a responsible disclosure report:

- **Security Email**: `security@flowpilot.ai`
- **GPG Key Fingerprint**: `9F8E 4D2A 1C7B 3E5F 6A8B 9C0D`
- **Response SLA**: Initial triage within 24 hours; patch updates within 7 days for High/Critical issues.

*Please do NOT create public GitHub issues for undisclosed security vulnerabilities.*
