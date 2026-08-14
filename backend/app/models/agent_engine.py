import uuid
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class AgentModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-4o")

    runs: Mapped[List["AgentRunModel"]] = relationship("AgentRunModel", back_populates="agent", cascade="all, delete-orphan")


class AgentRunModel(Base, TimestampMixin):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="idle", index=True)  # idle, thinking, running, completed, failed, needs_approval
    input_query: Mapped[str] = mapped_column(Text, nullable=False)

    agent: Mapped["AgentModel"] = relationship("AgentModel", back_populates="runs")
    messages: Mapped[List["AgentMessageModel"]] = relationship("AgentMessageModel", cascade="all, delete-orphan")
    tool_calls: Mapped[List["ToolCallModel"]] = relationship("ToolCallModel", cascade="all, delete-orphan")


class AgentMessageModel(Base, TimestampMixin):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # system, user, assistant, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)


class ToolCallModel(Base, TimestampMixin):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_args: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
