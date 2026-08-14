import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class AgentMemoryModel(Base, TimestampMixin):
    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    memory_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    memory_value: Mapped[str] = mapped_column(Text, nullable=False)
