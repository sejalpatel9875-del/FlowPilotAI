import uuid
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class LeadModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), default="https://acme.com")
    industry: Mapped[Optional[str]] = mapped_column(String(100), default="Technology")
    location: Mapped[Optional[str]] = mapped_column(String(100), default="San Francisco, CA")
    source: Mapped[str] = mapped_column(String(100), default="Organic", index=True)
    service_fit: Mapped[str] = mapped_column(String(50), default="High")  # High, Medium, Low
    value: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    
    lead_score: Mapped[int] = mapped_column(Integer, default=75, index=True)
    status: Mapped[str] = mapped_column(String(50), default="New", index=True)
    # 11 Stages: New, Qualified, Researching, Outreach Ready, Contacted, Replied, Meeting, Proposal, Won, Lost, Not Interested
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), default="Schedule discovery call")
    verification_status: Mapped[str] = mapped_column(String(50), default="Verified")  # Verified, Inferred, Unknown

    company_ref: Mapped[Optional["CompanyModel"]] = relationship("CompanyModel", back_populates="leads")
    primary_contact: Mapped[Optional["ContactModel"]] = relationship("ContactModel", back_populates="leads")
    activities: Mapped[List["LeadActivityModel"]] = relationship("LeadActivityModel", cascade="all, delete-orphan", lazy="selectin")
