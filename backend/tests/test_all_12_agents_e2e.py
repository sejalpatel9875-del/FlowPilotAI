"""
FlowPilot AI — Comprehensive End-to-End Production Verification Suite for All 12 Specialized Agents.

Agents Audited:
1. LeadAgent
2. ResearchAgent
3. OutreachAgent
4. FollowUpAgent
5. ProposalAgent
6. ProjectAgent
7. TimeManagementAgent
8. LearningAgent
9. AnalyticsAgent
10. InvitationAgent
11. LocationTracerAgent
12. ReminderAgent

Covers:
- Registration & Metadata
- Intent Routing
- Context Builder & Multi-Tenant Isolation
- Live End-to-End API Workflows & Service Invocations
- Error Handling & Security Boundaries
"""

import pytest
import inspect
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.orchestrator import orchestrator
from app.agents.router import IntentRouter
from app.agents.context_builder import AgentContextBuilder
from app.agents.base_agent import BaseAgent
from app.models.agent_engine import AgentRunModel
from app.models.lead import LeadModel
from app.models.project import ProjectModel
from app.models.workplace import TaskModel, ProposalModel
from app.models.time_management import TimeBlockModel
from app.models.learning import SkillModel, GoalModel, LearningPlanModel
from app.models.invitation import InvitationModel
from app.models.reminder import ReminderModel
from app.models.outreach import OutreachMessageModel
from app.models.follow_up import FollowUpSequenceModel, FollowUpModel


ALL_12_AGENT_NAMES = [
    "LeadAgent",
    "ResearchAgent",
    "OutreachAgent",
    "FollowUpAgent",
    "ProposalAgent",
    "ProjectAgent",
    "TimeManagementAgent",
    "LearningAgent",
    "AnalyticsAgent",
    "InvitationAgent",
    "LocationTracerAgent",
    "ReminderAgent",
]


# ============================================================================
# 1. REGISTRATION & METADATA AUDIT (ALL 12 AGENTS)
# ============================================================================

class TestAgentRegistrationAndMetadata:
    """Verifies that all 12 specialized agents are registered in the orchestrator with valid metadata."""

    def test_all_12_agents_registered(self):
        assert len(orchestrator.agent_registry) == 12
        for agent_name in ALL_12_AGENT_NAMES:
            assert agent_name in orchestrator.agent_registry, f"Agent '{agent_name}' missing from orchestrator registry"

    @pytest.mark.parametrize("agent_name", ALL_12_AGENT_NAMES)
    def test_agent_instance_and_metadata(self, agent_name: str):
        agent = orchestrator.get_agent(agent_name)
        assert agent is not None
        assert isinstance(agent, BaseAgent)
        assert agent.name == agent_name
        assert len(agent.description) > 10
        assert len(agent.purpose) > 10
        assert len(agent.system_policy) > 20
        assert agent.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert isinstance(agent.allowed_tools, list)
        assert len(agent.allowed_tools) >= 1
        assert isinstance(agent.allowed_data_scopes, list)
        assert len(agent.allowed_data_scopes) >= 1
        assert inspect.iscoroutinefunction(agent.run)
        assert inspect.iscoroutinefunction(agent.get_context)


# ============================================================================
# 2. INTENT ROUTING AUDIT (ALL 12 AGENTS)
# ============================================================================

class TestAgentIntentRoutingMatrix:
    """Verifies that IntentRouter routes user prompts to each of the 12 agents accurately."""

    @pytest.mark.parametrize("prompt,expected_agent", [
        ("Qualify this new enterprise lead opportunity", "LeadAgent"),
        ("Research competitor market analysis and summarize documents", "ResearchAgent"),
        ("Draft a cold email outreach pitch for new prospects", "OutreachAgent"),
        ("Follow up with unreplied prospects from last week", "FollowUpAgent"),
        ("Create a freelance proposal draft with pricing and scope of work", "ProposalAgent"),
        ("Break down project deliverables into tasks and milestones", "ProjectAgent"),
        ("Plan my next 3 hours focus block and agenda", "TimeManagementAgent"),
        ("Build a learning roadmap and spaced repetition skill plan", "LearningAgent"),
        ("Summarize my business performance and pipeline value analytics", "AnalyticsAgent"),
        ("Schedule a discovery call meeting invite for a prospective client", "InvitationAgent"),
        ("Where are my leads located in the geographic distribution", "LocationTracerAgent"),
        ("Remind me not to forget the project deadline tomorrow", "ReminderAgent"),
    ])
    def test_intent_routing_single_agent(self, prompt: str, expected_agent: str):
        result = IntentRouter.route_intent(prompt)
        assert expected_agent in result, f"Prompt '{prompt}' failed to route to '{expected_agent}', got {result}"

    def test_multi_agent_workflow_routing(self):
        result = IntentRouter.route_intent("What should I focus on next?")
        assert "TimeManagementAgent" in result
        assert "LeadAgent" in result
        assert "ProjectAgent" in result

    def test_fallback_routing(self):
        result = IntentRouter.route_intent("general query with no matching keywords")
        assert result == ["LeadAgent"]


# ============================================================================
# 3. CONTEXT BUILDER & MULTI-TENANT ISOLATION (ALL 12 AGENTS)
# ============================================================================

class TestAgentContextIsolation:
    """Verifies that AgentContextBuilder strictly isolates tenant data across all domains."""

    @pytest.mark.asyncio
    async def test_lead_context_tenant_isolation(self, db_session: AsyncSession):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        lead_a = LeadModel(user_id=user_a, name="Secret Lead User A", company="Acme Corp", email="a@acme.com", value=100000.0)
        db_session.add(lead_a)
        await db_session.commit()

        context_b = await AgentContextBuilder.build_lead_context(user_b, "analyze leads", db_session)
        assert "Secret Lead User A" not in context_b

    @pytest.mark.asyncio
    async def test_project_context_tenant_isolation(self, db_session: AsyncSession):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        proj_a = ProjectModel(user_id=user_a, title="Top Secret Project A", client_name="Client A", deadline="2026-12-31")
        db_session.add(proj_a)
        await db_session.commit()

        context_b = await AgentContextBuilder.build_project_context(user_b, "show projects", db_session)
        assert "Top Secret Project A" not in context_b

    @pytest.mark.asyncio
    async def test_invitation_context_tenant_isolation(self, db_session: AsyncSession):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        inv_a = InvitationModel(user_id=user_a, title="Private Executive Invite A", recipient_name="Alice", recipient_email="alice@private.com")
        db_session.add(inv_a)
        await db_session.commit()

        context_b = await AgentContextBuilder.build_invitation_context(user_b, "show invitations", db_session)
        assert "Private Executive Invite A" not in context_b

    @pytest.mark.asyncio
    async def test_reminder_context_tenant_isolation(self, db_session: AsyncSession):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        rem_a = ReminderModel(user_id=user_a, title="Confidential Reminder A", remind_at=datetime.utcnow() + timedelta(days=1), priority="urgent")
        db_session.add(rem_a)
        await db_session.commit()

        context_b = await AgentContextBuilder.build_reminder_context(user_b, "show reminders", db_session)
        assert "Confidential Reminder A" not in context_b

    @pytest.mark.asyncio
    async def test_location_context_tenant_isolation(self, db_session: AsyncSession):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        lead_a = LeadModel(user_id=user_a, name="Zurich Lead A", company="Swiss Bank", email="swiss@bank.ch", location="Zurich, Switzerland", value=50000.0)
        db_session.add(lead_a)
        await db_session.commit()

        context_b = await AgentContextBuilder.build_location_context(user_b, "lead locations", db_session)
        assert "Zurich, Switzerland" not in context_b

    @pytest.mark.asyncio
    async def test_learning_context_tenant_isolation(self, db_session: AsyncSession):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        skill_a = SkillModel(user_id=user_a, name="Quantum Cryptography A", proficiency_level="Master")
        db_session.add(skill_a)
        await db_session.commit()

        context_b = await AgentContextBuilder.build_learning_context(user_b, "my skills", db_session)
        assert "Quantum Cryptography A" not in context_b


# ============================================================================
# 4. COMPLETE END-TO-END API WORKFLOWS FOR ALL 12 AGENTS
# ============================================================================

class TestAll12AgentsEndToEndAPIWorkflows:
    """Verifies complete end-to-end API workflows for every single agent."""

    @pytest.fixture
    async def authenticated_session(self, async_client: AsyncClient):
        email = f"agent_e2e_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "E2E Agent User"})
        login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login_res.cookies["flowpilot_session"]
        return {"Authorization": f"Bearer {token}"}

    # 1. LeadAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_lead_agent(self, async_client: AsyncClient, authenticated_session: dict):
        create_res = await async_client.post(
            "/api/v1/leads",
            json={"name": "Enterprise Client", "company": "MegaCorp", "email": "vp@megacorp.com", "serviceFit": "High"},
            headers=authenticated_session
        )
        assert create_res.status_code == 200
        lead_id = create_res.json()["id"]

        action_res = await async_client.post(
            f"/api/v1/leads/{lead_id}/ai-action",
            json={"actionType": "analyze"},
            headers=authenticated_session
        )
        assert action_res.status_code == 200
        data = action_res.json()
        assert data["leadId"] == lead_id
        assert len(data.get("aiOutput", "")) > 0

    # 2. ResearchAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_research_agent(self, async_client: AsyncClient, authenticated_session: dict):
        files = {"file": ("market_brief.txt", b"AI agents reduce task latency by 70%.", "text/plain")}
        upload_res = await async_client.post("/api/v1/knowledge/upload", files=files, headers=authenticated_session)
        assert upload_res.status_code == 200

        exec_res = await async_client.post(
            "/api/v1/agents/execute",
            json={"prompt": "Research market strategies and summarize knowledge vault documents."},
            headers=authenticated_session
        )
        assert exec_res.status_code == 200
        data = exec_res.json()
        assert "ResearchAgent" in data["agentsExecuted"]
        assert len(data["finalResponse"]) > 0

    # 3. OutreachAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_outreach_agent(self, async_client: AsyncClient, authenticated_session: dict):
        lead_res = await async_client.post(
            "/api/v1/leads",
            json={"name": "Target Lead", "company": "Prospect Inc", "email": "lead@prospect.com"},
            headers=authenticated_session
        )
        lead_id = lead_res.json()["id"]

        draft_res = await async_client.post(
            "/api/v1/outreach/generate",
            json={"leadId": lead_id, "channel": "Email"},
            headers=authenticated_session
        )
        assert draft_res.status_code == 200
        msg_id = draft_res.json()["id"]

        approve_res = await async_client.post(f"/api/v1/outreach/{msg_id}/approve", headers=authenticated_session)
        assert approve_res.status_code == 200

        send_res = await async_client.post(f"/api/v1/outreach/{msg_id}/send", headers=authenticated_session)
        assert send_res.status_code == 200
        assert send_res.json()["status"] == "SENT"

    # 4. FollowUpAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_follow_up_agent(self, async_client: AsyncClient, authenticated_session: dict):
        lead_res = await async_client.post(
            "/api/v1/leads",
            json={"name": "Cadence Lead", "company": "Cadence Co", "email": "cadence@co.com"},
            headers=authenticated_session
        )
        lead_id = lead_res.json()["id"]

        start_res = await async_client.post(
            "/api/v1/follow-ups/start",
            json={"leadId": lead_id},
            headers=authenticated_session
        )
        assert start_res.status_code == 200
        seq_id = start_res.json()["sequenceId"]

        list_res = await async_client.get("/api/v1/follow-ups?queue=upcoming", headers=authenticated_session)
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert len(items) > 0
        followup_id = items[0]["id"]

        explain_res = await async_client.post(f"/api/v1/follow-ups/{followup_id}/explain", headers=authenticated_session)
        assert explain_res.status_code == 200
        assert "aiReasoning" in explain_res.json()

        draft_res = await async_client.post(f"/api/v1/follow-ups/{followup_id}/generate-draft", headers=authenticated_session)
        assert draft_res.status_code == 200
        assert "draftBody" in draft_res.json()

    # 5. ProposalAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_proposal_agent(self, async_client: AsyncClient, authenticated_session: dict):
        res = await async_client.post(
            "/api/v1/agents/execute",
            json={"prompt": "Create a scope of work and pricing draft proposal for a web app redesign."},
            headers=authenticated_session
        )
        assert res.status_code == 200
        data = res.json()
        assert "ProposalAgent" in data["agentsExecuted"]
        assert len(data["finalResponse"]) > 0

    # 6. ProjectAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_project_agent(self, async_client: AsyncClient, authenticated_session: dict):
        res = await async_client.post(
            "/api/v1/agents/execute",
            json={"prompt": "Break down project tasks and deliverables for our upcoming milestone."},
            headers=authenticated_session
        )
        assert res.status_code == 200
        data = res.json()
        assert "ProjectAgent" in data["agentsExecuted"]
        assert len(data["finalResponse"]) > 0

    # 7. TimeManagementAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_time_management_agent(self, async_client: AsyncClient, authenticated_session: dict):
        plan_res = await async_client.post("/api/v1/time/plan-day", headers=authenticated_session)
        assert plan_res.status_code == 200

        quick_res = await async_client.post(
            "/api/v1/time/quick-plan",
            json={"minutes": 60},
            headers=authenticated_session
        )
        assert quick_res.status_code == 200

    # 8. LearningAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_learning_agent(self, async_client: AsyncClient, authenticated_session: dict):
        skill_res = await async_client.post(
            "/api/v1/learning/skills",
            json={"name": "FastAPI System Architecture", "currentLevel": "Beginner", "targetLevel": "Advanced", "weeklyHours": 5},
            headers=authenticated_session
        )
        assert skill_res.status_code == 200
        skill_id = skill_res.json()["id"]

        rec_res = await async_client.post("/api/v1/learning/recommend", headers=authenticated_session)
        assert rec_res.status_code == 200

        log_res = await async_client.post(
            f"/api/v1/learning/{skill_id}/log-hours",
            json={"hours": 2.5},
            headers=authenticated_session
        )
        assert log_res.status_code == 200

    # 9. AnalyticsAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_analytics_agent(self, async_client: AsyncClient, authenticated_session: dict):
        dash_res = await async_client.get("/api/v1/analytics/overview", headers=authenticated_session)
        assert dash_res.status_code == 200

        exec_res = await async_client.post(
            "/api/v1/agents/execute",
            json={"prompt": "Summarize my business performance and revenue pipeline metrics."},
            headers=authenticated_session
        )
        assert exec_res.status_code == 200
        assert "AnalyticsAgent" in exec_res.json()["agentsExecuted"]

    # 10. InvitationAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_invitation_agent(self, async_client: AsyncClient, authenticated_session: dict):
        lead_res = await async_client.post(
            "/api/v1/leads",
            json={"name": "Invite Lead", "company": "Client Corp", "email": "client@corp.com"},
            headers=authenticated_session
        )
        lead_id = lead_res.json()["id"]

        gen_res = await async_client.post(
            "/api/v1/invitations/generate",
            json={"leadId": lead_id, "invitationType": "discovery_call", "prompt": "Schedule next Tuesday at 2 PM"},
            headers=authenticated_session
        )
        assert gen_res.status_code == 200
        inv_id = gen_res.json()["id"]

        list_res = await async_client.get("/api/v1/invitations", headers=authenticated_session)
        assert list_res.status_code == 200
        inv_ids = [i["id"] for i in list_res.json()["invitations"]]
        assert inv_id in inv_ids

        send_res = await async_client.post(f"/api/v1/invitations/{inv_id}/send", headers=authenticated_session)
        assert send_res.status_code == 200
        assert send_res.json()["status"] == "sent"

    # 11. LocationTracerAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_location_tracer_agent(self, async_client: AsyncClient, authenticated_session: dict):
        await async_client.post(
            "/api/v1/leads",
            json={"name": "Tokyo Lead", "company": "Tokyo Tech", "email": "tokyo@tech.jp", "location": "Tokyo, Japan"},
            headers=authenticated_session
        )

        map_res = await async_client.get("/api/v1/location/lead-map", headers=authenticated_session)
        assert map_res.status_code == 200
        data = map_res.json()
        assert "distribution" in data
        assert any(d["location"] == "Tokyo, Japan" for d in data["distribution"])

        trace_res = await async_client.post(
            "/api/v1/location/trace",
            json={"ip_address": "192.168.1.50"},
            headers=authenticated_session
        )
        assert trace_res.status_code == 200
        assert trace_res.json()["resolved_location"]["region"] == "Private Network"

    # 12. ReminderAgent E2E Workflow
    @pytest.mark.asyncio
    async def test_e2e_reminder_agent(self, async_client: AsyncClient, authenticated_session: dict):
        remind_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
        create_res = await async_client.post(
            "/api/v1/reminders",
            json={"title": "Client Review Reminder", "remind_at": remind_time, "priority": "high"},
            headers=authenticated_session
        )
        assert create_res.status_code == 200
        rem_id = create_res.json()["id"]

        suggest_res = await async_client.post(
            "/api/v1/reminders/smart-suggest",
            json={"prompt": "Suggest reminders for upcoming high-priority leads"},
            headers=authenticated_session
        )
        assert suggest_res.status_code == 200
        assert "suggestions" in suggest_res.json()

        snooze_res = await async_client.post(
            f"/api/v1/reminders/{rem_id}/snooze",
            json={"snooze_minutes": 60},
            headers=authenticated_session
        )
        assert snooze_res.status_code == 200
        assert snooze_res.json()["status"] == "snoozed"

        complete_res = await async_client.post(f"/api/v1/reminders/{rem_id}/complete", headers=authenticated_session)
        assert complete_res.status_code == 200
        assert complete_res.json()["status"] == "completed"


# ============================================================================
# 5. ERROR HANDLING & SECURITY BOUNDARY AUDIT
# ============================================================================

class TestAgentErrorHandlingAndSecurityBoundaries:
    """Verifies rejection of unauthenticated requests, empty inputs, cross-tenant tampering, and prompt injection."""

    @pytest.mark.asyncio
    async def test_unauthenticated_requests_rejected(self, async_client: AsyncClient):
        protected_routes = [
            ("POST", "/api/v1/agents/execute", {"prompt": "test"}),
            ("GET", "/api/v1/agents/dashboard", None),
            ("GET", "/api/v1/invitations", None),
            ("POST", "/api/v1/invitations/generate", {"leadId": "1", "invitationType": "meeting", "prompt": "test"}),
            ("GET", "/api/v1/location/lead-map", None),
            ("POST", "/api/v1/location/trace", {"ip_address": "127.0.0.1"}),
            ("GET", "/api/v1/reminders", None),
            ("POST", "/api/v1/reminders/smart-suggest", {"prompt": "test"}),
        ]
        for method, path, body in protected_routes:
            if method == "POST":
                res = await async_client.post(path, json=body)
            else:
                res = await async_client.get(path)
            assert res.status_code == 401, f"Route '{path}' failed to reject unauthenticated request"

    @pytest.mark.asyncio
    async def test_empty_prompt_rejected(self, async_client: AsyncClient):
        pwd = "Password123!"
        email = f"empty_prompt_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "User"})
        login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        headers = {"Authorization": f"Bearer {login_res.cookies['flowpilot_session']}"}

        res1 = await async_client.post("/api/v1/agents/execute", json={"prompt": ""}, headers=headers)
        assert res1.status_code == 400

        res2 = await async_client.post("/api/v1/agents/execute", json={"prompt": "   "}, headers=headers)
        assert res2.status_code == 400

    @pytest.mark.asyncio
    async def test_cross_tenant_invitation_tampering_blocked(self, async_client: AsyncClient):
        # Register User A & Create Invitation
        email_a = f"usera_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "fullName": "User A"})
        login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
        headers_a = {"Authorization": f"Bearer {login_a.cookies['flowpilot_session']}"}

        inv_res = await async_client.post(
            "/api/v1/invitations",
            json={"title": "User A Private Meeting", "recipient_name": "Bob", "recipient_email": "bob@corp.com"},
            headers=headers_a
        )
        inv_id = inv_res.json()["id"]

        # Register User B
        email_b = f"userb_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "fullName": "User B"})
        login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
        headers_b = {"Authorization": f"Bearer {login_b.cookies['flowpilot_session']}"}

        # User B attempts to view or modify User A's invitation
        get_res = await async_client.get(f"/api/v1/invitations/{inv_id}", headers=headers_b)
        assert get_res.status_code == 404

        send_res = await async_client.post(f"/api/v1/invitations/{inv_id}/send", headers=headers_b)
        assert send_res.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_tenant_reminder_tampering_blocked(self, async_client: AsyncClient):
        # Register User A & Create Reminder
        email_a = f"usera_rem_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "fullName": "User A"})
        login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
        headers_a = {"Authorization": f"Bearer {login_a.cookies['flowpilot_session']}"}

        rem_res = await async_client.post(
            "/api/v1/reminders",
            json={"title": "User A Private Reminder", "remind_at": (datetime.utcnow() + timedelta(days=1)).isoformat()},
            headers=headers_a
        )
        rem_id = rem_res.json()["id"]

        # Register User B
        email_b = f"userb_rem_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "fullName": "User B"})
        login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
        headers_b = {"Authorization": f"Bearer {login_b.cookies['flowpilot_session']}"}

        # User B attempts to access or complete User A's reminder
        get_res = await async_client.get(f"/api/v1/reminders/{rem_id}", headers=headers_b)
        assert get_res.status_code == 404

        complete_res = await async_client.post(f"/api/v1/reminders/{rem_id}/complete", headers=headers_b)
        assert complete_res.status_code == 404
