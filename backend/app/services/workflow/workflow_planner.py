import json
import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService, LLMRequest
from app.services.workflow.workflow_policy import (
    WorkflowPlanSpec,
    WorkflowStepSpec,
    WorkflowPolicyEngine,
    VALID_AGENT_NAMES,
    SIDE_EFFECT_ACTIONS,
)

logger = logging.getLogger("flowpilot.workflow.planner")

PLANNER_SYSTEM_PROMPT = f"""You are the Master Workflow Planner for FlowPilot AI.
Your job is to decompose high-level business objectives into an optimal, safe, machine-readable multi-agent execution plan.

You MUST choose agents ONLY from the following 12 verified agents:
1. LeadAgent (Lead qualification, ICP scoring, CRM pipeline management)
2. ResearchAgent (Market research, knowledge vault analysis, web search)
3. OutreachAgent (Drafting cold outreach messages, email pitches)
4. FollowUpAgent (Multi-step follow-up sequences, cadence drafting, why-to-followup reasoning)
5. ProposalAgent (Scope of work generation, freelance proposals, pricing structures)
6. ProjectAgent (Task decomposition, milestone planning, deliverable extraction)
7. TimeManagementAgent (Focus blocks, calendar scheduling, daily agenda planning)
8. LearningAgent (Skill acceleration, learning roadmaps, spaced repetition)
9. AnalyticsAgent (Revenue metrics, conversion tracking, business performance summaries)
10. InvitationAgent (Meeting invites, discovery call scheduling, kickoff invites)
11. LocationTracerAgent (Geographic lead mapping, timezone-aware scheduling context)
12. ReminderAgent (Deadline reminders, smart alert scheduling)

CRITICAL RULES:
- Output valid JSON only, matching the exact schema below.
- Do NOT invent new agent names.
- Identify dependencies cleanly using step IDs (e.g. ["step_1"]).
- Flag any step that performs external side effects (like sending emails, invitations, or altering live records) with "requires_approval": true.
- Safe read/analyze steps do NOT require approval ("requires_approval": false).

Output JSON Schema:
{{
  "goal": "<brief summary of the goal>",
  "steps": [
    {{
      "id": "step_1",
      "agent": "<One of the 12 Agents>",
      "action": "<specific_action_name>",
      "description": "<concise description of subtask>",
      "depends_on": [],
      "requires_approval": false
    }},
    {{
      "id": "step_2",
      "agent": "<One of the 12 Agents>",
      "action": "<specific_action_name>",
      "description": "<concise description>",
      "depends_on": ["step_1"],
      "requires_approval": false
    }}
  ]
}}
"""


class WorkflowPlanner:
    """Production planner decomposing natural-language goals into validated multi-agent execution graphs."""

    @classmethod
    async def create_plan(cls, goal: str, user_id: str, db: AsyncSession) -> WorkflowPlanSpec:
        """Decomposes a goal into a validated WorkflowPlanSpec using LLM with deterministic fallback."""
        if not goal or not goal.strip():
            raise ValueError("Workflow goal cannot be empty.")

        # Attempt LLM decomposition
        try:
            llm_req = LLMRequest(
                system_prompt=PLANNER_SYSTEM_PROMPT,
                prompt=f"Goal to plan:\n\"{goal}\"\n\nProduce the JSON execution plan now:",
                temperature=0.1,
                max_tokens=1024,
                response_format="json",
            )
            llm_res = await LLMService.generate(request=llm_req, user_id=user_id, db=db)
            raw_json = llm_res.content.strip()

            # Clean JSON markdown if wrapped in ```json
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

        # Deterministic Fallback Planner
        return cls._generate_deterministic_plan(goal)

    @classmethod
    def _generate_deterministic_plan(cls, goal: str) -> WorkflowPlanSpec:
        """Deterministic rule-based DAG synthesizer ensuring robust fallback for multi-agent workflows."""
        g_lower = goal.lower()
        steps: List[WorkflowStepSpec] = []

        # Check for lead + follow-up + time + approval workflow pattern (e.g. Hindi/English user objective)
        if ("lead" in g_lower or "prospect" in g_lower) and ("follow" in g_lower or "draft" in g_lower):
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="LeadAgent",
                    action="analyze_pending_leads",
                    description="Analyze pending leads and identify high-priority conversion opportunities",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_2",
                    agent="FollowUpAgent",
                    action="draft_followups",
                    description="Generate tailored follow-up communication drafts for identified high-priority leads",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )
            if "time" in g_lower or "timing" in g_lower or "schedule" in g_lower or "when" in g_lower or "choose" in g_lower:
                steps.append(
                    WorkflowStepSpec(
                        id="step_3",
                        agent="TimeManagementAgent",
                        action="recommend_followup_timing",
                        description="Determine optimal time blocks and calendar slots for dispatching follow-ups",
                        depends_on=["step_2"],
                        requires_approval=False,
                    )
                )
                prev_id = "step_3"
            else:
                prev_id = "step_2"

            # Check if approval or dispatch was requested
            if "approval" in g_lower or "approve" in g_lower or "bhejne" in g_lower or "send" in g_lower:
                steps.append(
                    WorkflowStepSpec(
                        id=f"step_{len(steps) + 1}",
                        agent="OutreachAgent",
                        action="send_followup",
                        description="Dispatch approved follow-up messages to recipient leads",
                        depends_on=[prev_id],
                        requires_approval=True,
                    )
                )

        elif "research" in g_lower or "market" in g_lower or "competitor" in g_lower:
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="ResearchAgent",
                    action="conduct_market_research",
                    description="Search knowledge vault and analyze market opportunities",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            if "proposal" in g_lower:
                steps.append(
                    WorkflowStepSpec(
                        id="step_2",
                        agent="ProposalAgent",
                        action="generate_proposal",
                        description="Generate client proposal based on research findings",
                        depends_on=["step_1"],
                        requires_approval=False,
                    )
                )

        elif "project" in g_lower or "milestone" in g_lower or "task" in g_lower:
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="ProjectAgent",
                    action="breakdown_tasks",
                    description="Decompose project deliverables into actionable tasks",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            steps.append(
                WorkflowStepSpec(
                    id="step_2",
                    agent="TimeManagementAgent",
                    action="schedule_tasks",
                    description="Allocate focus time blocks for decomposed project tasks",
                    depends_on=["step_1"],
                    requires_approval=False,
                )
            )

        elif "invite" in g_lower or "meeting" in g_lower or "discovery call" in g_lower:
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="InvitationAgent",
                    action="draft_invitation",
                    description="Draft personalized discovery call meeting invitation",
                    depends_on=[],
                    requires_approval=False,
                )
            )
            if "send" in g_lower or "dispatch" in g_lower or "bhejo" in g_lower:
                steps.append(
                    WorkflowStepSpec(
                        id="step_2",
                        agent="InvitationAgent",
                        action="send_invitation",
                        description="Send meeting invitation to client",
                        depends_on=["step_1"],
                        requires_approval=True,
                    )
                )

        else:
            # Default single-agent baseline
            steps.append(
                WorkflowStepSpec(
                    id="step_1",
                    agent="LeadAgent",
                    action="analyze_pipeline",
                    description=f"Process objective: {goal[:100]}",
                    depends_on=[],
                    requires_approval=False,
                )
            )

        plan = WorkflowPlanSpec(goal=goal, steps=steps)
        val = WorkflowPolicyEngine.validate_plan(plan)
        if not val["valid"]:
            raise ValueError(f"Generated fallback plan is invalid: {val['error']}")
        return plan
