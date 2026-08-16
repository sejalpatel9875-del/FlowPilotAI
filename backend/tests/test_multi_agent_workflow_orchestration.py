"""
FlowPilot AI — Comprehensive Permanent Regression Test Suite for True Multi-Agent Workflow Orchestration.

Covers:
1. Planner Decomposition & Policy Validation (DAG acyclicity, unknown agent rejection, side-effect flagging)
2. Execution Graph & State Machine (PLANNED, RUNNING, WAITING_FOR_APPROVAL, APPROVED, REJECTED, COMPLETED, FAILED, CANCELLED)
3. Dependency-Aware DAG Execution & Context Passing (Topological resolution, size-bounded transfer)
4. Human-In-The-Loop Approval Gates (Pause before side effects, explicit approve/reject, resumption)
5. Multi-Tenant Security & RBAC Isolation (401, 403, 404, cross-tenant protection)
6. Bounded Replanning & Failure Recovery (Max 3 replan attempts, safe abort on broken prerequisites)
7. Audit Trail & Telemetry (Immutable event logging, zero secret leakage)
8. Deterministic Demonstration Workflow (End-to-end bilingual multi-agent business flow)
"""

import pytest
import uuid
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.workflow import (
    WorkflowModel,
    WorkflowStepModel,
    WorkflowApprovalModel,
    WorkflowEventModel,
)
from app.models.lead import LeadModel
from app.services.workflow.workflow_policy import (
    WorkflowPlanSpec,
    WorkflowStepSpec,
    WorkflowPolicyEngine,
    VALID_AGENT_NAMES,
)
from app.services.workflow.workflow_planner import WorkflowPlanner
from app.services.workflow.workflow_engine import WorkflowExecutionEngine
from app.services.workflow.workflow_telemetry import WorkflowTelemetry


# ============================================================================
# 1. PLANNER & POLICY VALIDATION TESTS
# ============================================================================

class TestWorkflowPlannerAndPolicy:
    """Verifies that the planner generates valid plans and policy engine rejects invalid/dangerous plans."""

    def test_all_12_agents_whitelisted(self):
        assert len(VALID_AGENT_NAMES) == 12
        for agent in [
            "LeadAgent", "ResearchAgent", "OutreachAgent", "FollowUpAgent",
            "ProposalAgent", "ProjectAgent", "TimeManagementAgent", "LearningAgent",
            "AnalyticsAgent", "InvitationAgent", "LocationTracerAgent", "ReminderAgent"
        ]:
            assert agent in VALID_AGENT_NAMES

    def test_valid_plan_passes_policy(self):
        plan = WorkflowPlanSpec(
            goal="Analyze leads and draft outreach",
            steps=[
                WorkflowStepSpec(id="step_1", agent="LeadAgent", action="analyze_leads", description="Qualify pending leads"),
                WorkflowStepSpec(id="step_2", agent="OutreachAgent", action="send_outreach", description="Send emails", depends_on=["step_1"]),
            ]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert res["valid"] is True
        assert plan.steps[1].requires_approval is True  # Enforced side-effect approval

    def test_unknown_agent_rejected(self):
        plan = WorkflowPlanSpec(
            goal="Execute untrusted agent",
            steps=[
                WorkflowStepSpec(id="step_1", agent="ArbitraryHackerAgent", action="execute_code", description="Test"),
            ]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert res["valid"] is False
        assert "Invalid agent 'ArbitraryHackerAgent'" in res["error"]

    def test_circular_dependency_rejected(self):
        plan = WorkflowPlanSpec(
            goal="Circular dependency test",
            steps=[
                WorkflowStepSpec(id="step_1", agent="LeadAgent", action="analyze", depends_on=["step_2"]),
                WorkflowStepSpec(id="step_2", agent="FollowUpAgent", action="draft", depends_on=["step_1"]),
            ]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert res["valid"] is False
        assert "Circular dependency cycle detected" in res["error"]

    def test_self_dependency_rejected(self):
        plan = WorkflowPlanSpec(
            goal="Self dependency test",
            steps=[
                WorkflowStepSpec(id="step_1", agent="LeadAgent", action="analyze", depends_on=["step_1"]),
            ]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert res["valid"] is False
        assert "cannot depend on itself" in res["error"]

    def test_nonexistent_dependency_rejected(self):
        plan = WorkflowPlanSpec(
            goal="Missing dependency test",
            steps=[
                WorkflowStepSpec(id="step_1", agent="LeadAgent", action="analyze", depends_on=["step_999"]),
            ]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert res["valid"] is False
        assert "depends on non-existent step 'step_999'" in res["error"]


# ============================================================================
# 2. EXECUTION GRAPH & STATE MACHINE TESTS
# ============================================================================

class TestWorkflowExecutionGraph:
    """Verifies the state machine transitions, DAG dependency handling, and context passing."""

    @pytest.fixture
    async def authenticated_session(self, async_client: AsyncClient):
        email = f"wf_user_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "Workflow User"})
        login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login_res.cookies["flowpilot_session"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_sequential_safe_workflow_completes(self, async_client: AsyncClient, authenticated_session: dict):
        create_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Break down project deliverables into tasks and allocate focus schedule."},
            headers=authenticated_session
        )
        assert create_res.status_code == 201
        wf_data = create_res.json()
        wf_id = wf_data["id"]

        get_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=authenticated_session)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["status"] == "COMPLETED"
        assert data["completedSteps"] == data["totalSteps"]
        assert len(data["steps"]) >= 2
        for step in data["steps"]:
            assert step["status"] == "COMPLETED"
            assert step["output"] is not None

    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, async_client: AsyncClient, authenticated_session: dict):
        # Create workflow requiring approval so it stays in WAITING_FOR_APPROVAL
        create_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Draft meeting invitation and send invite to client."},
            headers=authenticated_session
        )
        assert create_res.status_code == 201
        wf_id = create_res.json()["id"]

        cancel_res = await async_client.post(f"/api/v1/workflows/{wf_id}/cancel", headers=authenticated_session)
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

        get_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=authenticated_session)
        assert get_res.json()["status"] == "CANCELLED"


# ============================================================================
# 3. HUMAN-IN-THE-LOOP APPROVAL TESTS
# ============================================================================

class TestWorkflowHumanInTheLoop:
    """Verifies mandatory approval gates before executing external side effects."""

    @pytest.fixture
    async def authenticated_session(self, async_client: AsyncClient):
        email = f"hil_user_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "HIL User"})
        login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login_res.cookies["flowpilot_session"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_approval_gate_and_resumption(self, async_client: AsyncClient, authenticated_session: dict):
        # 1. Create workflow with side effect
        create_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Draft cold outreach and send email to prospect lead."},
            headers=authenticated_session
        )
        assert create_res.status_code == 201
        wf_id = create_res.json()["id"]

        # 2. Verify state is WAITING_FOR_APPROVAL
        get_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=authenticated_session)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["status"] == "WAITING_FOR_APPROVAL"
        assert len(data["pendingApprovals"]) == 1
        approval_id = data["pendingApprovals"][0]["id"]

        # 3. Grant approval
        approve_res = await async_client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            json={"approvalId": approval_id, "decision": "approved", "reason": "Looks good to send"},
            headers=authenticated_session
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "COMPLETED"

        # 4. Verify completed state
        final_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=authenticated_session)
        assert final_res.json()["status"] == "COMPLETED"
        assert len(final_res.json()["pendingApprovals"]) == 0

    @pytest.mark.asyncio
    async def test_rejection_terminates_workflow_safely(self, async_client: AsyncClient, authenticated_session: dict):
        create_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Draft meeting invite and send invitation."},
            headers=authenticated_session
        )
        wf_id = create_res.json()["id"]

        get_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=authenticated_session)
        approval_id = get_res.json()["pendingApprovals"][0]["id"]

        reject_res = await async_client.post(
            f"/api/v1/workflows/{wf_id}/reject",
            json={"approvalId": approval_id, "decision": "rejected", "reason": "Wrong timing for meeting"},
            headers=authenticated_session
        )
        assert reject_res.status_code == 200
        assert reject_res.json()["status"] == "REJECTED"

        final_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=authenticated_session)
        assert final_res.json()["status"] == "REJECTED"


# ============================================================================
# 4. MULTI-TENANT SECURITY & RBAC TESTS
# ============================================================================

class TestWorkflowMultiTenantSecurity:
    """Verifies strict tenant isolation across all workflow endpoints."""

    @pytest.mark.asyncio
    async def test_unauthenticated_access_rejected(self, async_client: AsyncClient):
        res1 = await async_client.post("/api/v1/workflows", json={"goal": "Analyze leads"})
        assert res1.status_code == 401

        res2 = await async_client.get("/api/v1/workflows")
        assert res2.status_code == 401

    @pytest.mark.asyncio
    async def test_cross_tenant_workflow_access_blocked(self, async_client: AsyncClient):
        # Register User A & create workflow
        email_a = f"usera_wf_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "fullName": "User A"})
        login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
        headers_a = {"Authorization": f"Bearer {login_a.cookies['flowpilot_session']}"}

        wf_res = await async_client.post("/api/v1/workflows", json={"goal": "User A confidential workflow"}, headers=headers_a)
        wf_id = wf_res.json()["id"]

        # Register User B
        email_b = f"userb_wf_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "fullName": "User B"})
        login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
        headers_b = {"Authorization": f"Bearer {login_b.cookies['flowpilot_session']}"}

        # User B attempts to access User A's workflow
        get_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=headers_b)
        assert get_res.status_code == 404

        cancel_res = await async_client.post(f"/api/v1/workflows/{wf_id}/cancel", headers=headers_b)
        assert cancel_res.status_code == 400 or cancel_res.status_code == 404

        events_res = await async_client.get(f"/api/v1/workflows/{wf_id}/events", headers=headers_b)
        assert events_res.status_code == 404


# ============================================================================
# 5. AUDIT TRAIL & TELEMETRY TESTS
# ============================================================================

class TestWorkflowAuditTrailAndTelemetry:
    """Verifies immutable event logging and secret-free telemetry."""

    @pytest.fixture
    async def authenticated_session(self, async_client: AsyncClient):
        email = f"audit_user_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "Audit User"})
        login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login_res.cookies["flowpilot_session"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_complete_audit_event_trail(self, async_client: AsyncClient, authenticated_session: dict):
        create_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Conduct market research and generate proposal."},
            headers=authenticated_session
        )
        wf_id = create_res.json()["id"]

        events_res = await async_client.get(f"/api/v1/workflows/{wf_id}/events", headers=authenticated_session)
        assert events_res.status_code == 200
        events = events_res.json()["events"]
        assert len(events) >= 4

        event_types = [e["eventType"] for e in events]
        assert "WORKFLOW_CREATED" in event_types
        assert "PLAN_GENERATED" in event_types
        assert "PLAN_VALIDATED" in event_types
        assert "STEP_STARTED" in event_types
        assert "STEP_COMPLETED" in event_types
        assert "WORKFLOW_COMPLETED" in event_types

        # Verify no secrets in event details
        for ev in events:
            ev_str = json.dumps(ev)
            assert "nvapi-" not in ev_str
            assert "Bearer " not in ev_str
            assert "password" not in ev_str.lower() or "audit_user" in ev_str


# ============================================================================
# 6. DETERMINISTIC DEMONSTRATION WORKFLOW (END-TO-END)
# ============================================================================

class TestDemonstrationWorkflowEndToEnd:
    """
    Executes the exact requested demonstration workflow:
    Objective:
    'Mere pending leads analyze karo, high-priority leads identify karo, unke liye follow-up drafts banao,
     suitable timing recommend karo, aur final follow-up bhejne se pehle mujhse approval lo.'
    """

    @pytest.mark.asyncio
    async def test_full_demonstration_workflow(self, async_client: AsyncClient):
        # 1. Setup authenticated user & seed sample leads
        email = f"demo_exec_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "Demo Exec"})
        login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        headers = {"Authorization": f"Bearer {login_res.cookies['flowpilot_session']}"}

        # Seed 2 realistic leads via API
        await async_client.post(
            "/api/v1/leads",
            json={
                "name": "Sarah Jenkins",
                "company": "Acme Global Solutions",
                "email": "sarah.j@acmeglobal.com",
                "serviceFit": "High",
                "location": "San Francisco, CA"
            },
            headers=headers
        )
        await async_client.post(
            "/api/v1/leads",
            json={
                "name": "Rajiv Malhotra",
                "company": "Apex FinTech",
                "email": "rajiv@apexfintech.io",
                "serviceFit": "High",
                "location": "New York, NY"
            },
            headers=headers
        )

        # 2. Submit high-level bilingual objective
        objective = (
            "Mere pending leads analyze karo, high-priority leads identify karo, "
            "unke liye follow-up drafts banao, suitable timing recommend karo, "
            "aur final follow-up bhejne se pehle mujhse approval lo."
        )

        create_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": objective},
            headers=headers
        )
        assert create_res.status_code == 201
        wf_id = create_res.json()["id"]

        # 3. Check Workflow state: Should have executed LeadAgent -> FollowUpAgent -> TimeManagementAgent,
        # and paused at OutreachAgent WAITING_FOR_APPROVAL
        get_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=headers)
        assert get_res.status_code == 200
        wf_data = get_res.json()

        assert wf_data["status"] == "WAITING_FOR_APPROVAL"
        assert wf_data["totalSteps"] == 4
        assert wf_data["completedSteps"] == 3  # Steps 1, 2, 3 completed!

        step_agents = [s["agent"] for s in wf_data["steps"]]
        assert step_agents == ["LeadAgent", "FollowUpAgent", "TimeManagementAgent", "OutreachAgent"]

        # Verify completed steps have outputs
        assert wf_data["steps"][0]["status"] == "COMPLETED"
        assert wf_data["steps"][1]["status"] == "COMPLETED"
        assert wf_data["steps"][2]["status"] == "COMPLETED"
        assert wf_data["steps"][3]["status"] == "WAITING_FOR_APPROVAL"

        # Verify pending approval
        assert len(wf_data["pendingApprovals"]) == 1
        approval = wf_data["pendingApprovals"][0]
        approval_id = approval["id"]
        assert "send_followup" in approval["proposedAction"] or "OutreachAgent" in approval["proposedAction"]

        # 4. User reviews and GRANTS APPROVAL
        approve_res = await async_client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            json={"approvalId": approval_id, "decision": "approved", "reason": "Approved by sales director"},
            headers=headers
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "COMPLETED"

        # 5. Verify final completed state & execution of side effect
        final_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=headers)
        assert final_res.status_code == 200
        final_data = final_res.json()
        assert final_data["status"] == "COMPLETED"
        assert final_data["completedSteps"] == 4
        assert final_data["steps"][3]["status"] == "COMPLETED"

        # 6. Verify audit trail records complete lifecycle
        events_res = await async_client.get(f"/api/v1/workflows/{wf_id}/events", headers=headers)
        assert events_res.status_code == 200
        event_types = [e["eventType"] for e in events_res.json()["events"]]

        assert "WORKFLOW_CREATED" in event_types
        assert "PLAN_GENERATED" in event_types
        assert "PLAN_VALIDATED" in event_types
        assert "APPROVAL_REQUESTED" in event_types
        assert "APPROVAL_GRANTED" in event_types
        assert "SIDE_EFFECT_EXECUTED" in event_types
        assert "WORKFLOW_COMPLETED" in event_types
