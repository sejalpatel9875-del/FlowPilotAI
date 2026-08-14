import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.follow_up import FollowUpSequenceModel, FollowUpModel, FollowUpExecutionModel
from app.models.lead import LeadModel
from app.models.crm import LeadActivityModel
from app.models.governance import AuditLogModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.follow_up")

STOP_STAGES = [
    "Replied",
    "Meeting",
    "Proposal",
    "Won",
    "Lost",
    "Not Interested"
]

CADENCE_STEPS = [
    {"step": 1, "delay_days": 3, "label": "Follow-Up 1 (3 Days)"},
    {"step": 2, "delay_days": 7, "label": "Follow-Up 2 (7 Days)"},
    {"step": 3, "delay_days": 14, "label": "Final Follow-Up (14 Days)"},
]


class FollowUpService:
    @staticmethod
    async def start_sequence(
        lead_id: str,
        user_id: str,
        db: AsyncSession
    ) -> FollowUpSequenceModel:
        """Starts standard 3-step follow-up sequence for a lead (3d, 7d, 14d)."""
        res = await db.execute(select(LeadModel).where(LeadModel.id == lead_id, LeadModel.is_deleted == False))
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError("Lead record not found.")

        # Check if stop condition already active
        if lead.status in STOP_STAGES:
            raise ValueError(f"Cannot start follow-up sequence. Lead is already in '{lead.status}' stage.")

        # Create Sequence Record
        seq = FollowUpSequenceModel(
            lead_id=lead.id,
            user_id=user_id,
            name=f"Cadence: {lead.company}",
            status="ACTIVE",
            current_step=1
        )
        db.add(seq)
        await db.flush()

        # Create 3 Sequence Steps
        now = datetime.utcnow()
        cumulative_days = 0

        for item in CADENCE_STEPS:
            cumulative_days += item["delay_days"]
            due_dt = now + timedelta(days=cumulative_days)

            fu = FollowUpModel(
                sequence_id=seq.id,
                step_number=item["step"],
                delay_days=item["delay_days"],
                due_date=due_dt,
                status="UPCOMING",
            )
            db.add(fu)

        # Log Activity
        act = LeadActivityModel(
            lead_id=lead.id,
            activity_type="followup_sequence_started",
            description=f"Initialized 3-step follow-up sequence (3d -> 7d -> 14d).",
        )
        db.add(act)

        await db.commit()
        await db.refresh(seq)
        return seq

    @staticmethod
    async def check_and_apply_stop_conditions(
        lead_id: str,
        db: AsyncSession
    ) -> bool:
        """Evaluates if lead stage meets stop condition and updates active sequences to STOPPED."""
        lead_res = await db.execute(select(LeadModel).where(LeadModel.id == lead_id))
        lead = lead_res.scalar_one_or_none()
        if not lead or lead.status not in STOP_STAGES:
            return False

        seq_res = await db.execute(
            select(FollowUpSequenceModel)
            .options(selectinload(FollowUpSequenceModel.follow_ups))
            .where(
                FollowUpSequenceModel.lead_id == lead_id,
                FollowUpSequenceModel.status == "ACTIVE"
            )
        )
        active_seqs = seq_res.scalars().all()

        for seq in active_seqs:
            seq.status = "STOPPED"
            for fu in seq.follow_ups:
                if fu.status in ["DUE", "UPCOMING", "WAITING"]:
                    fu.status = "STOPPED"

            # Log activity
            act = LeadActivityModel(
                lead_id=lead.id,
                activity_type="followup_sequence_stopped",
                description=f"Follow-up sequence automatically STOPPED due to stage change to '{lead.status}'.",
            )
            db.add(act)

        await db.commit()
        return len(active_seqs) > 0

    @staticmethod
    async def explain_why_followup(
        followup_id: str,
        user_id: str,
        db: AsyncSession
    ) -> str:
        """Uses FollowUpAgent to explain why follow-up is recommended."""
        res = await db.execute(
            select(FollowUpModel)
            .options(selectinload(FollowUpModel.sequence).selectinload(FollowUpSequenceModel.lead))
            .where(FollowUpModel.id == followup_id)
        )
        fu = res.scalar_one_or_none()
        if not fu or not fu.sequence or not fu.sequence.lead:
            raise ValueError("Follow-up item not found.")

        lead = fu.sequence.lead
        prompt = (
            f"Analyze why I should follow up with lead '{lead.company}' (Industry: {lead.industry}, Current Stage: {lead.status}, Step {fu.step_number}). "
            f"Provide a concise, 2-sentence explanation highlighting timing, value proposition, and conversion likelihood."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="FollowUpAgent"
        )

        explanation = agent_res["outputText"]
        fu.ai_reasoning = explanation

        # Audit Execution
        exec_model = FollowUpExecutionModel(
            followup_id=fu.id,
            executed_by="FollowUpAgent",
            action="explain_why_followup",
            outcome=explanation
        )
        db.add(exec_model)

        await db.commit()
        return explanation

    @staticmethod
    async def generate_followup_draft(
        followup_id: str,
        user_id: str,
        db: AsyncSession
    ) -> str:
        """Generates tailored follow-up draft using FollowUpAgent."""
        res = await db.execute(
            select(FollowUpModel)
            .options(selectinload(FollowUpModel.sequence).selectinload(FollowUpSequenceModel.lead))
            .where(FollowUpModel.id == followup_id)
        )
        fu = res.scalar_one_or_none()
        if not fu or not fu.sequence or not fu.sequence.lead:
            raise ValueError("Follow-up item not found.")

        lead = fu.sequence.lead
        prompt = (
            f"Draft a polite, highly effective Step {fu.step_number} follow-up email for '{lead.name}' at '{lead.company}'. "
            f"Industry: {lead.industry}. Keep it concise and focused on offering value."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="FollowUpAgent"
        )

        draft_text = agent_res["outputText"]
        fu.draft_body = draft_text

        exec_model = FollowUpExecutionModel(
            followup_id=fu.id,
            executed_by="FollowUpAgent",
            action="generate_draft",
            outcome=f"Generated draft for Step {fu.step_number}"
        )
        db.add(exec_model)

        await db.commit()
        return draft_text
