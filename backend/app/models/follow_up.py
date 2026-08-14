import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class FollowUpSequenceModel(Base, TimestampMixin):
    __tablename__ = "follow_up_sequences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), default="Standard 3-Step Cadence")
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True)  # ACTIVE, COMPLETED, STOPPED
    current_step: Mapped[int] = mapped_column(Integer, default=1)

    lead: Mapped["LeadModel"] = relationship("LeadModel", lazy="selectin")
    follow_ups: Mapped[List["FollowUpModel"]] = relationship("FollowUpModel", back_populates="sequence", cascade="all, delete-orphan", lazy="selectin")


class FollowUpModel(Base, TimestampMixin):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_id: Mapped[str] = mapped_column(String(36), ForeignKey("follow_up_sequences.id", ondelete="CASCADE"), nullable=False, index=True)

    step_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 3, 7, 14
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), default="UPCOMING", index=True)
    # Statuses: DUE, UPCOMING, WAITING, COMPLETED, STOPPED

    draft_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    sequence: Mapped["FollowUpSequenceModel"] = relationship("FollowUpSequenceModel", back_populates="follow_ups")
    executions: Mapped[List["FollowUpExecutionModel"]] = relationship("FollowUpExecutionModel", cascade="all, delete-orphan", lazy="selectin")


class FollowUpExecutionModel(Base, TimestampMixin):
    __tablename__ = "follow_up_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    followup_id: Mapped[str] = mapped_column(String(36), ForeignKey("follow_ups.id", ondelete="CASCADE"), nullable=False, index=True)

    executed_by: Mapped[str] = mapped_column(String(100), default="FollowUpAgent")
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
