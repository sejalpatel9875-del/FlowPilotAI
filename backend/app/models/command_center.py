import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class CommandRecommendationModel(Base, TimestampMixin):
    __tablename__ = "command_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    query: Mapped[str] = mapped_column(String(255), default="What should I do next?")
    recommendations_json: Mapped[Text] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True)
    # Statuses: ACTIVE, ACCEPTED, DISMISSED, RESCHEDULED, FOCUS_STARTED

    outcome_action: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", lazy="selectin")
