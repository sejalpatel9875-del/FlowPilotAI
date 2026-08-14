from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.schemas.command import CommandPromptRequest, CommandPromptResponse
from app.services.command_service import CommandService

router = APIRouter()


class ActionOutcomeRequest(BaseModel):
    action: str = Field(..., description="ACCEPT, DISMISS, RESCHEDULE, or START_FOCUS")


@router.post("/process", response_model=CommandPromptResponse)
async def process_command(
    request: CommandPromptRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")

    return await CommandService.process_prompt(request, user.id, db)


@router.post("/what-should-i-do-next")
async def trigger_what_should_i_do_next(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyzes real data across 8 modules (Tasks, Deadlines, Leads, Follow-ups, Projects, Goals, Learning, Available time), ranks actions via 6-Factor Matrix, and returns Top 3 Actions."""
    try:
        recs = await CommandService.analyze_what_should_i_do_next(user.id, db)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation analysis failed: {str(e)}")


@router.post("/recommendations/{recommendation_id}/action")
async def apply_recommendation_action(
    recommendation_id: str,
    req: ActionOutcomeRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply user action (ACCEPT, DISMISS, RESCHEDULE, START_FOCUS) and store outcome analytics."""
    try:
        res = await CommandService.record_recommendation_action(recommendation_id, req.action, user.id, db)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
