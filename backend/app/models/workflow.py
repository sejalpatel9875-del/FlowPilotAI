import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class WorkflowModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", index=True)
    # States: PLANNED, VALIDATING, RUNNING, WAITING_FOR_APPROVAL, APPROVED, REJECTED, COMPLETED, FAILED, CANCELLED

    plan_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_state_json: Mapped[Optional[str]] = mapped_column(Text, default="{}")
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    completed_steps: Mapped[int] = mapped_column(Integer, default=0)
    replan_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    steps: Mapped[List["WorkflowStepModel"]] = relationship("WorkflowStepModel", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStepModel.step_order")
    approvals: Mapped[List["WorkflowApprovalModel"]] = relationship("WorkflowApprovalModel", back_populates="workflow", cascade="all, delete-orphan")
    events: Mapped[List["WorkflowEventModel"]] = relationship("WorkflowEventModel", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowEventModel.timestamp")


class WorkflowStepModel(Base, TimestampMixin):
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    step_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "step_1"
    step_order: Mapped[int] = mapped_column(Integer, default=0)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Must be in the 12 verified agents
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    depends_on_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON array of step_keys e.g. ["step_1"]
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    is_side_effect: Mapped[bool] = mapped_column(Boolean, default=False)
    
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", index=True)
    # States: PLANNED, RUNNING, WAITING_FOR_APPROVAL, APPROVED, REJECTED, COMPLETED, FAILED, SKIPPED

    input_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    workflow: Mapped["WorkflowModel"] = relationship("WorkflowModel", back_populates="steps")


class WorkflowApprovalModel(Base, TimestampMixin):
    __tablename__ = "workflow_approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    affected_resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    affected_resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, approved, rejected, expired
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approver_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    workflow: Mapped["WorkflowModel"] = relationship("WorkflowModel", back_populates="approvals")


class WorkflowEventModel(Base, TimestampMixin):
    __tablename__ = "workflow_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. WORKFLOW_CREATED, PLAN_GENERATED, PLAN_VALIDATED, STEP_STARTED, STEP_COMPLETED,
    # STEP_FAILED, APPROVAL_REQUESTED, APPROVAL_GRANTED, APPROVAL_REJECTED, SIDE_EFFECT_EXECUTED,
    # WORKFLOW_COMPLETED, WORKFLOW_FAILED, WORKFLOW_CANCELLED, REPLAN_TRIGGERED

    step_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    workflow: Mapped["WorkflowModel"] = relationship("WorkflowModel", back_populates="events")
