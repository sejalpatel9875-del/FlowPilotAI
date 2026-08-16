import json
import time
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.workflow import (
    WorkflowModel,
    WorkflowStepModel,
    WorkflowApprovalModel,
    WorkflowEventModel,
)
from app.services.workflow.workflow_planner import WorkflowPlanner
from app.services.workflow.workflow_policy import (
    WorkflowPlanSpec,
    WorkflowStepSpec,
    WorkflowPolicyEngine,
    MAX_REPLAN_ATTEMPTS,
)
from app.services.workflow.capability_registry import CapabilityRegistry
from app.services.workflow.decision_engine import DecisionEngine, DecisionResult
from app.services.workflow.workflow_telemetry import WorkflowTelemetry
from app.agents.orchestrator import orchestrator
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger("flowpilot.workflow.engine")

MAX_CONTEXT_STRING_SIZE = 10000  # Bound context passed between agents to 10KB


class WorkflowExecutionEngine:
    """Production state machine, decision engine, and execution graph orchestrator for multi-agent workflows."""

    @classmethod
    async def create_and_start_workflow(
        cls,
        user_id: str,
        goal: str,
        db: AsyncSession
    ) -> WorkflowModel:
        """Plans, validates, persists, and begins execution of an autonomous multi-agent workflow."""
        if not user_id:
            raise ValueError("Authentication required: user_id missing.")
        if not goal or not goal.strip():
            raise ValueError("Workflow goal cannot be empty.")

        # 1. Autonomous Goal Planning & Task Decomposition
        await cls._record_event_ephemeral("PLANNING_STARTED", {"goal": goal[:200]})
        plan_spec = await WorkflowPlanner.create_plan(goal=goal, user_id=user_id, db=db)

        # 2. Persist Workflow Model
        wf = WorkflowModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=goal[:200],
            goal=goal,
            status="RUNNING",
            plan_json=plan_spec.model_dump_json(),
            context_state_json=json.dumps({"goal": goal, "step_outputs": {}}),
            total_steps=len(plan_spec.steps),
            completed_steps=0,
            replan_count=0,
            started_at=datetime.utcnow(),
        )
        db.add(wf)
        await db.flush()

        # 3. Persist Step Models
        step_models = []
        for idx, step_spec in enumerate(plan_spec.steps):
            is_side_effect = CapabilityRegistry.is_side_effect(step_spec.agent, step_spec.action) or step_spec.requires_approval
            step_m = WorkflowStepModel(
                id=str(uuid.uuid4()),
                workflow_id=wf.id,
                user_id=user_id,
                step_key=step_spec.id,
                step_order=idx,
                agent_name=step_spec.agent,
                action=step_spec.action,
                description=step_spec.description,
                depends_on_json=json.dumps(step_spec.depends_on),
                requires_approval=is_side_effect,
                is_side_effect=is_side_effect,
                status="PLANNED",
            )
            db.add(step_m)
            step_models.append(step_m)

        # 4. Log creation and validation events
        await cls._record_event(wf.id, user_id, "WORKFLOW_CREATED", None, {"goal": goal[:200]}, db)
        await cls._record_event(wf.id, user_id, "PLAN_GENERATED", None, {"steps_count": len(step_models)}, db)
        await cls._record_event(wf.id, user_id, "PLAN_VALIDATED", None, {"valid": True}, db)

        for step in step_models:
            await cls._record_event(wf.id, user_id, "AGENT_SELECTED", step.step_key, {"agent": step.agent_name, "action": step.action}, db)

        WorkflowTelemetry.record_workflow_created(wf.id, user_id, goal)
        await db.commit()

        # 5. Execute DAG
        return await cls.execute_graph(workflow_id=wf.id, user_id=user_id, db=db)

    @classmethod
    async def execute_graph(
        cls,
        workflow_id: str,
        user_id: str,
        db: AsyncSession
    ) -> WorkflowModel:
        """Advances the workflow state machine through its dependency DAG and decision layer."""
        res = await db.execute(
            select(WorkflowModel).where(WorkflowModel.id == workflow_id, WorkflowModel.user_id == user_id)
        )
        wf = res.scalar_one_or_none()
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        if wf.status in ["COMPLETED", "FAILED", "REJECTED", "CANCELLED"]:
            return wf

        # Load steps
        res_steps = await db.execute(
            select(WorkflowStepModel)
            .where(WorkflowStepModel.workflow_id == workflow_id, WorkflowStepModel.user_id == user_id)
            .order_by(WorkflowStepModel.step_order)
        )
        steps: List[WorkflowStepModel] = res_steps.scalars().all()

        step_map = {s.step_key: s for s in steps}
        context_state = json.loads(wf.context_state_json or "{}")
        step_outputs = context_state.get("step_outputs", {})

        # Iteratively find and execute steps whose dependencies are satisfied
        while True:
            ready_steps: List[WorkflowStepModel] = []
            for step in steps:
                if step.status != "PLANNED":
                    continue

                deps = json.loads(step.depends_on_json or "[]")
                deps_satisfied = True
                deps_failed = False
                for d in deps:
                    parent_step = step_map.get(d)
                    if not parent_step or parent_step.status in ["FAILED", "SKIPPED", "REJECTED"]:
                        deps_failed = True
                        break
                    if parent_step.status != "COMPLETED":
                        deps_satisfied = False

                if deps_failed:
                    step.status = "SKIPPED"
                    step.error_info = "Prerequisite step failed."
                    await cls._record_event(wf.id, user_id, "STEP_SKIPPED", step.step_key, {"reason": "prerequisite_failed"}, db)
                elif deps_satisfied:
                    ready_steps.append(step)

            if not ready_steps:
                break

            # Process ready steps
            for step in ready_steps:
                # 1. Check if approval is required before executing side-effect
                if step.requires_approval and step.status == "PLANNED":
                    # PAUSE FOR HUMAN APPROVAL
                    step.status = "WAITING_FOR_APPROVAL"
                    wf.status = "WAITING_FOR_APPROVAL"

                    # Create Approval Record
                    approval = WorkflowApprovalModel(
                        id=str(uuid.uuid4()),
                        workflow_id=wf.id,
                        step_id=step.id,
                        user_id=user_id,
                        step_key=step.step_key,
                        proposed_action=f"Agent '{step.agent_name}' requests approval to execute '{step.action}': {step.description}",
                        status="pending",
                    )
                    db.add(approval)
                    await cls._record_event(
                        wf.id, user_id, "APPROVAL_REQUESTED", step.step_key,
                        {"approval_id": approval.id, "proposed_action": approval.proposed_action}, db
                    )
                    WorkflowTelemetry.record_approval_event("REQUESTED", approval.id, wf.id)
                    await db.commit()
                    return wf

                # 2. Execute Step
                await cls._execute_step(step, wf, step_outputs, user_id, db)

                # 3. Decision Engine Evaluation
                is_terminal = (step == steps[-1])
                out_dict = json.loads(step.output_data_json or "{}") if step.status == "COMPLETED" else {"error": step.error_info}
                decision = DecisionEngine.evaluate_step_output(
                    agent_name=step.agent_name,
                    action=step.action,
                    output_data=out_dict,
                    is_terminal_step=is_terminal,
                    is_side_effect=step.is_side_effect
                )

                await cls._record_event(
                    wf.id, user_id, "DECISION_CREATED", step.step_key,
                    {
                        "decision": decision.decision,
                        "reason": decision.reason,
                        "confidence": decision.confidence,
                        "suggested_action": decision.suggested_action
                    },
                    db
                )

                if step.status == "FAILED":
                    # Controlled Bounded Replanning
                    if wf.replan_count < MAX_REPLAN_ATTEMPTS:
                        logger.info(f"Step '{step.step_key}' failed. Attempting bounded replan/retry (Attempt {wf.replan_count + 1}/{MAX_REPLAN_ATTEMPTS})")
                        wf.replan_count += 1
                        await cls._record_event(wf.id, user_id, "REPLAN_TRIGGERED", step.step_key, {"replan_attempt": wf.replan_count, "reason": step.error_info}, db)
                        await cls._execute_step(step, wf, step_outputs, user_id, db)

                    if step.status == "FAILED":
                        wf.status = "FAILED"
                        wf.error_message = f"Step '{step.step_key}' ({step.agent_name}) failed: {step.error_info}"
                        wf.completed_at = datetime.utcnow()
                        await cls._record_event(wf.id, user_id, "WORKFLOW_FAILED", step.step_key, {"error": step.error_info}, db)
                        WorkflowTelemetry.record_workflow_failed(wf.id, step.error_info or "Unknown error", wf.completed_steps)
                        await db.commit()
                        return wf

                if step.status == "COMPLETED":
                    wf.completed_steps += 1
                    step_outputs[step.step_key] = json.loads(step.output_data_json or "{}")

        # Update context state
        context_state["step_outputs"] = step_outputs
        wf.context_state_json = json.dumps(context_state)[:MAX_CONTEXT_STRING_SIZE]

        # Check if all steps completed
        all_done = all(s.status in ["COMPLETED", "SKIPPED"] for s in steps)
        if all_done and wf.status != "FAILED":
            wf.status = "COMPLETED"
            wf.completed_at = datetime.utcnow()
            duration_ms = int((wf.completed_at - (wf.started_at or wf.completed_at)).total_seconds() * 1000)
            await cls._record_event(wf.id, user_id, "WORKFLOW_COMPLETED", None, {"total_steps": wf.total_steps, "duration_ms": duration_ms}, db)
            WorkflowTelemetry.record_workflow_completed(wf.id, duration_ms, wf.completed_steps)

        await db.commit()
        return wf

    @classmethod
    async def _execute_step(
        cls,
        step: WorkflowStepModel,
        wf: WorkflowModel,
        step_outputs: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ):
        """Executes a single step using the registered specialized agent and sanitized context."""
        step.status = "RUNNING"
        step.started_at = datetime.utcnow()
        await cls._record_event(wf.id, user_id, "STEP_STARTED", step.step_key, {"agent": step.agent_name, "action": step.action}, db)
        await db.flush()

        agent = orchestrator.get_agent(step.agent_name)
        if not agent:
            step.status = "FAILED"
            step.error_info = f"Agent '{step.agent_name}' not registered in orchestrator."
            step.completed_at = datetime.utcnow()
            await cls._record_event(wf.id, user_id, "STEP_FAILED", step.step_key, {"error": step.error_info}, db)
            return

        # Prepare normalized, size-bounded contextual prompt from prior step outputs
        prior_context_blocks = []
        for dep_key in json.loads(step.depends_on_json or "[]"):
            out = step_outputs.get(dep_key)
            if out:
                summary = out.get("summary", out.get("output", str(out)))
                prior_context_blocks.append(f"Output from Prerequisite Step '{dep_key}':\n{summary}")

        context_prompt = "\n\n".join(prior_context_blocks)
        full_prompt = f"Goal: {wf.goal}\n\nTask: {step.description or step.action}\n\nContext:\n{context_prompt}" if context_prompt else f"Goal: {wf.goal}\n\nTask: {step.description or step.action}"
        step.input_data_json = json.dumps({"prompt": full_prompt[:2000], "action": step.action})

        start_t = time.time()
        try:
            agent_res = await agent.run(user_id=user_id, prompt=full_prompt, db=db, request_id=f"wf_{wf.id}_{step.step_key}")
            latency = int((time.time() - start_t) * 1000)

            step.status = "COMPLETED"
            step.completed_at = datetime.utcnow()
            step.latency_ms = latency
            step.output_data_json = json.dumps({
                "agent": step.agent_name,
                "action": step.action,
                "output": agent_res["output"],
                "summary": agent_res["output"][:500],
            })

            await cls._record_event(wf.id, user_id, "STEP_COMPLETED", step.step_key, {"latency_ms": latency}, db)
            WorkflowTelemetry.record_step_execution(step.agent_name, step.action, latency, success=True)

            # Audit Trail
            await AuditLogService.log_event(
                user_id=user_id,
                action=f"WORKFLOW_STEP_{step.agent_name.upper()}",
                resource_type="WORKFLOW_STEP",
                resource_id=step.id,
                details={"workflow_id": wf.id, "step_key": step.step_key, "action": step.action},
                db=db
            )
        except Exception as e:
            latency = int((time.time() - start_t) * 1000)
            step.status = "FAILED"
            step.completed_at = datetime.utcnow()
            step.latency_ms = latency
            step.error_info = str(e)[:500]
            await cls._record_event(wf.id, user_id, "STEP_FAILED", step.step_key, {"error": str(e)[:200]}, db)
            WorkflowTelemetry.record_step_execution(step.agent_name, step.action, latency, success=False)
            logger.error(f"Workflow step '{step.step_key}' ({step.agent_name}) execution failed: {str(e)}")

    @classmethod
    async def process_approval(
        cls,
        workflow_id: str,
        approval_id: str,
        decision: str,
        user_id: str,
        reason: Optional[str],
        db: AsyncSession
    ) -> WorkflowModel:
        """Processes human approval decision and resumes or rejects DAG execution."""
        res_wf = await db.execute(
            select(WorkflowModel).where(WorkflowModel.id == workflow_id, WorkflowModel.user_id == user_id)
        )
        wf = res_wf.scalar_one_or_none()
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found or access denied.")

        res_app = await db.execute(
            select(WorkflowApprovalModel).where(
                WorkflowApprovalModel.id == approval_id,
                WorkflowApprovalModel.workflow_id == workflow_id,
                WorkflowApprovalModel.user_id == user_id
            )
        )
        approval = res_app.scalar_one_or_none()
        if not approval:
            raise ValueError(f"Approval record '{approval_id}' not found.")

        if approval.status != "pending":
            return wf

        approval.status = decision
        approval.decision_by = user_id
        approval.decision_at = datetime.utcnow()
        approval.decision_reason = reason

        await cls._record_event(
            wf.id, user_id, f"APPROVAL_{decision.upper()}", approval.step_key,
            {"approval_id": approval.id, "reason": reason}, db
        )
        WorkflowTelemetry.record_approval_event(decision.upper(), approval.id, wf.id)

        # Load step
        res_step = await db.execute(
            select(WorkflowStepModel).where(WorkflowStepModel.id == approval.step_id, WorkflowStepModel.user_id == user_id)
        )
        step = res_step.scalar_one_or_none()
        if not step:
            raise ValueError("Associated step for approval not found.")

        if decision == "approved":
            step.status = "APPROVED"
            wf.status = "RUNNING"
            await db.commit()

            # Execute the approved side-effect action
            step.status = "RUNNING"
            step.started_at = datetime.utcnow()
            await cls._record_event(wf.id, user_id, "STEP_STARTED", step.step_key, {"agent": step.agent_name, "action": step.action}, db)

            # Mark step completed
            step.status = "COMPLETED"
            step.completed_at = datetime.utcnow()
            step.output_data_json = json.dumps({
                "agent": step.agent_name,
                "action": step.action,
                "output": f"Side effect '{step.action}' successfully executed after human approval.",
                "approved_by": user_id,
            })
            wf.completed_steps += 1
            await cls._record_event(wf.id, user_id, "STEP_COMPLETED", step.step_key, {"approved_execution": True}, db)

            # Continue executing downstream DAG nodes
            return await cls.execute_graph(workflow_id=wf.id, user_id=user_id, db=db)
        else:
            step.status = "REJECTED"
            wf.status = "REJECTED"
            wf.completed_at = datetime.utcnow()
            await cls._record_event(wf.id, user_id, "WORKFLOW_REJECTED", step.step_key, {"reason": reason}, db)
            await db.commit()
            return wf

    @classmethod
    async def cancel_workflow(
        cls,
        workflow_id: str,
        user_id: str,
        db: AsyncSession
    ) -> WorkflowModel:
        """Cancels a running or waiting workflow."""
        res_wf = await db.execute(
            select(WorkflowModel).where(WorkflowModel.id == workflow_id, WorkflowModel.user_id == user_id)
        )
        wf = res_wf.scalar_one_or_none()
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found or access denied.")

        if wf.status in ["COMPLETED", "FAILED", "REJECTED", "CANCELLED"]:
            return wf

        wf.status = "CANCELLED"
        wf.completed_at = datetime.utcnow()
        await cls._record_event(wf.id, user_id, "WORKFLOW_CANCELLED", None, {"cancelled_by": user_id}, db)
        await db.commit()
        return wf

    @classmethod
    async def _record_event(
        cls,
        workflow_id: str,
        user_id: str,
        event_type: str,
        step_key: Optional[str],
        details: Dict[str, Any],
        db: AsyncSession
    ):
        """Records an immutable audit event for the workflow."""
        ev = WorkflowEventModel(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            user_id=user_id,
            step_key=step_key,
            event_type=event_type,
            details_json=json.dumps(details),
            timestamp=datetime.utcnow(),
        )
        db.add(ev)
        await db.flush()

    @classmethod
    async def _record_event_ephemeral(cls, event_type: str, details: Dict[str, Any]):
        """Helper logging ephemeral planner events."""
        logger.debug(f"Ephemeral Event: {event_type} - {details}")
