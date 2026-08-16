"""
FlowPilot AI — Comprehensive Permanent Test Suite for Phase 8:
Autonomous Planning, Capability Registry, Agent Selection, Decision Engine & Controlled Replanning.
"""

import pytest
import uuid
import json
from httpx import AsyncClient

from app.services.workflow.capability_registry import CapabilityRegistry, AGENT_REGISTRY
from app.services.workflow.decision_engine import DecisionEngine, DecisionResult
from app.services.workflow.workflow_policy import (
    WorkflowPlanSpec,
    WorkflowStepSpec,
    WorkflowPolicyEngine,
    VALID_AGENT_NAMES,
)
from app.services.workflow.workflow_planner import WorkflowPlanner
from app.services.workflow.workflow_engine import WorkflowExecutionEngine
from app.models.lead import LeadModel


# ============================================================================
# 1. CAPABILITY REGISTRY TESTS
# ============================================================================

class TestCapabilityRegistry:
    """Verifies that all 12 specialized agents have explicit, machine-readable capability specs."""

    def test_registry_contains_exact_12_agents(self):
        assert len(AGENT_REGISTRY) == 12
        for agent_name in [
            "LeadAgent", "ResearchAgent", "OutreachAgent", "FollowUpAgent",
            "ProposalAgent", "ProjectAgent", "TimeManagementAgent", "LearningAgent",
            "AnalyticsAgent", "InvitationAgent", "LocationTracerAgent", "ReminderAgent"
        ]:
            assert CapabilityRegistry.is_agent_valid(agent_name)

    def test_agent_capabilities_and_inputs_outputs(self):
        lead_spec = CapabilityRegistry.get_agent_spec("LeadAgent")
        assert lead_spec is not None
        assert "analyze_leads" in lead_spec.capabilities
        assert "score_leads" in lead_spec.capabilities
        assert "lead_id" in lead_spec.outputs
        assert lead_spec.risk_level == "LOW"

    def test_side_effect_classification(self):
        # Read-only actions must NOT be classified as side effects
        assert not CapabilityRegistry.is_side_effect("LeadAgent", "analyze_leads")
        assert not CapabilityRegistry.is_side_effect("FollowUpAgent", "draft_followups")
        assert not CapabilityRegistry.is_side_effect("TimeManagementAgent", "recommend_timing")

        # External side-effect actions MUST be classified as side effects requiring approval
        assert CapabilityRegistry.is_side_effect("OutreachAgent", "send_outreach")
        assert CapabilityRegistry.is_side_effect("InvitationAgent", "send_invitation")
        assert CapabilityRegistry.is_side_effect("ReminderAgent", "dispatch_alert")

    def test_unknown_agent_rejection(self):
        assert not CapabilityRegistry.is_agent_valid("HackerAgent")
        assert not CapabilityRegistry.is_agent_valid("ArbitraryCodeRunner")

    def test_unknown_action_rejection(self):
        assert not CapabilityRegistry.is_action_valid("LeadAgent", "drop_database_tables")
        assert not CapabilityRegistry.is_action_valid("ResearchAgent", "execute_arbitrary_python")

    def test_resolve_candidate_agent(self):
        agent = CapabilityRegistry.resolve_candidate_agent("Please score my leads")
        assert agent == "LeadAgent"

        agent_fu = CapabilityRegistry.resolve_candidate_agent("Draft follow-up email")
        assert agent_fu == "FollowUpAgent"


# ============================================================================
# 2. DECISION ENGINE TESTS
# ============================================================================

class TestDecisionEngine:
    """Verifies that the Decision Engine evaluates agent outputs and decides correct transitions."""

    def test_decision_for_safe_lead_agent_output(self):
        output = {"output": "Identified 2 qualified leads: Acme Corp and Apex Systems."}
        result = DecisionEngine.evaluate_step_output(
            agent_name="LeadAgent",
            action="analyze_leads",
            output_data=output,
            is_terminal_step=False,
            is_side_effect=False
        )
        assert result.decision == "CONTINUE"
        assert "LeadAgent" in result.reason
        assert not result.requires_approval

    def test_decision_for_side_effect_requires_approval(self):
        output = {"output": "Outreach draft prepared."}
        result = DecisionEngine.evaluate_step_output(
            agent_name="OutreachAgent",
            action="send_outreach",
            output_data=output,
            is_terminal_step=True,
            is_side_effect=True
        )
        assert result.decision == "WAIT_FOR_APPROVAL"
        assert result.requires_approval

    def test_decision_for_agent_error_signals_failure(self):
        output = {"error": "LLM context exceeded"}
        result = DecisionEngine.evaluate_step_output(
            agent_name="ResearchAgent",
            action="research_market",
            output_data=output,
            is_terminal_step=False,
            is_side_effect=False
        )
        assert result.decision == "FAIL"
        assert "error" in result.reason.lower()

    def test_decision_for_terminal_step_completion(self):
        output = {"output": "All milestones and calendar slots successfully allocated."}
        result = DecisionEngine.evaluate_step_output(
            agent_name="TimeManagementAgent",
            action="recommend_timing",
            output_data=output,
            is_terminal_step=True,
            is_side_effect=False
        )
        assert result.decision == "COMPLETE"

    def test_replan_viability_bounded(self):
        assert DecisionEngine.evaluate_replan_viability(0, max_replans=3)
        assert DecisionEngine.evaluate_replan_viability(1, max_replans=3)
        assert DecisionEngine.evaluate_replan_viability(2, max_replans=3)
        assert not DecisionEngine.evaluate_replan_viability(3, max_replans=3)
        assert not DecisionEngine.evaluate_replan_viability(4, max_replans=3)


# ============================================================================
# 3. POLICY & VALIDATION NEGATIVE TESTS
# ============================================================================

class TestPolicyAndValidationNegatives:
    """Verifies that invalid, cyclical, or unauthorized plans are strictly rejected."""

    def test_reject_unknown_agent_in_plan(self):
        plan = WorkflowPlanSpec(
            goal="Test unknown agent",
            steps=[WorkflowStepSpec(id="s1", agent="UnauthorizedAgent", action="analyze_leads")]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert not res["valid"]
        assert "Invalid agent 'UnauthorizedAgent'" in res["error"]

    def test_reject_unsupported_action_in_plan(self):
        plan = WorkflowPlanSpec(
            goal="Test unauthorized action",
            steps=[WorkflowStepSpec(id="s1", agent="LeadAgent", action="execute_arbitrary_shell")]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert not res["valid"]
        assert "not supported by agent" in res["error"]

    def test_reject_circular_dependency_dag(self):
        plan = WorkflowPlanSpec(
            goal="Test circular plan",
            steps=[
                WorkflowStepSpec(id="s1", agent="LeadAgent", action="analyze_leads", depends_on=["s2"]),
                WorkflowStepSpec(id="s2", agent="FollowUpAgent", action="draft_followups", depends_on=["s1"]),
            ]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert not res["valid"]
        assert "Circular dependency" in res["error"]

    def test_reject_self_dependency(self):
        plan = WorkflowPlanSpec(
            goal="Test self dependency",
            steps=[WorkflowStepSpec(id="s1", agent="LeadAgent", action="analyze_leads", depends_on=["s1"])]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert not res["valid"]
        assert "cannot depend on itself" in res["error"]

    def test_auto_flag_side_effect_action(self):
        plan = WorkflowPlanSpec(
            goal="Test side effect auto flagging",
            steps=[WorkflowStepSpec(id="s1", agent="OutreachAgent", action="send_outreach", requires_approval=False)]
        )
        res = WorkflowPolicyEngine.validate_plan(plan)
        assert res["valid"]
        # Must be auto-promoted to requires_approval = True
        assert plan.steps[0].requires_approval is True


# ============================================================================
# 4. GOLDEN PATH AUTONOMOUS WORKFLOW E2E TEST
# ============================================================================

class TestAutonomousWorkflowGoldenPath:
    """Verifies the complete Golden Path multi-agent workflow end-to-end."""

    @pytest.fixture
    async def auth_session(self, async_client: AsyncClient):
        email = f"golden_user_{uuid.uuid4().hex[:8]}@flowpilot.ai"
        pwd = "Password123!"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "fullName": "Golden Path User"})
        login = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        return {"Authorization": f"Bearer {login.cookies['flowpilot_session']}"}

    @pytest.mark.asyncio
    async def test_complete_golden_path_scenario(self, async_client: AsyncClient, auth_session: dict):
        """
        Scenario:
        User says: 'Analyze my pending leads, identify high-priority leads, create personalized follow-up drafts,
        recommend suitable timing, and show me the proposed actions for approval.'
        """
        # 1. Seed two test leads for the user
        lead_a = await async_client.post(
            "/api/v1/leads",
            json={
                "name": "Sarah Jenkins",
                "company": "Horizon Cloud Labs",
                "email": "sarah.j@horizoncloud.io",
                "status": "Qualified",
                "serviceFit": "High",
                "value": 15000.0,
                "notes": "Interested in AI automation pipeline."
            },
            headers=auth_session
        )
        assert lead_a.status_code in (200, 201)

        # 2. Initiate autonomous multi-agent workflow
        user_goal = "Analyze my pending leads, identify high-priority leads, create personalized follow-up drafts, recommend suitable timing, and show me the proposed actions for approval."
        wf_res = await async_client.post("/api/v1/workflows", json={"goal": user_goal}, headers=auth_session)
        assert wf_res.status_code == 201
        wf_data = wf_res.json()
        wf_id = wf_data["id"]

        # 3. State machine must pause at WAITING_FOR_APPROVAL
        detail_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=auth_session)
        assert detail_res.status_code == 200
        wf = detail_res.json()

        assert wf["status"] == "WAITING_FOR_APPROVAL"
        assert len(wf["pendingApprovals"]) == 1
        approval_id = wf["pendingApprovals"][0]["id"]

        # Verify steps executed in sequence
        steps = wf["steps"]
        assert len(steps) == 4
        assert steps[0]["agent"] == "LeadAgent" and steps[0]["status"] == "COMPLETED"
        assert steps[1]["agent"] == "FollowUpAgent" and steps[1]["status"] == "COMPLETED"
        assert steps[2]["agent"] == "TimeManagementAgent" and steps[2]["status"] == "COMPLETED"
        assert steps[3]["agent"] == "OutreachAgent" and steps[3]["status"] == "WAITING_FOR_APPROVAL"

        # 4. User grants approval via Human Approval Center
        appr_res = await async_client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            json={"approvalId": approval_id, "decision": "approved", "reason": "Drafts and timing verified by Sales Director."},
            headers=auth_session
        )
        assert appr_res.status_code == 200

        # 5. Workflow resumes and completes
        final_res = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=auth_session)
        final_wf = final_res.json()
        assert final_wf["status"] == "COMPLETED"
        assert final_wf["completedSteps"] == 4

        # 6. Verify immutable audit trail contains DECISION_CREATED and APPROVAL_APPROVED events
        events_res = await async_client.get(f"/api/v1/workflows/{wf_id}/events", headers=auth_session)
        assert events_res.status_code == 200
        event_types = [ev["eventType"] for ev in events_res.json()["events"]]

        assert "WORKFLOW_CREATED" in event_types
        assert "PLAN_VALIDATED" in event_types
        assert "DECISION_CREATED" in event_types
        assert "APPROVAL_REQUESTED" in event_types
        assert "APPROVAL_APPROVED" in event_types
        assert "WORKFLOW_COMPLETED" in event_types


# ============================================================================
# 5. MULTI-TENANT & IDEMPOTENCY SECURITY TESTS
# ============================================================================

class TestWorkflowSecurityAndIdempotency:
    """Verifies that cross-tenant access is blocked and duplicate approvals are idempotent."""

    @pytest.mark.asyncio
    async def test_cross_tenant_approval_blocked(self, async_client: AsyncClient):
        # Register User A & create workflow with pending approval
        email_a = f"usera_appr_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_a, "password": "Password123!", "fullName": "User A"})
        login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
        headers_a = {"Authorization": f"Bearer {login_a.cookies['flowpilot_session']}"}

        wf_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Analyze leads and send outreach"},
            headers=headers_a
        )
        wf_id = wf_res.json()["id"]
        detail_a = (await async_client.get(f"/api/v1/workflows/{wf_id}", headers=headers_a)).json()
        approval_id = detail_a["pendingApprovals"][0]["id"]

        # Register User B
        email_b = f"userb_intruder_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email_b, "password": "Password123!", "fullName": "User B"})
        login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
        headers_b = {"Authorization": f"Bearer {login_b.cookies['flowpilot_session']}"}

        # User B attempts to approve User A's workflow
        intruder_res = await async_client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            json={"approvalId": approval_id, "decision": "approved"},
            headers=headers_b
        )
        assert intruder_res.status_code in (400, 404)

    @pytest.mark.asyncio
    async def test_duplicate_approval_is_idempotent(self, async_client: AsyncClient):
        email = f"idempotent_user_{uuid.uuid4().hex[:6]}@flowpilot.ai"
        await async_client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "fullName": "Idempotent User"})
        login = await async_client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        headers = {"Authorization": f"Bearer {login.cookies['flowpilot_session']}"}

        wf_res = await async_client.post(
            "/api/v1/workflows",
            json={"goal": "Analyze leads and draft followups with outreach"},
            headers=headers
        )
        wf_id = wf_res.json()["id"]
        detail = (await async_client.get(f"/api/v1/workflows/{wf_id}", headers=headers)).json()
        approval_id = detail["pendingApprovals"][0]["id"]

        # First approval
        appr_1 = await async_client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            json={"approvalId": approval_id, "decision": "approved"},
            headers=headers
        )
        assert appr_1.status_code == 200

        # Second identical approval must not crash or re-execute side effect
        appr_2 = await async_client.post(
            f"/api/v1/workflows/{wf_id}/approve",
            json={"approvalId": approval_id, "decision": "approved"},
            headers=headers
        )
        assert appr_2.status_code == 200
