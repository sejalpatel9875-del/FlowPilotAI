from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent import AgentActivityModel
from app.schemas.agent import AgentActivityCreate, AgentActivityResponse


class AgentService:
    @staticmethod
    async def get_all_activities(db: AsyncSession) -> List[AgentActivityResponse]:
        result = await db.execute(select(AgentActivityModel).order_by(AgentActivityModel.created_at.desc()))
        activities = result.scalars().all()
        return [
            AgentActivityResponse(
                id=a.id,
                agentId=a.agent_id,
                agentName=a.agent_name,
                action=a.action,
                status=a.status,
                details=a.details,
                requiresApproval=a.requires_approval,
                timestamp=a.timestamp,
            )
            for a in activities
        ]

    @staticmethod
    async def create_activity(activity_in: AgentActivityCreate, db: AsyncSession) -> AgentActivityResponse:
        a = AgentActivityModel(
            agent_id=activity_in.agentId,
            agent_name=activity_in.agentName,
            action=activity_in.action,
            status=activity_in.status,
            details=activity_in.details,
            requires_approval=activity_in.requiresApproval,
            timestamp=activity_in.timestamp,
        )
        db.add(a)
        await db.commit()
        await db.refresh(a)
        return AgentActivityResponse(
            id=a.id,
            agentId=a.agent_id,
            agentName=a.agent_name,
            action=a.action,
            status=a.status,
            details=a.details,
            requiresApproval=a.requires_approval,
            timestamp=a.timestamp,
        )

    @staticmethod
    async def approve_activity(activity_id: str, db: AsyncSession) -> bool:
        result = await db.execute(select(AgentActivityModel).where(AgentActivityModel.id == activity_id))
        activity = result.scalar_one_or_none()
        if not activity:
            return False

        activity.status = "completed"
        activity.requires_approval = False
        activity.details = "Human approval granted. Action executed successfully."
        await db.commit()
        return True
