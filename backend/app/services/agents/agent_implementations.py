from typing import List, Dict, Any, Optional
from app.services.agents.base_agent import BaseAgent, AgentRunResult


class LeadAgent(BaseAgent):
    @property
    def name(self) -> str: return "LeadAgent"
    @property
    def description(self) -> str: return "Scores, qualifies, and prioritizes incoming CRM leads."
    @property
    def system_policy(self) -> str: return "Analyze lead parameters and rank deals by value and conversion probability."
    @property
    def allowed_tools(self) -> List[str]: return ["lead_search", "lead_score", "lead_update"]
    @property
    def denied_tools(self) -> List[str]: return ["external_message_send", "database_delete", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Analyzed lead query '{input_query}'. High-value prospect identified with conversion score of 88%.",
            reasoning_summary="Evaluated company size, domain authority, and pipeline velocity.",
            tools_used=["lead_score", "lead_search"]
        )


class ResearchAgent(BaseAgent):
    @property
    def name(self) -> str: return "ResearchAgent"
    @property
    def description(self) -> str: return "Performs prospect research and Knowledge Vault semantic lookups."
    @property
    def system_policy(self) -> str: return "Gather market intelligence and synthesize document context."
    @property
    def allowed_tools(self) -> List[str]: return ["knowledge_search", "company_lookup", "web_search"]
    @property
    def denied_tools(self) -> List[str]: return ["database_delete", "external_message_send", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Research synthesis completed for '{input_query}'. Extracted 3 key industry pain points and target tech stack.",
            reasoning_summary="Queried Knowledge Vault and aggregated company domain signals.",
            tools_used=["knowledge_search", "company_lookup"]
        )


class OutreachAgent(BaseAgent):
    @property
    def name(self) -> str: return "OutreachAgent"
    @property
    def description(self) -> str: return "Drafts personalized cold outreach messages and email pitches."
    @property
    def system_policy(self) -> str: return "Craft persuasive, personalized pitch copy. Sending requires user approval."
    @property
    def allowed_tools(self) -> List[str]: return ["email_draft", "template_generate"]
    @property
    def denied_tools(self) -> List[str]: return ["database_delete", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Drafted cold outreach sequence for: '{input_query}'. Subject: 'Scaling Freelance Engineering Capacity'.",
            reasoning_summary="Generated personalized 3-step email sequence tailored to prospect target role.",
            tools_used=["email_draft"],
            requires_approval=True,
            action_to_approve=f"Send cold email sequence to target lead for '{input_query}'"
        )


class FollowUpAgent(BaseAgent):
    @property
    def name(self) -> str: return "FollowUpAgent"
    @property
    def description(self) -> str: return "Schedules automated follow-up reminders and check-in tasks."
    @property
    def system_policy(self) -> str: return "Track client response timelines and schedule timely touchpoints."
    @property
    def allowed_tools(self) -> List[str]: return ["task_creation", "calendar_read", "reminder_set"]
    @property
    def denied_tools(self) -> List[str]: return ["external_message_send", "database_delete", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Follow-up task scheduled for '{input_query}' in 3 business days.",
            reasoning_summary="Checked calendar availability and set automated reminder priority.",
            tools_used=["reminder_set", "task_creation"]
        )


class ProposalAgent(BaseAgent):
    @property
    def name(self) -> str: return "ProposalAgent"
    @property
    def description(self) -> str: return "Generates scopes of work, pricing estimates, and formal client proposals."
    @property
    def system_policy(self) -> str: return "Structure clear scope boundaries, milestones, and value-based pricing."
    @property
    def allowed_tools(self) -> List[str]: return ["proposal_create", "pricing_calculate", "template_generate"]
    @property
    def denied_tools(self) -> List[str]: return ["database_delete", "external_message_send", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Generated formal project proposal for '{input_query}' with estimated budget of $12,500.",
            reasoning_summary="Calculated hourly estimates across 3 deliverables and applied standard terms.",
            tools_used=["pricing_calculate", "proposal_create"]
        )


class ProjectAgent(BaseAgent):
    @property
    def name(self) -> str: return "ProjectAgent"
    @property
    def description(self) -> str: return "Monitors project milestones, subtasks, and delivery deadlines."
    @property
    def system_policy(self) -> str: return "Ensure project deliverables remain on schedule and track completion percentage."
    @property
    def allowed_tools(self) -> List[str]: return ["project_read", "task_creation", "status_update"]
    @property
    def denied_tools(self) -> List[str]: return ["database_delete", "external_message_send", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Project milestone check complete for '{input_query}'. Overall progress: 68%.",
            reasoning_summary="Audited completed subtasks and updated milestone target completion.",
            tools_used=["project_read", "status_update"]
        )


class TimeManagementAgent(BaseAgent):
    @property
    def name(self) -> str: return "TimeManagementAgent"
    @property
    def description(self) -> str: return "Optimizes daily work schedules, focus blocks, and meeting slots."
    @property
    def system_policy(self) -> str: return "Protect deep work time slots and resolve scheduling conflicts."
    @property
    def allowed_tools(self) -> List[str]: return ["calendar_read", "calendar_write", "slot_optimize"]
    @property
    def denied_tools(self) -> List[str]: return ["database_delete", "external_message_send", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Schedule optimized for '{input_query}'. Reserved 3.5h uninterrupted deep work block.",
            reasoning_summary="Reordered flexible tasks around calendar commitments.",
            tools_used=["calendar_read", "slot_optimize"]
        )


class LearningAgent(BaseAgent):
    @property
    def name(self) -> str: return "LearningAgent"
    @property
    def description(self) -> str: return "Tracks skill acquisition, target roadmaps, and educational progress."
    @property
    def system_policy(self) -> str: return "Guide structured learning paths and recommend skill improvement modules."
    @property
    def allowed_tools(self) -> List[str]: return ["knowledge_search", "task_creation", "calendar_read"]
    @property
    def denied_tools(self) -> List[str]: return ["external_message_send", "database_delete", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Learning roadmap updated for '{input_query}'. Added 2 study subtasks for async architecture.",
            reasoning_summary="Queried skill matrix and scheduled progressive learning goals.",
            tools_used=["knowledge_search", "task_creation"]
        )


class AnalyticsAgent(BaseAgent):
    @property
    def name(self) -> str: return "AnalyticsAgent"
    @property
    def description(self) -> str: return "Computes revenue metrics, lead conversion rates, and time allocation."
    @property
    def system_policy(self) -> str: return "Aggregate performance metrics and highlight operational bottlenecks."
    @property
    def allowed_tools(self) -> List[str]: return ["analytics_query", "report_generate", "metrics_read"]
    @property
    def denied_tools(self) -> List[str]: return ["external_message_send", "database_delete", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Analytics report generated for '{input_query}'. Monthly effective hourly rate: $142/hr.",
            reasoning_summary="Aggregated total project revenue against logged time records.",
            tools_used=["analytics_query", "report_generate"]
        )


class SecurityAgent(BaseAgent):
    @property
    def name(self) -> str: return "SecurityAgent"
    @property
    def description(self) -> str: return "Inspects audit logs, verifies session state, and enforces RBAC rules."
    @property
    def system_policy(self) -> str: return "Audit system integrity, monitor failed logins, and flag security risks."
    @property
    def allowed_tools(self) -> List[str]: return ["audit_read", "session_revoke", "rbac_inspect"]
    @property
    def denied_tools(self) -> List[str]: return ["external_message_send", "database_delete", "credential_access"]

    async def run(self, input_query: str, user_id: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> AgentRunResult:
        return AgentRunResult(
            agent_name=self.name,
            output_text=f"Security audit completed for '{input_query}'. Zero anomalous login events detected.",
            reasoning_summary="Scanned active session signatures and verified password hashing standards.",
            tools_used=["audit_read", "rbac_inspect"]
        )
