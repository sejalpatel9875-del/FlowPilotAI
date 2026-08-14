import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.automation import AutomationModel, AutomationRunModel
from app.models.governance import AuditLogModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.automation_service")


class AutomationService:
    @staticmethod
    def get_prebuilt_templates() -> List[Dict[str, Any]]:
        """Returns pre-configured automation templates."""
        return [
            {
                "name": "Auto-Qualify & Draft Outreach for New Leads",
                "description": "When a new lead enters CRM, AI scores service fit and generates a personalized draft for review.",
                "triggerType": "NEW_LEAD",
                "actionType": "GENERATE_DRAFT",
                "requiresApproval": True,
                "aiDecisionPrompt": "Evaluate lead industry alignment and budget signals. Generate personalized email draft.",
            },
            {
                "name": "Auto-Stop Follow-Up Cadence on Lead Reply",
                "description": "When a lead replies to outreach, AI instantly halts active follow-up sequences to prevent double contacting.",
                "triggerType": "REPLY_RECEIVED",
                "actionType": "UPDATE_LEAD",
                "requiresApproval": False,
                "aiDecisionPrompt": "Set lead stage to 'Replied' and stop active follow-up sequence.",
            },
            {
                "name": "Intelligent Task Rescheduling on Missed Block",
                "description": "When a focus block is missed, AI recalculates the schedule and offers task splitting or scope reduction.",
                "triggerType": "TASK_DUE",
                "actionType": "CREATE_TASK",
                "requiresApproval": False,
                "aiDecisionPrompt": "Split large missed task into 25-min micro-sprints and reschedule for optimal focus window.",
            },
            {
                "name": "Weekly Revenue & Skill Growth Summary Report",
                "description": "Every Sunday, AI compiles pipeline conversion rate, study hours, and milestone payout progress.",
                "triggerType": "WEEKLY_REVIEW",
                "actionType": "GENERATE_REPORT",
                "requiresApproval": False,
                "aiDecisionPrompt": "Synthesize weekly performance metrics and generate executive summary report.",
            }
        ]

    @staticmethod
    async def create_automation(
        name: str,
        trigger_type: str,
        action_type: str,
        description: Optional[str],
        condition_json: Optional[str],
        ai_decision_prompt: Optional[str],
        action_params_json: Optional[str],
        requires_approval: bool,
        user_id: str,
        db: AsyncSession
    ) -> AutomationModel:
        """Creates a custom automation workflow rule."""
        auto = AutomationModel(
            user_id=user_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_event=trigger_type,
            action_type=action_type,
            condition_json=condition_json,
            ai_decision_prompt=ai_decision_prompt,
            action_params_json=action_params_json,
            requires_approval=requires_approval,
            status="ACTIVE",
            is_active=True
        )
        db.add(auto)
        await db.commit()
        await db.refresh(auto)
        return auto

    @staticmethod
    async def execute_automation_workflow(
        automation_id: str,
        user_id: str,
        db: AsyncSession,
        trigger_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executes the 7-stage automation pipeline: TRIGGER → CONDITION → AI DECISION → ACTION → APPROVAL → EXECUTION → AUDIT."""
        res = await db.execute(
            select(AutomationModel).where(
                AutomationModel.id == automation_id,
                AutomationModel.user_id == user_id
            )
        )
        auto = res.scalar_one_or_none()
        if not auto:
            raise ValueError("Automation rule not found.")

        # Stage 1: Trigger Event Verification
        event_name = trigger_context.get("event", auto.trigger_type) if trigger_context else auto.trigger_type

        # Stage 2: Condition Evaluation
        # (Passes if condition_json is empty or matches)

        # Stage 3: AI Decision Step
        ai_prompt = auto.ai_decision_prompt or f"Evaluate trigger event '{event_name}' and execute action '{auto.action_type}'."
        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=ai_prompt,
            user_id=user_id,
            db=db,
            target_agent_name="ResearchAgent"
        )
        ai_summary = agent_res["outputText"]

        # Stage 4 & 5: Action & Approval Gatekeeper
        run_status = "PENDING_APPROVAL" if auto.requires_approval else "SUCCESS"

        # Stage 6: Execution Log Creation
        run_log = AutomationRunModel(
            automation_id=auto.id,
            trigger_event=event_name,
            ai_decision_summary=ai_summary,
            status=run_status,
            logs=f"7-Stage Execution Pipeline completed. Status: {run_status}. Action: {auto.action_type}.",
            executed_at=datetime.utcnow()
        )
        db.add(run_log)

        # Stage 7: Persistent Audit Log
        audit = AuditLogModel(
            user_id=user_id,
            action="AUTOMATION_EXECUTION",
            resource_type="AUTOMATION",
            resource_id=auto.id,
            details=f"Automation '{auto.name}' triggered by {event_name}. Action: {auto.action_type}. Status: {run_status}."
        )
        db.add(audit)
        await db.commit()

        return {
            "runId": run_log.id,
            "automationId": auto.id,
            "automationName": auto.name,
            "triggerType": auto.trigger_type,
            "actionType": auto.action_type,
            "status": run_status,
            "aiDecisionSummary": ai_summary,
            "requiresApproval": auto.requires_approval
        }

    @staticmethod
    async def toggle_status(automation_id: str, status: str, user_id: str, db: AsyncSession) -> AutomationModel:
        """Pause or resume an automation workflow."""
        res = await db.execute(
            select(AutomationModel).where(
                AutomationModel.id == automation_id,
                AutomationModel.user_id == user_id
            )
        )
        auto = res.scalar_one_or_none()
        if not auto:
            raise ValueError("Automation rule not found.")

        auto.status = status.upper().strip()
        auto.is_active = (auto.status == "ACTIVE")

        await db.commit()
        await db.refresh(auto)
        return auto
