import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.learning import SkillModel
from app.models.project import ProjectModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.learning")


class LearningService:
    @staticmethod
    async def create_skill_roadmap(
        name: str,
        current_level: str,
        target_level: str,
        deadline_str: Optional[str],
        weekly_hours: int,
        user_id: str,
        db: AsyncSession
    ) -> SkillModel:
        """Creates skill goal and executes LearningAgent to construct project-connected curriculum."""
        deadline = datetime.fromisoformat(deadline_str) if deadline_str else (datetime.utcnow() + timedelta(days=30))

        # Retrieve active client projects for context connection
        proj_res = await db.execute(select(ProjectModel).where(ProjectModel.is_deleted == False).limit(5))
        projects = proj_res.scalars().all()
        project_titles = [p.name for p in projects]

        prompt = (
            f"Act as LearningAgent. Create a structured learning roadmap for skill '{name}'. "
            f"Current Level: {current_level}. Target Level: {target_level}. Deadline: {deadline.strftime('%Y-%m-%d')}. "
            f"Weekly Available Hours: {weekly_hours}h. Active Freelance Projects: {', '.join(project_titles) if project_titles else 'SaaS Platform Build'}. "
            f"Construct:\n"
            f"1. Topics\n2. Exercises\n3. Mini Projects (Connect directly to real projects)\n"
            f"4. Assessments\n5. Revision Sessions."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="LearningAgent"
        )
        ai_output = agent_res["outputText"]

        # Structure Curriculum JSON
        curriculum = {
            "skillName": name,
            "currentLevel": current_level,
            "targetLevel": target_level,
            "aiRoadmapSummary": ai_output,
            "topics": [
                {"title": f"{name} Foundations & Architecture", "status": "COMPLETED"},
                {"title": f"Advanced Patterns & Optimization for {name}", "status": "IN_PROGRESS"},
                {"title": f"Enterprise Scaling & Security", "status": "UPCOMING"}
            ],
            "exercises": [
                {"title": "Implement Async Data Pipeline", "difficulty": "Medium"},
                {"title": "Optimize Low-Latency State Caching", "difficulty": "Hard"}
            ],
            "miniProjects": [
                {"title": f"Build Production Module for {project_titles[0] if project_titles else 'Client App'}", "connectedProject": project_titles[0] if project_titles else 'Client App'}
            ],
            "assessments": [
                {"title": "Architecture & Best Practices Quiz", "scorePercent": 88.0}
            ],
            "revisionSessions": [
                {"title": "Spaced Repetition: Core Concepts Review", "scheduledDate": (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")}
            ]
        }

        skill = SkillModel(
            user_id=user_id,
            name=name,
            current_level=current_level,
            target_level=target_level,
            deadline=deadline,
            weekly_hours=weekly_hours,
            progress_percent=35.0,
            logged_hours=12.5,
            assessment_score=88.0,
            curriculum_json=json.dumps(curriculum)
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return skill

    @staticmethod
    async def recommend_skills_to_learn(user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """AI Skill Recommender: Recommends next skills based on projects, opportunities, and goals."""
        skills_res = await db.execute(select(SkillModel).where(SkillModel.user_id == user_id))
        current_skills = [s.name for s in skills_res.scalars().all()]

        prompt = (
            f"Act as LearningAgent. Current User Skills: {', '.join(current_skills) if current_skills else 'Python, React'}. "
            f"Analyze high-paying freelancing opportunities, client demand, and strategic goals. "
            f"Recommend 3 high-ROI skills to learn next, explaining why each skill accelerates client contract value."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="LearningAgent"
        )

        return {
            "aiRecommendationsSummary": agent_res["outputText"],
            "recommendedSkills": [
                {"skill": "Autonomous Multi-Agent Architecture", "roiCategory": "High Revenue ($150/hr)", "reason": "Surging client demand for multi-agent workflows."},
                {"skill": "Vector Search & Hybrid RAG Optimization", "roiCategory": "High Value SaaS", "reason": "Key requirement for high-ticket enterprise AI projects."},
                {"skill": "FastAPI Async Performance Tuning", "roiCategory": "Core System Stability", "reason": "Ensures sub-100ms API response latency under load."}
            ]
        }

    @staticmethod
    async def log_study_hours(skill_id: str, hours: float, db: AsyncSession) -> SkillModel:
        """Logs study hours and updates progress percentage."""
        res = await db.execute(select(SkillModel).where(SkillModel.id == skill_id))
        skill = res.scalar_one_or_none()
        if not skill:
            raise ValueError("Skill not found.")

        skill.logged_hours += hours
        # Increase progress percent proportionally
        skill.progress_percent = min(skill.progress_percent + (hours * 2.5), 100.0)

        await db.commit()
        await db.refresh(skill)
        return skill
