from typing import List, Dict, Any, Set
from pydantic import BaseModel, Field


# The 12 explicitly verified and registered agents in FlowPilot AI
VALID_AGENT_NAMES = {
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
}

# Actions that produce external state modifications or irreversible side effects
SIDE_EFFECT_ACTIONS = {
    "send_outreach",
    "send_email",
    "send_invitation",
    "send_followup",
    "dispatch_message",
    "delete_record",
    "archive_data",
    "execute_external_action",
    "modify_critical_crm",
}

MAX_WORKFLOW_STEPS = 10
MAX_REPLAN_ATTEMPTS = 3


class WorkflowStepSpec(BaseModel):
    id: str = Field(..., description="Unique step identifier e.g. step_1")
    agent: str = Field(..., description="Specialized agent name")
    action: str = Field(..., description="Action to perform")
    description: str = Field("", description="Human-readable description")
    depends_on: List[str] = Field(default_factory=list, description="List of prerequisite step IDs")
    requires_approval: bool = Field(False, description="Whether human approval is required before execution")


class WorkflowPlanSpec(BaseModel):
    goal: str
    steps: List[WorkflowStepSpec]


class WorkflowPolicyEngine:
    """Production policy and safety layer enforcing plan validity, DAG acyclicity, and approval gates."""

    @classmethod
    def validate_plan(cls, plan_spec: WorkflowPlanSpec) -> Dict[str, Any]:
        """Thoroughly validates a workflow plan against security and structure policies."""
        if not plan_spec.goal or not plan_spec.goal.strip():
            return {"valid": False, "error": "Workflow goal cannot be empty."}

        if not plan_spec.steps or len(plan_spec.steps) == 0:
            return {"valid": False, "error": "Workflow plan must contain at least one step."}

        if len(plan_spec.steps) > MAX_WORKFLOW_STEPS:
            return {"valid": False, "error": f"Workflow plan exceeds maximum allowed steps ({MAX_WORKFLOW_STEPS})."}

        step_ids = set()
        for step in plan_spec.steps:
            # 1. Unique step IDs
            if step.id in step_ids:
                return {"valid": False, "error": f"Duplicate step ID '{step.id}' in workflow plan."}
            step_ids.add(step.id)

            # 2. Strict Agent Whitelist Validation
            if step.agent not in VALID_AGENT_NAMES:
                return {
                    "valid": False,
                    "error": f"Invalid agent '{step.agent}'. Agent must be one of: {sorted(list(VALID_AGENT_NAMES))}."
                }

            # 3. Mandatory Side-Effect Approval Gate
            action_lower = step.action.lower()
            if any(side_act in action_lower for side_act in SIDE_EFFECT_ACTIONS) or "send" in action_lower or "delete" in action_lower:
                step.requires_approval = True

        # 4. Dependency Existence Validation
        for step in plan_spec.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    return {"valid": False, "error": f"Step '{step.id}' depends on non-existent step '{dep}'."}
                if dep == step.id:
                    return {"valid": False, "error": f"Step '{step.id}' cannot depend on itself."}

        # 5. DAG Cycle Detection (DFS)
        cycle_error = cls._detect_cycles(plan_spec.steps)
        if cycle_error:
            return {"valid": False, "error": cycle_error}

        return {"valid": True, "error": None}

    @classmethod
    def _detect_cycles(cls, steps: List[WorkflowStepSpec]) -> str | None:
        """Detects circular dependencies in the execution graph using topological DFS."""
        adj: Dict[str, List[str]] = {s.id: list(s.depends_on) for s in steps}
        visited: Dict[str, int] = {s.id: 0 for s in steps}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node: str) -> bool:
            visited[node] = 1
            for neighbor in adj.get(node, []):
                if visited.get(neighbor) == 1:
                    return True  # Cycle detected
                if visited.get(neighbor) == 0:
                    if dfs(neighbor):
                        return True
            visited[node] = 2
            return False

        for s in steps:
            if visited[s.id] == 0:
                if dfs(s.id):
                    return f"Circular dependency cycle detected involving step '{s.id}'."

        return None
