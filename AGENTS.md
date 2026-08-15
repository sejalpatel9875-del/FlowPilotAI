# FlowPilot AI — Production Multi-Agent Architecture (`AGENTS.md`)

FlowPilot AI implements a production **Multi-Agent Orchestrator** powered by 9 specialized agents, tenant-isolated context builders, NVIDIA Nemotron 3 Ultra synthesis, and strict security controls.

---

## 1. Available Specialized Agents

| Agent Name | Primary Purpose | Risk Level | Allowed Data Scopes |
| :--- | :--- | :--- | :--- |
| **LeadAgent** | Qualification, deal scoring, and opportunity ranking | **LOW** | `leads`, `companies`, `contacts`, `knowledge` |
| **ResearchAgent** | Competitor analysis & RAG knowledge extraction | **LOW** | `knowledge`, `research_docs` |
| **OutreachAgent** | Personalized outreach & email campaign drafting | **MEDIUM** | `leads`, `companies`, `outreach_messages` |
| **FollowUpAgent** | Follow-up sequence planning & cadence management | **MEDIUM** | `leads`, `follow_ups`, `sequences` |
| **ProposalAgent** | Scope of work, milestone, and pricing drafting | **MEDIUM** | `proposals`, `clients`, `leads`, `knowledge` |
| **ProjectAgent** | Project milestone breakdown & blocker detection | **LOW** | `projects`, `tasks` |
| **TimeManagementAgent** | Schedule optimization & focus block allocation | **LOW** | `tasks`, `time_blocks`, `preferences` |
| **LearningAgent** | Skill gap assessment & roadmap generation | **LOW** | `skills`, `goals`, `learning_plans`, `knowledge` |
| **AnalyticsAgent** | Business metrics & pipeline value summarization | **LOW** | `analytics`, `leads`, `projects` |

---

## 2. Agent Security Boundaries & Permission Policy

- **Strict Multi-Tenant Scoping**: All database queries and context builders filter strictly on `user_id == current_user.id`.
- **Prohibited Capabilities**:
  - No agent can access user passwords, session tokens, or API secrets.
  - No agent can execute arbitrary shell commands or external tools.
  - No agent can alter authentication or RBAC settings.
  - No agent can access or query another user's tenant data.
- **Untrusted RAG Data Wrapping**: Documents retrieved via RAG Knowledge search are explicitly tagged `[UNTRUSTED_KNOWLEDGE_DOCUMENTS]` so system policies remain strictly authoritative against prompt injection.

---

## 3. Orchestration Safety & Execution Limits

- **Maximum Recursion Depth**: 3 agents max per query workflow.
- **Maximum Execution Time**: 30 seconds execution timeout limit.
- **Maximum Agents Per Request**: 3 agents max per request to prevent infinite loops.
- **Human-in-the-Loop Approvals**: Medium/High risk actions (e.g. outreach sending) require explicit user approval before finalization.
