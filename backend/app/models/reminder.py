import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ReminderModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    linked_lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)  # active, snoozed, completed, dismissed
    priority: Mapped[str] = mapped_column(String(50), default="medium")  # low, medium, high, urgent
    recurrence: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # daily, weekly, none/null
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
