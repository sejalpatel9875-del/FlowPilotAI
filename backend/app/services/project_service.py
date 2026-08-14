from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import ProjectModel
from app.schemas.project import ProjectCreate, ProjectResponse


class ProjectService:
    @staticmethod
    async def get_all_projects(user_id: str, db: AsyncSession) -> List[ProjectResponse]:
        """List authenticated user's projects."""
        result = await db.execute(
            select(ProjectModel).where(
                ProjectModel.user_id == user_id,
                ProjectModel.is_deleted == False
            ).order_by(ProjectModel.created_at.desc())
        )
        projects = result.scalars().all()
        return [
            ProjectResponse(
                id=p.id,
                title=p.title,
                clientName=p.client_name,
                status=p.status,
                deadline=p.deadline,
                progressPercent=p.progress_percent,
                hourlyRate=p.hourly_rate,
            )
            for p in projects
        ]

    @staticmethod
    async def create_project(project_in: ProjectCreate, user_id: str, db: AsyncSession) -> ProjectResponse:
        """Create project scoped to authenticated user."""
        p = ProjectModel(
            user_id=user_id,
            title=project_in.title,
            client_name=project_in.clientName,
            status=project_in.status,
            deadline=project_in.deadline,
            progress_percent=project_in.progressPercent,
            hourly_rate=project_in.hourlyRate,
        )
        db.add(p)
        await db.commit()
        await db.refresh(p)
        return ProjectResponse(
            id=p.id,
            title=p.title,
            clientName=p.client_name,
            status=p.status,
            deadline=p.deadline,
            progressPercent=p.progress_percent,
            hourlyRate=p.hourly_rate,
        )

    @staticmethod
    async def get_project_by_id(project_id: str, user_id: str, db: AsyncSession) -> Optional[ProjectResponse]:
        """Retrieve project by ID with user ownership check."""
        result = await db.execute(
            select(ProjectModel).where(
                ProjectModel.id == project_id,
                ProjectModel.user_id == user_id,
                ProjectModel.is_deleted == False
            )
        )
        p = result.scalar_one_or_none()
        if not p:
            return None
        return ProjectResponse(
            id=p.id,
            title=p.title,
            clientName=p.client_name,
            status=p.status,
            deadline=p.deadline,
            progressPercent=p.progress_percent,
            hourlyRate=p.hourly_rate,
        )

    @staticmethod
    async def delete_project(project_id: str, user_id: str, db: AsyncSession) -> bool:
        """Soft delete project with user ownership check."""
        result = await db.execute(
            select(ProjectModel).where(
                ProjectModel.id == project_id,
                ProjectModel.user_id == user_id,
                ProjectModel.is_deleted == False
            )
        )
        p = result.scalar_one_or_none()
        if not p:
            return False
        p.is_deleted = True
        await db.commit()
        return True
