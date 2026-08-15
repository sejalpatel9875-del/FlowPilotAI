import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.invitation import InvitationModel
from app.models.lead import LeadModel
from app.models.governance import AuditLogModel
logger = logging.getLogger("flowpilot.invitation")

class InvitationService:
    @staticmethod
    async def create_invitation(
        user_id: str, 
        title: str, 
        recipient_name: str, 
        recipient_email: str, 
        invitation_type: str, 
        description: Optional[str], 
        scheduled_at: Optional[datetime], 
        location: Optional[str], 
        meeting_link: Optional[str], 
        db: AsyncSession
    ) -> InvitationModel:
        invitation = InvitationModel(
            user_id=user_id,
            title=title,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            invitation_type=invitation_type,
            description=description,
            scheduled_at=scheduled_at,
            location=location,
            meeting_link=meeting_link,
            status="draft"
        )
        db.add(invitation)
        
        audit = AuditLogModel(
            user_id=user_id,
            action="invitation_created",
            resource_type="invitation",
            resource_id=invitation.id,
            ip_address="127.0.0.1",
            details=f"Created {invitation_type} invitation for {recipient_email}"
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(invitation)
        return invitation

    @staticmethod
    async def list_invitations(user_id: str, status_filter: Optional[str], db: AsyncSession) -> List[InvitationModel]:
        query = select(InvitationModel).where(InvitationModel.user_id == user_id, InvitationModel.is_deleted == False)
        if status_filter:
            query = query.where(InvitationModel.status == status_filter)
        query = query.order_by(InvitationModel.created_at.desc())
        res = await db.execute(query)
        return list(res.scalars().all())

    @staticmethod
    async def get_invitation(user_id: str, invitation_id: str, db: AsyncSession) -> InvitationModel:
        res = await db.execute(
            select(InvitationModel).where(
                InvitationModel.id == invitation_id, 
                InvitationModel.user_id == user_id,
                InvitationModel.is_deleted == False
            )
        )
        inv = res.scalar_one_or_none()
        if not inv:
            raise ValueError("Invitation not found")
        return inv

    @staticmethod
    async def update_invitation(user_id: str, invitation_id: str, updates_dict: Dict[str, Any], db: AsyncSession) -> InvitationModel:
        inv = await InvitationService.get_invitation(user_id, invitation_id, db)
        for key, value in updates_dict.items():
            if hasattr(inv, key):
                setattr(inv, key, value)
                
        audit = AuditLogModel(
            user_id=user_id,
            action="invitation_updated",
            resource_type="invitation",
            resource_id=inv.id,
            ip_address="127.0.0.1",
            details=f"Updated invitation fields: {list(updates_dict.keys())}"
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(inv)
        return inv

    @staticmethod
    async def update_status(user_id: str, invitation_id: str, new_status: str, db: AsyncSession) -> InvitationModel:
        inv = await InvitationService.get_invitation(user_id, invitation_id, db)
        old_status = inv.status
        inv.status = new_status
        
        audit = AuditLogModel(
            user_id=user_id,
            action=f"invitation_status:{new_status}",
            resource_type="invitation",
            resource_id=inv.id,
            ip_address="127.0.0.1",
            details=f"Status changed from {old_status} to {new_status}"
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(inv)
        return inv

    @staticmethod
    async def generate_ai_invitation(user_id: str, lead_id: str, invitation_type: str, prompt: str, db: AsyncSession) -> InvitationModel:
        res = await db.execute(select(LeadModel).where(LeadModel.id == lead_id, LeadModel.is_deleted == False))
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError("Lead not found")

        full_prompt = f"Generate a {invitation_type} invitation for {lead.name} at {lead.company}. Additional instructions: {prompt}"

        from app.agents.orchestrator import orchestrator
        agent_res = await orchestrator.execute_request(
            user_id=user_id,
            prompt=full_prompt,
            db=db,
            target_agent_name="InvitationAgent"
        )
        draft_text = agent_res.get("finalResponse", "")

        invitation = InvitationModel(
            user_id=user_id,
            lead_id=lead_id,
            title=f"AI Generated {invitation_type.replace('_', ' ').title()} Invitation",
            recipient_name=lead.name,
            recipient_email=lead.email,
            invitation_type=invitation_type,
            message_body=draft_text,
            status="draft"
        )
        db.add(invitation)

        audit = AuditLogModel(
            user_id=user_id,
            action="invitation_ai_generated",
            resource_type="invitation",
            resource_id=invitation.id,
            ip_address="127.0.0.1",
            details=f"AI generated {invitation_type} invitation for lead {lead.id}"
        )
        db.add(audit)

        await db.commit()
        await db.refresh(invitation)
        return invitation
