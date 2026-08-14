import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AgentActivityModel(Base):
    __tablename__ = "agent_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="idle")
    details: Mapped[str] = mapped_column(Text, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[str] = mapped_column(String(100), default=lambda: datetime.utcnow().strftime("%H:%M:%S UTC"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
