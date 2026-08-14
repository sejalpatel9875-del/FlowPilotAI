import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class OutreachMessageModel(Base, TimestampMixin):
    __tablename__ = "outreach_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Channels: Email, LinkedIn connection note, Freelance proposal, Contact form draft

    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    draft_body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="REVIEW", index=True)
    # Statuses: DRAFT, REVIEW, APPROVED, SCHEDULED, SENT, FAILED, CANCELLED

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    lead: Mapped["LeadModel"] = relationship("LeadModel", lazy="selectin")
