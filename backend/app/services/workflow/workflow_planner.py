import json
import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService, LLMRequest
from app.services.workflow.capability_registry import CapabilityRegistry
from app.services.workflow.workflow_policy import (
    WorkflowPlanSpec,
    WorkflowStepSpec,
    WorkflowPolicyEngine,
    VALID_AGENT_NAMES,
    SIDE_EFFECT_ACTIONS,
)

logger = logging.getLogger("flowpilot.workflow.planner")


def get_planner_system_prompt() -> str:
    registry_text = CapabilityRegistry.format_registry_for_planner()
    return f"""You are the Master Autonomous Workflow Planner for FlowPilot AI.
Your job is to decompose high-level business objectives into an optimal, safe, machine-readable multi-agent execution plan.

You MUST choose agents and actions ONLY from the following verified Capability Registry:

{registry_text}

CRITICAL PLANNING RULES:
- Output valid JSON only matching the schema below.
- Choose ONLY agents and actions defined in the Capability Registry. Do NOT invent new agent names or actions.
- Identify dependencies cleanly using step IDs (e.g. ["step_1"]).
- Automatically mark any step that performs external side effects (e.g. sending messages, modifying critical data) with "requires_approval": true.
- Safe analysis and drafting steps do NOT require approval ("requires_approval": false).
- Keep execution graphs acyclic and strictly purposeful.

Output JSON Schema:
{{
  "goal": "<brief summary of the objective>",
  "steps": [
    {{
      "id": "step_1",
      "agent": "<AgentName from Registry>",
      "action": "<action_name from Registry>",
      "description": "<concise description of task>",
      "depends_on": [],
      "requires_approval": false
    }},
    {{
      "id": "step_2",
      "agent": "<AgentName from Registry>",
      "action": "<action_name from Registry>",
      "description": "<concise description>",
      "depends_on": ["step_1"],
      "requires_approval": false
    }}
  ]
}}
"""


class WorkflowPlanner:
    """Production autonomous planner decomposing goals into validated multi-agent execution graphs."""

    @classmethod
    async def create_plan(cls, goal: str, user_id: str, db: AsyncSession) -> WorkflowPlanSpec:
        """Decomposes a goal into a validated WorkflowPlanSpec using LLM with deterministic fallback."""
        if not goal or not goal.strip():
            raise ValueError("Workflow goal cannot be empty.")

        # 1. Attempt LLM-powered autonomous goal decomposition
        try:
            llm_req = LLMRequest(
                system_prompt=get_planner_system_prompt(),
                prompt=f"Goal to plan:\n\"{goal}\"\n\nProduce the JSON execution plan now:",
                temperature=0.1,
                max_tokens=1024,
                response_format="json",
            )
            llm_res = await LLMService.generate(req=llm_req, user_id=user_id, db=db)
            raw_json = llm_res.content.strip()

            # Clean JSON markdown fences
            if "```" in raw_json:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_json, re.DOTALL)
                if match:
                    raw_json = match.group(1)

            parsed = json.loads(raw_json)
            plan_spec = WorkflowPlanSpec(**parsed)

            # Validate plan via policy engine
            val_res = WorkflowPolicyEngine.validate_plan(plan_spec)
            if val_res["valid"]:
                return plan_spec
            else:
                logger.warning(f"LLM plan failed policy validation ({val_res['error']}). Falling back to deterministic planner.")
        except Exception as e:
            logger.warning(f"LLM planning failed ({str(e)}). Generating deterministic plan.")

        # 2. Deterministic Fallback Planner
        return cls._generate_deterministic_plan(goal)

    @classmethod
    def _generate_deterministic_plan(cls, goal: str) -> WorkflowPlanSpec:
        """Deterministic rule-based DAG synthesizer ensuring robust fallback for multi-agent workflows."""
        g_lower = goal.lower()
        steps: List[WorkflowStepSpec] = []

        # Pattern A: Lead Analysis -> FollowUp Drafting -> Time Recommendation -> Outreach Side Effect
        if ("lead" in g_lower or "prospect" in g_lower) and any(k in g_lower for k in ["follow", "draft", "outreach", "priorit", "analyz", "email"]):
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="LeadAgent",
                    action="analyze_leads",
                    description="Analyze pending leads and evaluate high-priority prospect scoring.",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_2",
                    agent="FollowUpAgent",
                    action="draft_followups",
                    description="Generate personalized follow-up email drafts based on qualified lead signals.",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_3",
                    agent="TimeManagementAgent",
                    action="recommend_timing",
                    description="Analyze calendar workload and recommend optimal follow-up dispatch timing.",
                    depends_on=["step_2"],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_4",
                    agent="OutreachAgent",
                    action="send_outreach",
                    description="Dispatch approved follow-up communications to prospective clients.",
                    depends_on=["step_3"],
                    requires_approval=True,  # External side effect requires human approval
                )
            )
            return WorkflowPlanSpec(goal=goal, steps=steps)

        # Pattern B: Proposal & Pricing Generation
        if "proposal" in g_lower or "quote" in g_lower or "scope" in g_lower:
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="ResearchAgent",
                    action="research_market",
                    description="Research client domain and competitive positioning.",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_2",
                    agent="ProposalAgent",
                    action="generate_proposal",
                    description="Generate structured project proposal, milestone deliverables, and pricing.",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_3",
                    agent="ProposalAgent",
                    action="send_proposal",
                    description="Dispatch finalized proposal to client for review.",
                    depends_on=["step_2"],
                    requires_approval=True,
                )
            )
            return WorkflowPlanSpec(goal=goal, steps=steps)

        # Pattern C: Meeting Coordination & Discovery
        if "meeting" in g_lower or "call" in g_lower or "invite" in g_lower or "discovery" in g_lower:
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="TimeManagementAgent",
                    action="recommend_timing",
                    description="Identify available calendar slots for discovery meeting.",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_2",
                    agent="InvitationAgent",
                    action="draft_invitation",
                    description="Draft discovery call invitation with agenda details.",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_3",
                    agent="InvitationAgent",
                    action="send_invitation",
                    description="Dispatch meeting invitation to attendee.",
                    depends_on=["step_2"],
                    requires_approval=True,
                )
            )
            return WorkflowPlanSpec(goal=goal, steps=steps)

        # Generic Safe 2-Step Fallback (Research -> Analytics)
        steps.append(
            WorkflowStepSpec(
                id="step_1",
                agent="ResearchAgent",
                action="research_market",
                description=f"Synthesize intelligence regarding: {goal[:100]}",
                depends_on=[],
                requires_approval=False,
            )
        )
        steps.append(
            WorkflowStepSpec(
                id="step_2",
                agent="AnalyticsAgent",
                action="generate_analytics_report",
                description="Summarize execution insights and business impact metrics.",
                depends_on=["step_1"],
                requires_approval=False,
            )
        )
        return WorkflowPlanSpec(goal=goal, steps=steps)
