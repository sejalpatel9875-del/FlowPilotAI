import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("flowpilot.workflow.telemetry")


class WorkflowTelemetry:
    """Production telemetry recorder for Multi-Agent Workflow Orchestration."""

    _metrics = {
        "workflows_created": 0,
        "workflows_completed": 0,
        "workflows_failed": 0,
        "workflows_cancelled": 0,
        "approvals_requested": 0,
        "approvals_granted": 0,
        "approvals_rejected": 0,
        "replanning_attempts": 0,
        "side_effects_executed": 0,
        "agent_executions": {},
    }

    @classmethod
    def record_workflow_created(cls, workflow_id: str, user_id: str, goal: str):
        cls._metrics["workflows_created"] += 1
        logger.info(f"[TELEMETRY] Workflow created: id={workflow_id}, user={user_id}, goal_len={len(goal)}")

    @classmethod
    def record_workflow_completed(cls, workflow_id: str, total_duration_ms: int, total_steps: int):
        cls._metrics["workflows_completed"] += 1
        logger.info(f"[TELEMETRY] Workflow completed: id={workflow_id}, duration={total_duration_ms}ms, steps={total_steps}")

    @classmethod
    def record_workflow_failed(cls, workflow_id: str, error: str, completed_steps: int):
        cls._metrics["workflows_failed"] += 1
        logger.error(f"[TELEMETRY] Workflow failed: id={workflow_id}, error={error[:100]}, steps={completed_steps}")

    @classmethod
    def record_step_execution(cls, agent_name: str, action: str, latency_ms: int, success: bool):
        if agent_name not in cls._metrics["agent_executions"]:
            cls._metrics["agent_executions"][agent_name] = {"count": 0, "total_ms": 0, "failures": 0}
        cls._metrics["agent_executions"][agent_name]["count"] += 1
        cls._metrics["agent_executions"][agent_name]["total_ms"] += latency_ms
        if not success:
            cls._metrics["agent_executions"][agent_name]["failures"] += 1

    @classmethod
    def record_approval_event(cls, event_type: str, approval_id: str, workflow_id: str):
        if event_type == "REQUESTED":
            cls._metrics["approvals_requested"] += 1
        elif event_type == "GRANTED":
            cls._metrics["approvals_granted"] += 1
        elif event_type == "REJECTED":
            cls._metrics["approvals_rejected"] += 1
        logger.info(f"[TELEMETRY] Approval event: type={event_type}, id={approval_id}, workflow={workflow_id}")

    @classmethod
    def get_metrics_snapshot(cls) -> Dict[str, Any]:
        return dict(cls._metrics)
