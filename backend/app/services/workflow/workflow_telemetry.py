import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("flowpilot.workflow.telemetry")


class WorkflowTelemetry:
    """Production telemetry recorder for Multi-Agent Workflow Orchestration & Distributed Execution."""

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
        # Distributed execution & queue metrics
        "lease_acquisitions": 0,
        "lease_renewals": 0,
        "lease_failures": 0,
        "stale_worker_detections": 0,
        "jobs_enqueued": 0,
        "jobs_dequeued": 0,
        "jobs_retried": 0,
        "jobs_dlq": 0,
        "duplicate_deliveries": 0,
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
    def record_workflow_cancelled(cls, workflow_id: str, user_id: str):
        cls._metrics["workflows_cancelled"] += 1
        logger.info(f"[TELEMETRY] Workflow cancelled: id={workflow_id}, user={user_id}")

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
        if event_type in ["REQUESTED", "APPROVAL_REQUESTED"]:
            cls._metrics["approvals_requested"] += 1
        elif event_type in ["GRANTED", "APPROVED", "APPROVAL_GRANTED"]:
            cls._metrics["approvals_granted"] += 1
        elif event_type in ["REJECTED", "APPROVAL_REJECTED"]:
            cls._metrics["approvals_rejected"] += 1
        logger.info(f"[TELEMETRY] Approval event: type={event_type}, id={approval_id}, workflow={workflow_id}")

    @classmethod
    def record_side_effect_executed(cls, workflow_id: str, step_key: str, action: str):
        cls._metrics["side_effects_executed"] += 1
        logger.info(f"[TELEMETRY] Side effect executed: workflow={workflow_id}, step={step_key}, action={action}")

    # Distributed Execution Telemetry
    @classmethod
    def record_lease_acquired(cls, workflow_id: str, worker_id: str):
        cls._metrics["lease_acquisitions"] += 1
        logger.debug(f"[TELEMETRY] Lease acquired: wf={workflow_id}, worker={worker_id}")

    @classmethod
    def record_lease_renewed(cls, workflow_id: str, worker_id: str):
        cls._metrics["lease_renewals"] += 1
        logger.debug(f"[TELEMETRY] Lease renewed: wf={workflow_id}, worker={worker_id}")

    @classmethod
    def record_lease_failed(cls, workflow_id: str, worker_id: str, reason: str):
        cls._metrics["lease_failures"] += 1
        logger.warning(f"[TELEMETRY] Lease failed: wf={workflow_id}, worker={worker_id}, reason={reason}")

    @classmethod
    def record_stale_worker_fenced(cls, workflow_id: str, worker_id: str):
        cls._metrics["stale_worker_detections"] += 1
        logger.error(f"[TELEMETRY] Stale worker fenced: wf={workflow_id}, worker={worker_id}")

    @classmethod
    def record_job_enqueued(cls, workflow_id: str, job_id: str):
        cls._metrics["jobs_enqueued"] += 1
        logger.debug(f"[TELEMETRY] Job enqueued: wf={workflow_id}, job={job_id}")

    @classmethod
    def record_job_dequeued(cls, workflow_id: str, job_id: str):
        cls._metrics["jobs_dequeued"] += 1
        logger.debug(f"[TELEMETRY] Job dequeued: wf={workflow_id}, job={job_id}")

    @classmethod
    def record_job_retried(cls, workflow_id: str, job_id: str, retry_count: int):
        cls._metrics["jobs_retried"] += 1
        logger.warning(f"[TELEMETRY] Job retried: wf={workflow_id}, job={job_id}, count={retry_count}")

    @classmethod
    def record_job_dlq(cls, workflow_id: str, job_id: str, retry_count: int):
        cls._metrics["jobs_dlq"] += 1
        logger.error(f"[TELEMETRY] Job moved to DLQ: wf={workflow_id}, job={job_id}, retries={retry_count}")

    @classmethod
    def record_duplicate_delivery(cls, workflow_id: str, job_id: str):
        cls._metrics["duplicate_deliveries"] += 1
        logger.warning(f"[TELEMETRY] Duplicate job delivery detected: wf={workflow_id}, job={job_id}")

    @classmethod
    def get_metrics_snapshot(cls) -> Dict[str, Any]:
        return dict(cls._metrics)
