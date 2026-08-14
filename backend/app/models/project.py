import uuid
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ProjectModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="in_progress", index=True)
    deadline: Mapped[str] = mapped_column(String(100), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    hourly_rate: Mapped[float] = mapped_column(Float, default=100.0)

    client_ref: Mapped[Optional["ClientModel"]] = relationship("ClientModel", back_populates="projects")
    tasks: Mapped[List["TaskModel"]] = relationship("TaskModel", cascade="all, delete-orphan")
