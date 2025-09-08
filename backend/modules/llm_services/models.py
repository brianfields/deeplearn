"""SQLAlchemy models for LLM services."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.data_structures import Base

__all__ = ["UUID", "LLMRequestModel"]


class UUID(TypeDecorator):
    """Database-agnostic UUID type that works with both PostgreSQL and SQLite."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        else:
            return uuid.UUID(value) if isinstance(value, str) else value


class LLMRequestModel(Base):
    """
    Tracks individual LLM API requests with full request/response data.

    This model provides comprehensive logging for LLM interactions including:
    - Complete request/response capture for debugging
    - Performance and cost analysis
    - Error tracking and retry information
    - Caching and optimization data
    """

    __tablename__ = "llm_requests"

    # Core identification
    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(), nullable=True, index=True)

    # Provider and model information
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Request parameters
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False)

    # Request and response data
    messages: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    additional_params: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    response_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_raw: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Usage and cost information
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Response metadata
    finish_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Execution status and timing
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)  # pending, completed, failed
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Retry and optimization information
    retry_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Context and metadata
    context_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<LLMRequestModel(id={self.id}, provider='{self.provider}', model='{self.model}', status='{self.status}')>"

    @property
    def total_tokens_calculated(self) -> int | None:
        """Calculate total tokens if not provided."""
        if self.tokens_used is not None:
            return self.tokens_used
        if self.prompt_tokens is not None and self.completion_tokens is not None:
            return self.prompt_tokens + self.completion_tokens
        return None

    @property
    def request_summary(self) -> dict[str, Any]:
        """Get a summary of the request for logging/debugging."""
        return {
            "id": str(self.id),
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "execution_time_ms": self.execution_time_ms,
            "cached": self.cached,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
