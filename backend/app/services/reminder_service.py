import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reminder import ReminderModel
from app.models.governance import AuditLogModel

logger = logging.getLogger("flowpilot.reminder")


class ReminderService:

    @staticmethod
    async def create_reminder(
        user_id: str,
        title: str,
        remind_at: datetime,
        db: AsyncSession,
        description: Optional[str] = None,
        priority: str = "medium",
        linked_lead_id: Optional[str] = None,
        linked_project_id: Optional[str] = None,
        recurrence: Optional[str] = None,
    ) -> ReminderModel:
        reminder = ReminderModel(
            user_id=user_id,
            title=title,
            remind_at=remind_at,
            description=description,
            priority=priority,
            linked_lead_id=linked_lead_id,
            linked_project_id=linked_project_id,
            recurrence=recurrence,
            status="active"
        )
        db.add(reminder)

        audit = AuditLogModel(
            user_id=user_id,
            action="REMINDER_CREATED",
            resource_type="reminder",
            resource_id=reminder.id,
            ip_address="127.0.0.1",
            details=f"Created reminder: {title}"
        )
        db.add(audit)

        await db.commit()
        await db.refresh(reminder)
        return reminder

    @staticmethod
    async def list_reminders(user_id: str, status_filter: Optional[str], db: AsyncSession) -> List[ReminderModel]:
        query = select(ReminderModel).where(
            ReminderModel.user_id == user_id,
            ReminderModel.is_deleted == False
        )
        now = datetime.utcnow()
        if status_filter == "due_today":
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            query = query.where(
                ReminderModel.remind_at >= today_start,
                ReminderModel.remind_at < today_end,
                ReminderModel.status == "active"
            )
        elif status_filter == "upcoming":
            query = query.where(ReminderModel.remind_at > now, ReminderModel.status == "active")
        elif status_filter in ("completed", "snoozed", "active", "dismissed"):
            query = query.where(ReminderModel.status == status_filter)

        query = query.order_by(ReminderModel.remind_at.asc())
        res = await db.execute(query)
        return list(res.scalars().all())

    @staticmethod
    async def get_reminder(user_id: str, reminder_id: str, db: AsyncSession) -> ReminderModel:
        res = await db.execute(
            select(ReminderModel).where(
                ReminderModel.id == reminder_id,
                ReminderModel.user_id == user_id,
                ReminderModel.is_deleted == False
            )
        )
        reminder = res.scalar_one_or_none()
        if not reminder:
            raise ValueError("Reminder not found")
        return reminder

    @staticmethod
    async def get_due_reminders(user_id: str, db: AsyncSession) -> List[ReminderModel]:
        now = datetime.utcnow()
        res = await db.execute(
            select(ReminderModel).where(
                ReminderModel.user_id == user_id,
                ReminderModel.remind_at <= now,
                ReminderModel.status == "active",
                ReminderModel.is_deleted == False
            ).order_by(ReminderModel.remind_at.asc())
        )
        return list(res.scalars().all())

    @staticmethod
    async def snooze_reminder(user_id: str, reminder_id: str, snooze_until: datetime, db: AsyncSession) -> ReminderModel:
        reminder = await ReminderService.get_reminder(user_id, reminder_id, db)
        reminder.status = "snoozed"
        reminder.snoozed_until = snooze_until

        audit = AuditLogModel(
            user_id=user_id,
            action="REMINDER_SNOOZED",
            resource_type="reminder",
            resource_id=reminder.id,
            ip_address="127.0.0.1",
            details=f"Snoozed until {snooze_until.isoformat()}"
        )
        db.add(audit)

        await db.commit()
        await db.refresh(reminder)
        return reminder

    @staticmethod
    async def complete_reminder(user_id: str, reminder_id: str, db: AsyncSession) -> ReminderModel:
        reminder = await ReminderService.get_reminder(user_id, reminder_id, db)
        reminder.status = "completed"

        audit = AuditLogModel(
            user_id=user_id,
            action="REMINDER_COMPLETED",
            resource_type="reminder",
            resource_id=reminder.id,
            ip_address="127.0.0.1",
            details=f"Completed reminder: {reminder.title}"
        )
        db.add(audit)

        await db.commit()
        await db.refresh(reminder)
        return reminder

    @staticmethod
    async def dismiss_reminder(user_id: str, reminder_id: str, db: AsyncSession) -> ReminderModel:
        reminder = await ReminderService.get_reminder(user_id, reminder_id, db)
        reminder.status = "dismissed"

        audit = AuditLogModel(
            user_id=user_id,
            action="REMINDER_DISMISSED",
            resource_type="reminder",
            resource_id=reminder.id,
            ip_address="127.0.0.1",
            details=f"Dismissed reminder: {reminder.title}"
        )
        db.add(audit)

        await db.commit()
        await db.refresh(reminder)
        return reminder

    @staticmethod
    async def generate_smart_reminders(user_id: str, prompt: str, db: AsyncSession) -> Dict[str, Any]:
        """Call ReminderAgent via orchestrator to suggest intelligent reminders."""
        from app.agents.orchestrator import orchestrator

        result = await orchestrator.execute_request(
            user_id=user_id,
            prompt=f"Suggest smart reminders based on my pipeline: {prompt}",
            db=db,
            target_agent_name="ReminderAgent"
        )
        return {
            "suggestions": result.get("finalResponse", ""),
            "agentsExecuted": result.get("agentsExecuted", [])
        }
