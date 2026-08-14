import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class TimeBlockModel(Base, TimestampMixin):
    __tablename__ = "time_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    block_type: Mapped[str] = mapped_column(String(50), default="FOCUS", index=True)
    # Types: FOCUS, LEARNING, BREAK, FIXED

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", index=True)
    # Statuses: SCHEDULED, COMPLETED, SKIPPED, RESCHEDULED, REDUCED_SCOPE

    task: Mapped[Optional["TaskModel"]] = relationship("TaskModel", lazy="selectin")


class UserTimePreferenceModel(Base, TimestampMixin):
    __tablename__ = "user_time_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    available_hours_per_day: Mapped[float] = mapped_column(Float, default=8.0)
    work_start_time: Mapped[str] = mapped_column(String(10), default="09:00")
    work_end_time: Mapped[str] = mapped_column(String(10), default="17:00")

    priority_areas: Mapped[Optional[str]] = mapped_column(Text, default="High-Revenue Freelance Projects, Core Skill Growth")
    learning_goals: Mapped[Optional[str]] = mapped_column(Text, default="Master AI Agent Architecture & Full-Stack Systems")
    freelancing_goals: Mapped[Optional[str]] = mapped_column(Text, default="Reach $10k/mo MRR with high-fit SaaS clients")

    user: Mapped["UserModel"] = relationship("UserModel", lazy="selectin")
