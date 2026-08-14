import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class GoalModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="in_progress")


class SkillModel(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Technical")
    proficiency_level: Mapped[int] = mapped_column(Integer, default=1)

    current_level: Mapped[str] = mapped_column(String(50), default="Beginner")
    target_level: Mapped[str] = mapped_column(String(50), default="Advanced")
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=5)

    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    logged_hours: Mapped[float] = mapped_column(Float, default=0.0)
    assessment_score: Mapped[float] = mapped_column(Float, default=85.0)

    curriculum_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class LearningPlanModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "learning_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    progress_items: Mapped[List["LearningProgressModel"]] = relationship("LearningProgressModel", cascade="all, delete-orphan")


class LearningProgressModel(Base, TimestampMixin):
    __tablename__ = "learning_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    last_studied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
