import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class CompanyModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    contacts: Mapped[List["ContactModel"]] = relationship("ContactModel", back_populates="company", cascade="all, delete-orphan")
    leads: Mapped[List["LeadModel"]] = relationship("LeadModel", back_populates="company_ref")


class ContactModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    company: Mapped[Optional["CompanyModel"]] = relationship("CompanyModel", back_populates="contacts")
    leads: Mapped[List["LeadModel"]] = relationship("LeadModel", back_populates="primary_contact")


class LeadActivityModel(Base, TimestampMixin):
    __tablename__ = "lead_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # call, email, meeting, note
    description: Mapped[str] = mapped_column(Text, nullable=False)
