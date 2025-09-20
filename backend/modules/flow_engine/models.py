"""SQLAlchemy models for flow execution tracking."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship  # type: ignore[attr-defined]

from modules.shared_models import Base, PostgresUUID

__all__ = ["FlowRunModel", "FlowStepRunModel"]


class FlowRunModel(Base):
    """
    Tracks execution of complete flows.

    This model stores comprehensive information about flow execution including:
    - Execution status and progress
    - Performance metrics (tokens, cost, timing)
    - Background task support
    - User and flow identification
    """

    __tablename__ = "flow_runs"

    # Core identification
    id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PostgresUUID(), nullable=True, index=True)
    flow_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Execution tracking
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)  # pending, running, completed, failed, cancelled

    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="sync")  # sync, async, background

    # Progress tracking for background tasks
    current_step: Mapped[str | None] = mapped_column(String(200), nullable=True)
    step_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timing information
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Performance metrics
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Data and metadata
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    flow_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    steps: Mapped[list["FlowStepRunModel"]] = relationship("FlowStepRunModel", back_populates="flow_run", cascade="all, delete-orphan")  # type: ignore

    def __repr__(self) -> str:
        return f"<FlowRunModel(id={self.id}, flow_name='{self.flow_name}', status='{self.status}')>"

    @property
    def duration_ms(self) -> int | None:
        """Calculate execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None

    @property
    def is_running(self) -> bool:
        """Check if the flow is currently running."""
        return self.status == "running"

    @property
    def is_complete(self) -> bool:
        """Check if the flow has completed (success or failure)."""
        return self.status in ["completed", "failed", "cancelled"]

    @property
    def progress_info(self) -> dict[str, Any]:
        """Get comprehensive progress information."""
        return {
            "flow_run_id": str(self.id),
            "flow_name": self.flow_name,
            "status": self.status,
            "execution_mode": self.execution_mode,
            "current_step": self.current_step,
            "step_progress": self.step_progress,
            "total_steps": self.total_steps,
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
        }


class FlowStepRunModel(Base):
    """
    Tracks execution of individual steps within a flow.

    This model provides detailed information about each step execution including:
    - Step-level performance metrics
    - Input/output capture for debugging
    - Error isolation and recovery
    - LLM request correlation
    """

    __tablename__ = "flow_step_runs"

    # Core identification
    id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(), primary_key=True, default=uuid.uuid4)
    flow_run_id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(), ForeignKey("flow_runs.id"), nullable=False, index=True)
    llm_request_id: Mapped[uuid.UUID | None] = mapped_column(PostgresUUID(), ForeignKey("llm_requests.id"), nullable=True, index=True)

    # Step information
    step_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Execution status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)  # pending, running, completed, failed

    # Data capture
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Performance metrics
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    flow_run: Mapped["FlowRunModel"] = relationship("FlowRunModel", back_populates="steps")  # type: ignore

    def __repr__(self) -> str:
        return f"<FlowStepRunModel(id={self.id}, step_name='{self.step_name}', status='{self.status}')>"

    @property
    def duration_ms(self) -> int | None:
        """Calculate step execution duration in milliseconds."""
        if self.created_at and self.completed_at:
            return int((self.completed_at - self.created_at).total_seconds() * 1000)
        return None
