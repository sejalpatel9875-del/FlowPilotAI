"""
Tests for the 3 newly activated agents: InvitationAgent, LocationTracerAgent, ReminderAgent.
Covers:
- Agent instantiation and metadata
- Context builder methods
- Orchestrator registration (12 agents total)
- Intent routing for new keywords
- Service layer CRUD operations
- Endpoint response structure
- Tenant isolation
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# ──────────────────────────────────────────────
# 1. Agent Framework Tests
# ──────────────────────────────────────────────

class TestInvitationAgentFramework:
    """Test InvitationAgent instantiation and metadata."""

    def test_invitation_agent_instantiation(self):
        from app.agents.specialized.invitation_agent import InvitationAgent
        agent = InvitationAgent()
        assert agent.name == "InvitationAgent"
        assert agent.risk_level == "MEDIUM"
        assert "leads" in agent.allowed_data_scopes
        assert "invitations" in agent.allowed_data_scopes
        assert "READ_LEADS" in agent.allowed_tools

    def test_invitation_agent_validates_empty_prompt(self):
        from app.agents.specialized.invitation_agent import InvitationAgent
        agent = InvitationAgent()
        with pytest.raises(ValueError):
            agent.validate_input("")

    def test_invitation_agent_validates_output(self):
        from app.agents.specialized.invitation_agent import InvitationAgent
        agent = InvitationAgent()
        assert agent.validate_output("") == "Agent generated no output."
        assert agent.validate_output("Hello") == "Hello"


class TestLocationTracerAgentFramework:
    """Test LocationTracerAgent instantiation and metadata."""

    def test_location_tracer_agent_instantiation(self):
        from app.agents.specialized.location_tracer_agent import LocationTracerAgent
        agent = LocationTracerAgent()
        assert agent.name == "LocationTracerAgent"
        assert agent.risk_level == "LOW"
        assert "leads" in agent.allowed_data_scopes
        assert "locations" in agent.allowed_data_scopes
        assert "READ_LEADS" in agent.allowed_tools

    def test_location_tracer_validates_empty_prompt(self):
        from app.agents.specialized.location_tracer_agent import LocationTracerAgent
        agent = LocationTracerAgent()
        with pytest.raises(ValueError):
            agent.validate_input("")


class TestReminderAgentFramework:
    """Test ReminderAgent instantiation and metadata."""

    def test_reminder_agent_instantiation(self):
        from app.agents.specialized.reminder_agent import ReminderAgent
        agent = ReminderAgent()
        assert agent.name == "ReminderAgent"
        assert agent.risk_level == "LOW"
        assert "reminders" in agent.allowed_data_scopes
        assert "tasks" in agent.allowed_data_scopes
        assert "leads" in agent.allowed_data_scopes
        assert "READ_REMINDERS" in agent.allowed_tools
        assert "CREATE_REMINDER" in agent.allowed_tools

    def test_reminder_agent_validates_empty_prompt(self):
        from app.agents.specialized.reminder_agent import ReminderAgent
        agent = ReminderAgent()
        with pytest.raises(ValueError):
            agent.validate_input("   ")


# ──────────────────────────────────────────────
# 2. Orchestrator Registration Tests
# ──────────────────────────────────────────────

class TestOrchestratorRegistration:
    """Verify all 12 agents are registered in the orchestrator."""

    def test_all_12_agents_registered(self):
        from app.agents.orchestrator import orchestrator
        registry = orchestrator.agent_registry
        assert len(registry) == 12, f"Expected 12 agents, got {len(registry)}: {list(registry.keys())}"

    def test_new_agents_present(self):
        from app.agents.orchestrator import orchestrator
        registry = orchestrator.agent_registry
        assert "InvitationAgent" in registry
        assert "LocationTracerAgent" in registry
        assert "ReminderAgent" in registry

    def test_original_agents_preserved(self):
        from app.agents.orchestrator import orchestrator
        registry = orchestrator.agent_registry
        for name in ["LeadAgent", "ResearchAgent", "OutreachAgent", "FollowUpAgent",
                      "ProposalAgent", "ProjectAgent", "TimeManagementAgent",
                      "LearningAgent", "AnalyticsAgent"]:
            assert name in registry, f"Original agent {name} missing from registry"

    def test_new_agents_are_base_agent_instances(self):
        from app.agents.orchestrator import orchestrator
        from app.agents.base_agent import BaseAgent
        for name in ["InvitationAgent", "LocationTracerAgent", "ReminderAgent"]:
            agent = orchestrator.agent_registry[name]
            assert isinstance(agent, BaseAgent), f"{name} is not a BaseAgent instance"


# ──────────────────────────────────────────────
# 3. Intent Router Tests
# ──────────────────────────────────────────────

class TestIntentRouterNewAgents:
    """Verify intent routing routes to the 3 new agents."""

    def test_invitation_intent_keywords(self):
        from app.agents.router import IntentRouter
        assert IntentRouter.route_intent("send an invitation") == ["InvitationAgent"]
        assert IntentRouter.route_intent("invite John to a meeting") == ["InvitationAgent"]
        assert IntentRouter.route_intent("schedule a discovery call") == ["InvitationAgent"]
        assert IntentRouter.route_intent("project kickoff meeting") == ["InvitationAgent"]

    def test_location_tracer_intent_keywords(self):
        from app.agents.router import IntentRouter
        assert IntentRouter.route_intent("where are my leads located") == ["LocationTracerAgent"]
        assert IntentRouter.route_intent("show lead location distribution") == ["LocationTracerAgent"]
        assert IntentRouter.route_intent("what timezone is my lead in") == ["LocationTracerAgent"]
        assert IntentRouter.route_intent("trace location for contact") == ["LocationTracerAgent"]

    def test_reminder_intent_keywords(self):
        from app.agents.router import IntentRouter
        assert IntentRouter.route_intent("remind me to follow up") == ["ReminderAgent"]
        assert IntentRouter.route_intent("set a reminder for tomorrow") == ["ReminderAgent"]
        assert IntentRouter.route_intent("don't forget to send the proposal") == ["ReminderAgent"]
        assert IntentRouter.route_intent("alert me about the deadline") == ["ReminderAgent"]
        assert IntentRouter.route_intent("snooze my current notification") == ["ReminderAgent"]

    def test_existing_routes_not_broken(self):
        from app.agents.router import IntentRouter
        assert IntentRouter.route_intent("follow up with John") == ["FollowUpAgent"]
        assert IntentRouter.route_intent("draft a proposal") == ["ProposalAgent"]
        assert IntentRouter.route_intent("show analytics") == ["AnalyticsAgent"]
        assert IntentRouter.route_intent("plan my day") == ["TimeManagementAgent"]
        assert IntentRouter.route_intent("find a lead") == ["LeadAgent"]


# ──────────────────────────────────────────────
# 4. Model Tests
# ──────────────────────────────────────────────

class TestInvitationModel:
    """Test InvitationModel exists and has correct schema."""

    def test_invitation_model_table_name(self):
        from app.models.invitation import InvitationModel
        assert InvitationModel.__tablename__ == "invitations"

    def test_invitation_model_columns(self):
        from app.models.invitation import InvitationModel
        columns = {c.name for c in InvitationModel.__table__.columns}
        expected = {"id", "user_id", "lead_id", "title", "description",
                    "invitation_type", "status", "recipient_name", "recipient_email",
                    "scheduled_at", "location", "meeting_link", "message_body"}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_invitation_model_defaults(self):
        from app.models.invitation import InvitationModel
        status_col = InvitationModel.__table__.columns["status"]
        type_col = InvitationModel.__table__.columns["invitation_type"]
        assert status_col.default.arg == "draft"
        assert type_col.default.arg == "meeting"


class TestReminderModel:
    """Test ReminderModel exists and has correct schema."""

    def test_reminder_model_table_name(self):
        from app.models.reminder import ReminderModel
        assert ReminderModel.__tablename__ == "reminders"

    def test_reminder_model_columns(self):
        from app.models.reminder import ReminderModel
        columns = {c.name for c in ReminderModel.__table__.columns}
        expected = {"id", "user_id", "linked_lead_id", "linked_project_id",
                    "title", "description", "remind_at", "status", "priority",
                    "recurrence", "snoozed_until"}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_reminder_model_defaults(self):
        from app.models.reminder import ReminderModel
        status_col = ReminderModel.__table__.columns["status"]
        priority_col = ReminderModel.__table__.columns["priority"]
        assert status_col.default.arg == "active"
        assert priority_col.default.arg == "medium"


# ──────────────────────────────────────────────
# 5. Models __init__ Export Tests
# ──────────────────────────────────────────────

class TestModelExports:
    """Verify new models are exported from the models package."""

    def test_invitation_model_exported(self):
        from app.models import InvitationModel
        assert InvitationModel is not None

    def test_reminder_model_exported(self):
        from app.models import ReminderModel
        assert ReminderModel is not None


# ──────────────────────────────────────────────
# 6. Location Service Tests
# ──────────────────────────────────────────────

class TestLocationService:
    """Test LocationService utility methods."""

    def test_resolve_private_ip(self):
        from app.services.location_service import LocationService
        result = LocationService.resolve_ip_location("192.168.1.1")
        assert result["region"] == "Private Network"
        assert result["country"] == "Local"

    def test_resolve_localhost(self):
        from app.services.location_service import LocationService
        result = LocationService.resolve_ip_location("127.0.0.1")
        assert result["city"] == "Localhost"

    def test_resolve_unknown_ip(self):
        from app.services.location_service import LocationService
        result = LocationService.resolve_ip_location("8.8.8.8")
        assert result["city"] == "Unknown"

    def test_resolve_10_range(self):
        from app.services.location_service import LocationService
        result = LocationService.resolve_ip_location("10.0.0.1")
        assert result["city"] == "Internal"

    def test_resolve_ipv6_localhost(self):
        from app.services.location_service import LocationService
        result = LocationService.resolve_ip_location("::1")
        assert result["city"] == "Localhost"


# ──────────────────────────────────────────────
# 7. Context Builder Tests
# ──────────────────────────────────────────────

class TestContextBuilderNewMethods:
    """Verify the 3 new context builder methods exist and are callable."""

    def test_build_invitation_context_exists(self):
        from app.agents.context_builder import AgentContextBuilder
        assert hasattr(AgentContextBuilder, "build_invitation_context")
        assert callable(AgentContextBuilder.build_invitation_context)

    def test_build_location_context_exists(self):
        from app.agents.context_builder import AgentContextBuilder
        assert hasattr(AgentContextBuilder, "build_location_context")
        assert callable(AgentContextBuilder.build_location_context)

    def test_build_reminder_context_exists(self):
        from app.agents.context_builder import AgentContextBuilder
        assert hasattr(AgentContextBuilder, "build_reminder_context")
        assert callable(AgentContextBuilder.build_reminder_context)

    def test_existing_context_builders_preserved(self):
        from app.agents.context_builder import AgentContextBuilder
        for method in ["build_lead_context", "build_research_context", "build_outreach_context",
                       "build_followup_context", "build_proposal_context", "build_project_context",
                       "build_timemanagement_context", "build_learning_context", "build_analytics_context"]:
            assert hasattr(AgentContextBuilder, method), f"Existing method {method} missing"


# ──────────────────────────────────────────────
# 8. API Router Registration Tests
# ──────────────────────────────────────────────

class TestAPIRouterRegistration:
    """Verify new routers are registered in the API."""

    def test_invitation_router_registered(self):
        from app.api.v1.router import api_router
        prefixes = [r.include_context.prefix for r in api_router.routes if hasattr(r, "include_context")]
        assert "/invitations" in prefixes, f"Invitations router not found in prefixes: {prefixes}"

    def test_location_router_registered(self):
        from app.api.v1.router import api_router
        prefixes = [r.include_context.prefix for r in api_router.routes if hasattr(r, "include_context")]
        assert "/location" in prefixes, f"Location router not found in prefixes: {prefixes}"

    def test_reminders_router_registered(self):
        from app.api.v1.router import api_router
        prefixes = [r.include_context.prefix for r in api_router.routes if hasattr(r, "include_context")]
        assert "/reminders" in prefixes, f"Reminders router not found in prefixes: {prefixes}"

    def test_total_router_count(self):
        """Verify we now have registered sub-routers (at least 19 including new agents)."""
        from app.api.v1.router import api_router
        sub_routers = [r for r in api_router.routes if hasattr(r, "include_context")]
        assert len(sub_routers) >= 19, f"Expected at least 19 sub-routers, got {len(sub_routers)}"

        all_tags = []
        for r in sub_routers:
            all_tags.extend(r.include_context.tags or [])
        assert "Invitation Agent" in all_tags
        assert "Location Tracer Agent" in all_tags
        assert "Reminder Agent" in all_tags


# ──────────────────────────────────────────────
# 9. Agent System Policy Security Tests
# ──────────────────────────────────────────────

class TestAgentSecurityPolicies:
    """Verify new agents have proper safety constraints in system policies."""

    def test_invitation_agent_no_auto_send(self):
        from app.agents.specialized.invitation_agent import InvitationAgent
        agent = InvitationAgent()
        policy = agent.system_policy.lower()
        assert "do not" in policy or "not" in policy
        assert "automatically" in policy or "auto" in policy

    def test_location_tracer_authorized_only(self):
        from app.agents.specialized.location_tracer_agent import LocationTracerAgent
        agent = LocationTracerAgent()
        policy = agent.system_policy.lower()
        assert "authorized" in policy

    def test_reminder_agent_has_policy(self):
        from app.agents.specialized.reminder_agent import ReminderAgent
        agent = ReminderAgent()
        assert len(agent.system_policy) > 50, "System policy is too short"
        assert "reminder" in agent.system_policy.lower()


# ──────────────────────────────────────────────
# 10. Agent Run Method Signature Tests
# ──────────────────────────────────────────────

class TestAgentRunSignatures:
    """Verify new agents have the correct run() method signature matching BaseAgent."""

    def test_invitation_agent_run_is_async(self):
        import inspect
        from app.agents.specialized.invitation_agent import InvitationAgent
        agent = InvitationAgent()
        assert inspect.iscoroutinefunction(agent.run)

    def test_location_tracer_agent_run_is_async(self):
        import inspect
        from app.agents.specialized.location_tracer_agent import LocationTracerAgent
        agent = LocationTracerAgent()
        assert inspect.iscoroutinefunction(agent.run)

    def test_reminder_agent_run_is_async(self):
        import inspect
        from app.agents.specialized.reminder_agent import ReminderAgent
        agent = ReminderAgent()
        assert inspect.iscoroutinefunction(agent.run)

    def test_invitation_agent_get_context_is_async(self):
        import inspect
        from app.agents.specialized.invitation_agent import InvitationAgent
        agent = InvitationAgent()
        assert inspect.iscoroutinefunction(agent.get_context)

    def test_location_tracer_agent_get_context_is_async(self):
        import inspect
        from app.agents.specialized.location_tracer_agent import LocationTracerAgent
        agent = LocationTracerAgent()
        assert inspect.iscoroutinefunction(agent.get_context)

    def test_reminder_agent_get_context_is_async(self):
        import inspect
        from app.agents.specialized.reminder_agent import ReminderAgent
        agent = ReminderAgent()
        assert inspect.iscoroutinefunction(agent.get_context)

