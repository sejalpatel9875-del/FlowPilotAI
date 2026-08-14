import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class AutomationModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "automations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 10 Triggers: NEW_LEAD, LEAD_QUALIFIED, OUTREACH_SENT, NO_RESPONSE, REPLY_RECEIVED, TASK_DUE, DEADLINE_APPROACHING, LEARNING_BEHIND_SCHEDULE, DAILY_SCHEDULE, WEEKLY_REVIEW
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    trigger_event: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    condition_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_decision_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 7 Actions: GENERATE_DRAFT, CREATE_TASK, CREATE_FOLLOW_UP, UPDATE_LEAD, GENERATE_REPORT, CREATE_LEARNING_SESSION, SEND_NOTIFICATION
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action_params_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True)  # ACTIVE, PAUSED
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)

    runs: Mapped[List["AutomationRunModel"]] = relationship("AutomationRunModel", back_populates="automation", cascade="all, delete-orphan", lazy="selectin")


class AutomationRunModel(Base, TimestampMixin):
    __tablename__ = "automation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    automation_id: Mapped[str] = mapped_column(String(36), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True)

    trigger_event: Mapped[str] = mapped_column(String(100), default="Manual Test Trigger")
    ai_decision_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS", index=True)  # SUCCESS, PENDING_APPROVAL, FAILED
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    automation: Mapped["AutomationModel"] = relationship("AutomationModel", back_populates="runs")
