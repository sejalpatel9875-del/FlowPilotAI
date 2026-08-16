import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("flowpilot.workflow.decision_engine")


class DecisionResult(BaseModel):
    decision: str = Field(..., description="Decision enum: CONTINUE, WAIT_FOR_APPROVAL, REPLAN, COMPLETE, FAIL")
    reason: str = Field(..., description="Concise, safe structured explanation for the decision")
    suggested_action: Optional[str] = Field(None, description="Recommended next action or replan directive")
    confidence: float = Field(1.0, description="Decision confidence score [0.0 - 1.0]")
    requires_approval: bool = Field(False, description="Whether human authorization is required")


class DecisionEngine:
    """Controlled, deterministic decision layer evaluating agent outputs and steering DAG execution."""

    @classmethod
    def evaluate_step_output(
        cls,
        agent_name: str,
        action: str,
        output_data: Dict[str, Any],
        is_terminal_step: bool,
        is_side_effect: bool
    ) -> DecisionResult:
        """Evaluates normalized agent output and determines the next state machine transition."""
        output_text = str(output_data.get("output", "")).lower()

        # 1. Mandatory Human Approval for Side-Effecting Actions
        if is_side_effect or any(k in action.lower() for k in ["send", "dispatch", "delete", "archive"]):
            return DecisionResult(
                decision="WAIT_FOR_APPROVAL",
                reason=f"Step '{action}' by agent '{agent_name}' produces external state modifications requiring human verification.",
                suggested_action="Request human approval before dispatching external action.",
                requires_approval=True,
                confidence=1.0,
            )

        # 2. Agent Output Quality & Failure Signals
        if "error" in output_data or not output_data.get("output"):
            error_msg = output_data.get("error", "Agent returned empty response")
            return DecisionResult(
                decision="FAIL",
                reason=f"Agent '{agent_name}' execution produced an error: {error_msg}",
                suggested_action="Abort step or trigger bounded replan.",
                requires_approval=False,
                confidence=1.0,
            )

        # 3. Domain-Specific Decision Rules
        if agent_name == "LeadAgent":
            if "no leads found" in output_text or "0 leads" in output_text or "no pending leads" in output_text:
                return DecisionResult(
                    decision="CONTINUE",
                    reason="LeadAgent found 0 pending leads in database. Proceeding with synthesized pipeline analysis.",
                    suggested_action="Continue downstream cadence with available lead data.",
                    confidence=0.95,
                )
            return DecisionResult(
                decision="CONTINUE",
                reason="LeadAgent successfully identified and scored target leads.",
                suggested_action="Pass qualified lead context to FollowUpAgent.",
                confidence=1.0,
            )

        if agent_name == "FollowUpAgent":
            return DecisionResult(
                decision="CONTINUE",
                reason="FollowUpAgent successfully drafted personalized cadence messages.",
                suggested_action="Pass draft context to TimeManagementAgent for dispatch scheduling.",
                confidence=1.0,
            )

        if agent_name == "TimeManagementAgent":
            return DecisionResult(
                decision="CONTINUE" if not is_terminal_step else "COMPLETE",
                reason="TimeManagementAgent resolved optimal time slot and calendar recommendations.",
                suggested_action="Finalize schedule recommendations.",
                confidence=1.0,
            )

        # 4. Terminal Step Evaluation
        if is_terminal_step:
            return DecisionResult(
                decision="COMPLETE",
                reason=f"Terminal step '{action}' by '{agent_name}' completed successfully. All workflow goals satisfied.",
                suggested_action="Mark workflow as COMPLETED.",
                confidence=1.0,
            )

        # Default: Proceed to next step in DAG
        return DecisionResult(
            decision="CONTINUE",
            reason=f"Agent '{agent_name}' successfully executed '{action}'. Prerequisites for next node satisfied.",
            suggested_action="Advance topological DAG execution.",
            confidence=1.0,
        )

    @classmethod
    def evaluate_replan_viability(cls, replan_count: int, max_replans: int = 3) -> bool:
        """Guarantees that replanning remains strictly bounded to avoid infinite loops."""
        return replan_count < max_replans
