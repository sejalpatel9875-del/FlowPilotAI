from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve authenticated user's projects."""
    return await ProjectService.get_all_projects(user.id, db)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create project scoped strictly to authenticated user."""
    return await ProjectService.create_project(project_in, user.id, db)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve single project by ID with strict ownership check."""
    proj = await ProjectService.get_project_by_id(project_id, user.id, db)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized.")
    return proj


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete project with strict ownership check."""
    success = await ProjectService.delete_project(project_id, user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized.")
    return {"status": "success", "message": "Project deleted successfully."}
