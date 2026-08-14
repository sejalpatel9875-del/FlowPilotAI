import uuid
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class AIRequestModel(Base, TimestampMixin):
    __tablename__ = "ai_gateway_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # generate, stream, structured, embed
    
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[str] = mapped_column(String(50), default="completed", index=True)  # completed, failed, error
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
