import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.models.learning import SkillModel
from app.services.learning_service import LearningService

router = APIRouter()


class CreateSkillGoalRequest(BaseModel):
    name: str = Field(..., description="Skill name (e.g. FastAPI System Architecture)")
    currentLevel: str = Field(default="Beginner", description="Beginner, Intermediate, or Advanced")
    targetLevel: str = Field(default="Advanced", description="Intermediate, Advanced, or Expert")
    deadline: Optional[str] = Field(None, description="ISO target date string")
    weeklyHours: int = Field(default=5, description="Weekly study hours budget")


class LogHoursRequest(BaseModel):
    hours: float = Field(..., description="Study hours spent")


class SubmitAssessmentRequest(BaseModel):
    scorePercent: float = Field(..., description="Assessment score % achieved")


@router.get("")
async def list_skills_and_learning_dashboard(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve Learning Dashboard summary, skill roadmaps, and progress analytics."""
    res = await db.execute(select(SkillModel).where(SkillModel.user_id == user.id))
    skills = res.scalars().all()

    total_logged_hours = sum(s.logged_hours for s in skills)
    avg_progress = (sum(s.progress_percent for s in skills) / len(skills)) if skills else 0.0
    avg_score = (sum(s.assessment_score for s in skills) / len(skills)) if skills else 85.0

    return {
        "dashboardMetrics": {
            "activeSkillGoals": len(skills),
            "totalStudyHours": round(total_logged_hours, 1),
            "avgAssessmentScore": round(avg_score, 1),
            "overallProgressPercent": round(avg_progress, 1),
        },
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "currentLevel": s.current_level,
                "targetLevel": s.target_level,
                "deadline": s.deadline.strftime("%Y-%m-%d") if s.deadline else None,
                "weeklyHours": s.weekly_hours,
                "progressPercent": round(s.progress_percent, 1),
                "loggedHours": round(s.logged_hours, 1),
                "assessmentScore": round(s.assessment_score, 1),
                "curriculum": json.loads(s.curriculum_json) if s.curriculum_json else {},
            }
            for s in skills
        ]
    }


@router.post("/skills")
async def create_skill_goal(
    req: CreateSkillGoalRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create skill goal and trigger LearningAgent to generate AI roadmap."""
    try:
        skill = await LearningService.create_skill_roadmap(
            name=req.name,
            current_level=req.currentLevel,
            target_level=req.targetLevel,
            deadline_str=req.deadline,
            weekly_hours=req.weeklyHours,
            user_id=user.id,
            db=db
        )
        return {
            "id": skill.id,
            "name": skill.name,
            "currentLevel": skill.current_level,
            "targetLevel": skill.target_level,
            "progressPercent": skill.progress_percent,
            "curriculum": json.loads(skill.curriculum_json) if skill.curriculum_json else {},
            "message": "AI Learning Roadmap generated and connected to real client projects."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill roadmap creation failed: {str(e)}")


@router.post("/recommend")
async def recommend_next_skills(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI Skill Recommender: 'What should I learn next?'."""
    try:
        recs = await LearningService.recommend_skills_to_learn(user.id, db)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill recommendation failed: {str(e)}")


@router.post("/{skill_id}/log-hours")
async def log_study_hours(
    skill_id: str,
    req: LogHoursRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log study hours for a skill."""
    try:
        skill = await LearningService.log_study_hours(skill_id, req.hours, db)
        return {
            "id": skill.id,
            "loggedHours": skill.logged_hours,
            "progressPercent": skill.progress_percent
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{skill_id}/assessment")
async def submit_assessment_score(
    skill_id: str,
    req: SubmitAssessmentRequest,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit assessment quiz score."""
    res = await db.execute(select(SkillModel).where(SkillModel.id == skill_id, SkillModel.user_id == user.id))
    skill = res.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found.")

    skill.assessment_score = req.scorePercent
    await db.commit()
    return {"status": "success", "skillId": skill.id, "assessmentScore": skill.assessment_score}
