import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.outreach import OutreachMessageModel
from app.models.lead import LeadModel
from app.models.crm import LeadActivityModel
from app.models.governance import AuditLogModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.outreach")

VALID_CHANNELS = [
    "Email",
    "LinkedIn connection note",
    "Freelance proposal",
    "Contact form draft"
]

VALID_STATUSES = [
    "DRAFT",
    "REVIEW",
    "APPROVED",
    "SCHEDULED",
    "SENT",
    "FAILED",
    "CANCELLED"
]


class OutreachService:
    @staticmethod
    async def generate_draft(
        lead_id: str,
        channel: str,
        user_id: str,
        db: AsyncSession,
        custom_instructions: Optional[str] = None
    ) -> OutreachMessageModel:
        """Generates personalized outreach draft for a lead using OutreachAgent."""
        if channel not in VALID_CHANNELS:
            raise ValueError(f"Invalid channel '{channel}'. Allowed: {VALID_CHANNELS}")

        res = await db.execute(select(LeadModel).where(LeadModel.id == lead_id, LeadModel.is_deleted == False))
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError("Lead record not found.")

        # Build channel-specific prompt
        prompt = (
            f"Generate a personalized {channel} for client '{lead.company}' (Contact: {lead.name}, Industry: {lead.industry}). "
            f"Service Fit: {lead.service_fit}. Next Action: {lead.next_action}. "
            f"{'Instructions: ' + custom_instructions if custom_instructions else ''} "
            f"Maintain high professionalism. Do NOT include spammy hype."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="OutreachAgent"
        )
        draft_text = agent_res["outputText"]

        subject = f"Partnership Inquiry: FlowPilot AI x {lead.company}" if channel in ["Email", "Freelance proposal"] else None

        msg = OutreachMessageModel(
            lead_id=lead.id,
            user_id=user_id,
            channel=channel,
            subject=subject,
            draft_body=draft_text,
            status="REVIEW"  # Always goes to Human Approval Inbox
        )
        db.add(msg)

        # Audit Trail in lead_activities
        act = LeadActivityModel(
            lead_id=lead.id,
            activity_type="outreach_draft",
            description=f"Generated {channel} draft for human review.",
        )
        db.add(act)

        # Audit Trail in audit_logs
        audit = AuditLogModel(
            user_id=user_id,
            action=f"outreach_generated:{channel}",
            resource_type="outreach_message",
            resource_id=msg.id,
            ip_address="127.0.0.1",
            details=f"Generated {channel} draft for lead {lead.company}",
        )
        db.add(audit)

        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def update_status(
        message_id: str,
        new_status: str,
        user_id: str,
        db: AsyncSession,
        scheduled_time: Optional[datetime] = None
    ) -> OutreachMessageModel:
        """Handles human approval, rejection, scheduling, or sending with strict audit logging."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {VALID_STATUSES}")

        res = await db.execute(select(OutreachMessageModel).where(OutreachMessageModel.id == message_id))
        msg = res.scalar_one_or_none()
        if not msg:
            raise ValueError("Outreach message not found.")

        old_status = msg.status
        msg.status = new_status

        if new_status == "APPROVED":
            msg.approved_at = datetime.utcnow()
        elif new_status == "SCHEDULED":
            msg.scheduled_at = scheduled_time or datetime.utcnow()
        elif new_status == "SENT":
            msg.sent_at = datetime.utcnow()
            # Update lead pipeline stage to "Contacted"
            lead_res = await db.execute(select(LeadModel).where(LeadModel.id == msg.lead_id))
            lead = lead_res.scalar_one_or_none()
            if lead:
                lead.status = "Contacted"

        # Log activity
        act = LeadActivityModel(
            lead_id=msg.lead_id,
            activity_type="outreach_status_change",
            description=f"Outreach message ({msg.channel}) moved: '{old_status}' -> '{new_status}'.",
        )
        db.add(act)

        # Log audit entry
        audit = AuditLogModel(
            user_id=user_id,
            action=f"outreach_status:{new_status}",
            resource_type="outreach_message",
            resource_id=msg.id,
            ip_address="127.0.0.1",
            details=f"Updated outreach message state from {old_status} to {new_status}",
        )
        db.add(audit)

        await db.commit()
        await db.refresh(msg)
        return msg
