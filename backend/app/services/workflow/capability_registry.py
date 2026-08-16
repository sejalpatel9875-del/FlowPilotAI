from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field


class AgentCapabilitySpec(BaseModel):
    agent_name: str = Field(..., description="Unique name matching orchestrator agent registration")
    description: str = Field(..., description="High-level description of agent's functional domain")
    risk_level: str = Field("LOW", description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")
    capabilities: List[str] = Field(..., description="Machine-readable list of supported capabilities")
    inputs: List[str] = Field(..., description="Required input field names")
    outputs: List[str] = Field(..., description="Normalized output fields")
    read_actions: List[str] = Field(default_factory=list, description="Safe read/query operations (no approval needed)")
    side_effect_actions: List[str] = Field(default_factory=list, description="External state-modifying actions (mandatory approval)")


# Comprehensive, machine-readable registry for the 12 verified agents
AGENT_REGISTRY: Dict[str, AgentCapabilitySpec] = {
    "LeadAgent": AgentCapabilitySpec(
        agent_name="LeadAgent",
        description="Lead qualification, ICP scoring, CRM pipeline management, and contact research.",
        risk_level="LOW",
        capabilities=["analyze_leads", "score_leads", "prioritize_leads", "enrich_lead_profile"],
        inputs=["goal", "lead_records", "criteria"],
        outputs=["qualified_leads", "lead_id", "priority", "score", "recommended_action"],
        read_actions=["analyze_leads", "score_leads", "prioritize_leads", "enrich_lead_profile"],
        side_effect_actions=["archive_lead", "delete_lead"],
    ),
    "ResearchAgent": AgentCapabilitySpec(
        agent_name="ResearchAgent",
        description="Market research, competitor analysis, client intelligence, and knowledge retrieval.",
        risk_level="LOW",
        capabilities=["research_market", "analyze_competitors", "query_knowledge_vault", "synthesize_domain_report"],
        inputs=["query", "domain", "context"],
        outputs=["research_summary", "key_insights", "sources"],
        read_actions=["research_market", "analyze_competitors", "query_knowledge_vault", "synthesize_domain_report"],
        side_effect_actions=[],
    ),
    "OutreachAgent": AgentCapabilitySpec(
        agent_name="OutreachAgent",
        description="Cold email drafting, personalized pitch generation, and communication dispatch.",
        risk_level="MEDIUM",
        capabilities=["draft_cold_email", "generate_pitch", "send_outreach", "dispatch_message"],
        inputs=["lead_context", "value_proposition", "tone"],
        outputs=["draft_email", "subject", "recipient_email", "dispatch_status"],
        read_actions=["draft_cold_email", "generate_pitch"],
        side_effect_actions=["send_outreach", "dispatch_message", "send_email"],
    ),
    "FollowUpAgent": AgentCapabilitySpec(
        agent_name="FollowUpAgent",
        description="Multi-touch follow-up cadence planning, message drafting, and check-in timing.",
        risk_level="MEDIUM",
        capabilities=["plan_cadence", "draft_followups", "analyze_stale_leads", "send_followup"],
        inputs=["lead_id", "interaction_history", "last_contact_date"],
        outputs=["followup_draft", "cadence_step", "recommended_delay_days", "followup_reason"],
        read_actions=["plan_cadence", "draft_followups", "analyze_stale_leads"],
        side_effect_actions=["send_followup", "dispatch_message"],
    ),
    "ProposalAgent": AgentCapabilitySpec(
        agent_name="ProposalAgent",
        description="Scope of work generation, milestone estimates, pricing structures, and deliverables.",
        risk_level="MEDIUM",
        capabilities=["generate_proposal", "estimate_scope", "calculate_pricing", "send_proposal"],
        inputs=["client_requirements", "deliverables", "rate_card"],
        outputs=["proposal_document", "milestones", "total_estimate", "terms"],
        read_actions=["generate_proposal", "estimate_scope", "calculate_pricing"],
        side_effect_actions=["send_proposal"],
    ),
    "ProjectAgent": AgentCapabilitySpec(
        agent_name="ProjectAgent",
        description="Project planning, sprint task decomposition, milestone tracking, and deliverables.",
        risk_level="LOW",
        capabilities=["decompose_project", "create_milestones", "track_deliverables", "assign_tasks"],
        inputs=["project_scope", "deadline", "milestone_list"],
        outputs=["task_breakdown", "sprint_plan", "deliverables_timeline"],
        read_actions=["decompose_project", "create_milestones", "track_deliverables"],
        side_effect_actions=["modify_project_status", "delete_project"],
    ),
    "TimeManagementAgent": AgentCapabilitySpec(
        agent_name="TimeManagementAgent",
        description="Calendar planning, focus time optimization, workload balancing, and scheduling recommendations.",
        risk_level="LOW",
        capabilities=["recommend_timing", "schedule_focus_block", "optimize_calendar", "balance_workload"],
        inputs=["pending_tasks", "calendar_events", "target_deadline"],
        outputs=["optimal_time_slot", "scheduled_blocks", "daily_agenda"],
        read_actions=["recommend_timing", "optimize_calendar", "balance_workload"],
        side_effect_actions=["schedule_focus_block", "modify_calendar_event"],
    ),
    "LearningAgent": AgentCapabilitySpec(
        agent_name="LearningAgent",
        description="Skill acceleration, curriculum generation, spaced repetition, and technical upskilling.",
        risk_level="LOW",
        capabilities=["generate_curriculum", "schedule_spaced_repetition", "track_skill_progress"],
        inputs=["target_skill", "current_level", "target_date"],
        outputs=["learning_roadmap", "daily_review_topics", "quiz_items"],
        read_actions=["generate_curriculum", "track_skill_progress"],
        side_effect_actions=["schedule_spaced_repetition"],
    ),
    "AnalyticsAgent": AgentCapabilitySpec(
        agent_name="AnalyticsAgent",
        description="Revenue metrics, pipeline conversion forecasting, business velocity, and performance analytics.",
        risk_level="LOW",
        capabilities=["compute_pipeline_metrics", "forecast_conversions", "generate_analytics_report"],
        inputs=["date_range", "pipeline_data", "metrics_filter"],
        outputs=["conversion_rates", "projected_revenue", "velocity_summary"],
        read_actions=["compute_pipeline_metrics", "forecast_conversions", "generate_analytics_report"],
        side_effect_actions=[],
    ),
    "InvitationAgent": AgentCapabilitySpec(
        agent_name="InvitationAgent",
        description="Client discovery calls, meeting coordination, and event kickoff scheduling.",
        risk_level="MEDIUM",
        capabilities=["draft_invitation", "coordinate_meeting", "send_invitation", "cancel_invitation"],
        inputs=["recipient_email", "recipient_name", "meeting_type", "proposed_time"],
        outputs=["invitation_body", "meeting_link", "dispatch_status"],
        read_actions=["draft_invitation", "coordinate_meeting"],
        side_effect_actions=["send_invitation", "cancel_invitation"],
    ),
    "LocationTracerAgent": AgentCapabilitySpec(
        agent_name="LocationTracerAgent",
        description="Geographic intelligence, lead location resolution, and timezone-aware scheduling.",
        risk_level="LOW",
        capabilities=["analyze_lead_locations", "resolve_ip_region", "compute_timezone_matrix"],
        inputs=["lead_locations", "ip_address"],
        outputs=["geographic_summary", "timezone_offsets", "recommended_windows"],
        read_actions=["analyze_lead_locations", "resolve_ip_region", "compute_timezone_matrix"],
        side_effect_actions=[],
    ),
    "ReminderAgent": AgentCapabilitySpec(
        agent_name="ReminderAgent",
        description="Deadline tracking, smart reminder scheduling, and proactive alert planning.",
        risk_level="LOW",
        capabilities=["create_reminder", "list_due_reminders", "snooze_reminder", "dispatch_alert"],
        inputs=["title", "remind_at", "priority", "linked_resource"],
        outputs=["reminder_id", "scheduled_at", "status"],
        read_actions=["list_due_reminders"],
        side_effect_actions=["create_reminder", "snooze_reminder", "dispatch_alert"],
    ),
}


class CapabilityRegistry:
    """Master machine-readable registry and deterministic validation engine for all 12 agents."""

    @classmethod
    def get_agent_spec(cls, agent_name: str) -> Optional[AgentCapabilitySpec]:
        return AGENT_REGISTRY.get(agent_name)

    @classmethod
    def get_all_agents(cls) -> List[AgentCapabilitySpec]:
        return list(AGENT_REGISTRY.values())

    @classmethod
    def is_agent_valid(cls, agent_name: str) -> bool:
        return agent_name in AGENT_REGISTRY

    @classmethod
    def is_action_valid(cls, agent_name: str, action: str) -> bool:
        spec = AGENT_REGISTRY.get(agent_name)
        if not spec:
            return False
        action_clean = action.strip().lower()
        all_actions = [c.lower() for c in spec.capabilities] + [r.lower() for r in spec.read_actions] + [s.lower() for s in spec.side_effect_actions]
        # Direct match or partial action identifier match
        return any(act == action_clean or act in action_clean or action_clean in act for act in all_actions)

    @classmethod
    def is_side_effect(cls, agent_name: str, action: str) -> bool:
        spec = AGENT_REGISTRY.get(agent_name)
        if not spec:
            return True  # Unknown agent action defaults to requiring approval for safety
        action_clean = action.strip().lower()
        if any(side_act in action_clean for side_act in [s.lower() for s in spec.side_effect_actions]):
            return True
        if any(kw in action_clean for kw in ["send", "delete", "dispatch", "archive", "modify"]):
            return True
        return False

    @classmethod
    def resolve_candidate_agent(cls, query: str) -> Optional[str]:
        """Resolves the best suited agent for a given task description."""
        q_lower = query.lower()
        
        # 1. Check exact capability matches
        for name, spec in AGENT_REGISTRY.items():
            if any(cap.lower().replace("_", " ") in q_lower for cap in spec.capabilities):
                return name
            if name.lower() in q_lower:
                return name

        # 2. Check token intersections for multi-word capabilities (e.g. 'score' and 'leads')
        for name, spec in AGENT_REGISTRY.items():
            for cap in spec.capabilities:
                parts = cap.lower().split("_")
                if len(parts) >= 2 and all(p in q_lower for p in parts):
                    return name

        # 3. Domain keyword heuristics
        domain_keywords = {
            "LeadAgent": ["lead", "prospect", "crm", "icp"],
            "FollowUpAgent": ["follow", "cadence", "followup"],
            "OutreachAgent": ["outreach", "pitch", "cold email"],
            "ProposalAgent": ["proposal", "scope", "pricing", "quote"],
            "ProjectAgent": ["project", "deliverable", "milestone", "sprint"],
            "TimeManagementAgent": ["time", "timing", "schedule", "calendar", "focus block", "agenda"],
            "LearningAgent": ["learn", "skill", "curriculum", "spaced repetition"],
            "AnalyticsAgent": ["analytic", "metric", "revenue", "conversion"],
            "InvitationAgent": ["invitation", "invite", "meeting", "discovery call"],
            "LocationTracerAgent": ["location", "geographic", "timezone", "tracer"],
            "ReminderAgent": ["reminder", "remind", "deadline alert"],
            "ResearchAgent": ["research", "competitor", "market analysis"],
        }
        for agent_name, kws in domain_keywords.items():
            if any(kw in q_lower for kw in kws):
                return agent_name

        return None

    @classmethod
    def format_registry_for_planner(cls) -> str:
        """Formats the capability registry into a concise schema description for the LLM planner."""
        lines = []
        for name, spec in AGENT_REGISTRY.items():
            lines.append(
                f"- {name} (Risk: {spec.risk_level}): {spec.description}\n"
                f"  Capabilities: {', '.join(spec.capabilities)}\n"
                f"  Read Actions: {', '.join(spec.read_actions) or 'None'}\n"
                f"  Side Effect Actions (Approval Required): {', '.join(spec.side_effect_actions) or 'None'}"
            )
        return "\n".join(lines)
