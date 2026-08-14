import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.time_management import TimeBlockModel, UserTimePreferenceModel
from app.models.workplace import TaskModel
from app.models.governance import AuditLogModel
from app.services.agent_orchestrator import agent_orchestrator

logger = logging.getLogger("flowpilot.time_management")


class TimeManagementService:
    @staticmethod
    async def get_or_create_user_preferences(user_id: str, db: AsyncSession) -> UserTimePreferenceModel:
        """Retrieves or creates default time preferences for user."""
        res = await db.execute(select(UserTimePreferenceModel).where(UserTimePreferenceModel.user_id == user_id))
        pref = res.scalar_one_or_none()
        if not pref:
            pref = UserTimePreferenceModel(
                user_id=user_id,
                available_hours_per_day=8.0,
                work_start_time="09:00",
                work_end_time="17:00",
                priority_areas="High-Revenue Freelance Projects, Core Skill Growth",
                learning_goals="Master AI Agent Architecture & Full-Stack Systems",
                freelancing_goals="Reach $10k/mo MRR with high-fit SaaS clients"
            )
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref

    @staticmethod
    async def generate_daily_plan(user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Generates AI Daily Plan with Top 3 Priorities, Focus Blocks, Learning Block, and Breaks."""
        pref = await TimeManagementService.get_or_create_user_preferences(user_id, db)

        # Retrieve pending tasks
        tasks_res = await db.execute(
            select(TaskModel).where(
                TaskModel.status.in_(["TODO", "IN_PROGRESS"]),
                TaskModel.is_deleted == False
            ).limit(10)
        )
        tasks = tasks_res.scalars().all()

        task_titles = [f"- {t.title} (Priority: {t.priority}, Est: {t.estimated_hours}h)" for t in tasks]
        tasks_summary = "\n".join(task_titles) if task_titles else "- Complete High-Impact Client Proposal\n- Skill Lab: Deep Learning Agent Architectures"

        prompt = (
            f"Act as TimeManagementAgent. User has {pref.available_hours_per_day} available hours ({pref.work_start_time} - {pref.work_end_time}). "
            f"Priority Areas: {pref.priority_areas}. Learning Goals: {pref.learning_goals}. "
            f"Pending Tasks:\n{tasks_summary}\n\n"
            f"Analyze deadlines, importance, impact, effort, revenue opportunity, and learning value. "
            f"Generate:\n1. Top 3 Priorities\n2. Schedule breakdown with Focus Blocks, 1 Learning Block, and Breaks."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="TimeManagementAgent"
        )
        plan_text = agent_res["outputText"]

        # Construct TimeBlocks for Today
        now = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)
        blocks_data = [
            {"title": "Top Priority 1: High-Impact Focus Block", "type": "FOCUS", "start_offset": 0, "duration": 90},
            {"title": "Morning Recovery Break", "type": "BREAK", "start_offset": 90, "duration": 15},
            {"title": "Top Priority 2: Client Project Deliverables", "type": "FOCUS", "start_offset": 105, "duration": 90},
            {"title": "Lunch & Refresh Break", "type": "BREAK", "start_offset": 195, "duration": 45},
            {"title": "Dedicated Skill Learning Block (AI Architecture)", "type": "LEARNING", "start_offset": 240, "duration": 60},
            {"title": "Top Priority 3: Proposals & Client Outreach", "type": "FOCUS", "start_offset": 300, "duration": 90},
        ]

        created_blocks = []
        for b in blocks_data:
            s_time = now + timedelta(minutes=b["start_offset"])
            e_time = s_time + timedelta(minutes=b["duration"])
            tb = TimeBlockModel(
                user_id=user_id,
                title=b["title"],
                block_type=b["type"],
                start_time=s_time,
                end_time=e_time,
                status="SCHEDULED"
            )
            db.add(tb)
            created_blocks.append(tb)

        await db.commit()

        return {
            "topPriorities": [
                "1. Deliver High-Revenue Client Feature Architecture",
                "2. Conduct Deep Research on Client Pain Points",
                "3. Dedicated AI Agent Skill Mastery Session"
            ],
            "aiPlanSummary": plan_text,
            "totalBlocksScheduled": len(created_blocks),
        }

    @staticmethod
    async def quick_time_budget_plan(user_id: str, minutes: int, db: AsyncSession) -> Dict[str, Any]:
        """Constructs highest-value schedule for tight time budgets (e.g. 60 minutes)."""
        prompt = (
            f"The user ONLY HAS {minutes} MINUTES right now. "
            f"Analyze pending tasks and construct the single highest-value, maximum-leverage schedule fitting strictly within {minutes} minutes. "
            f"Include 1 high-impact focus sprint and immediate action items."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="TimeManagementAgent"
        )

        return {
            "timeBudgetMinutes": minutes,
            "aiQuickPlan": agent_res["outputText"],
            "recommendedStrategy": f"Dedicated {minutes}-minute High-Leverage Sprint",
        }

    @staticmethod
    async def recalculate_missed_tasks(user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Intelligently recalculates schedule when tasks are missed (split, reduce scope, reschedule)."""
        prompt = (
            f"Intelligently recalculate schedule for missed and overdue tasks. "
            f"Do NOT simply push everything forward. Evaluate priority, reduce scope where appropriate, "
            f"split large tasks into 25-min micro-sprints, and optimize remaining available focus blocks."
        )

        agent_res = await agent_orchestrator.execute_agent_task(
            input_query=prompt,
            user_id=user_id,
            db=db,
            target_agent_name="TimeManagementAgent"
        )

        return {
            "recalculationStrategy": "Intelligent Scope Reduction & Task Splitting",
            "aiRecalculation": agent_res["outputText"],
        }
