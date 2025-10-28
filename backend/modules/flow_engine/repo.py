"""Repository layer for flow execution data access."""

import uuid

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .models import FlowRunModel, FlowStepRunModel

__all__ = ["FlowRunRepo", "FlowStepRunRepo"]


class FlowRunRepo:
    """Repository for FlowRun database operations."""

    def __init__(self, session: Session) -> None:
        self.s = session

    def by_id(self, flow_run_id: uuid.UUID) -> FlowRunModel | None:
        """Get flow run by ID."""
        return self.s.get(FlowRunModel, flow_run_id)

    def create(self, flow_run: FlowRunModel) -> FlowRunModel:
        """Create a new flow run."""
        self.s.add(flow_run)
        self.s.flush()
        return flow_run

    def save(self, flow_run: FlowRunModel) -> FlowRunModel:
        """Save changes to an existing flow run."""
        self.s.add(flow_run)
        return flow_run

    def by_user_id(self, user_id: int, limit: int = 50, offset: int = 0) -> list[FlowRunModel]:
        """Get flow runs for a specific user."""
        return list(self.s.execute(select(FlowRunModel).where(FlowRunModel.user_id == user_id).order_by(desc(FlowRunModel.created_at)).limit(limit).offset(offset)).scalars())

    def by_status(self, status: str, limit: int = 100) -> list[FlowRunModel]:
        """Get flow runs by status."""
        return list(self.s.execute(select(FlowRunModel).where(FlowRunModel.status == status).order_by(desc(FlowRunModel.created_at)).limit(limit)).scalars())

    def by_flow_name(self, flow_name: str, limit: int = 50, offset: int = 0) -> list[FlowRunModel]:
        """Get flow runs by flow name."""
        return list(self.s.execute(select(FlowRunModel).where(FlowRunModel.flow_name == flow_name).order_by(desc(FlowRunModel.created_at)).limit(limit).offset(offset)).scalars())

    def count_by_user(self, user_id: int) -> int:
        """Count total flow runs for a user."""
        result = self.s.execute(select(FlowRunModel.id).where(FlowRunModel.user_id == user_id))
        return len(list(result.scalars()))

    def count_by_status(self, status: str) -> int:
        """Count flow runs by status."""
        result = self.s.execute(select(FlowRunModel.id).where(FlowRunModel.status == status))
        return len(list(result.scalars()))

    def get_recent(self, limit: int = 50, offset: int = 0) -> list[FlowRunModel]:
        """Get recent flow runs with pagination."""
        return list(self.s.execute(select(FlowRunModel).order_by(desc(FlowRunModel.created_at)).limit(limit).offset(offset)).scalars())

    def list_by_filters(
        self,
        *,
        arq_task_id: str | None = None,
        unit_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FlowRunModel]:
        """List flow runs filtered by ARQ task ID or embedded unit identifier."""

        stmt = select(FlowRunModel)
        if arq_task_id:
            stmt = stmt.where(FlowRunModel.arq_task_id == arq_task_id)
        if unit_id:
            stmt = stmt.where(FlowRunModel.inputs["unit_id"].astext == unit_id)

        stmt = stmt.order_by(desc(FlowRunModel.created_at)).limit(limit).offset(offset)
        return list(self.s.execute(stmt).scalars())

    def count_all(self) -> int:
        """Count all flow runs."""
        result = self.s.execute(select(FlowRunModel.id))
        return len(list(result.scalars()))


class FlowStepRunRepo:
    """Repository for FlowStepRun database operations."""

    def __init__(self, session: Session) -> None:
        self.s = session

    def by_id(self, step_run_id: uuid.UUID) -> FlowStepRunModel | None:
        """Get step run by ID."""
        return self.s.get(FlowStepRunModel, step_run_id)

    def create(self, step_run: FlowStepRunModel) -> FlowStepRunModel:
        """Create a new step run."""
        self.s.add(step_run)
        self.s.flush()
        return step_run

    def save(self, step_run: FlowStepRunModel) -> FlowStepRunModel:
        """Save changes to an existing step run."""
        self.s.add(step_run)
        return step_run

    def by_flow_run_id(self, flow_run_id: uuid.UUID) -> list[FlowStepRunModel]:
        """Get all step runs for a flow run."""
        return list(self.s.execute(select(FlowStepRunModel).where(FlowStepRunModel.flow_run_id == flow_run_id).order_by(FlowStepRunModel.step_order)).scalars())

    def by_step_name(self, step_name: str, limit: int = 50) -> list[FlowStepRunModel]:
        """Get step runs by step name."""
        return list(self.s.execute(select(FlowStepRunModel).where(FlowStepRunModel.step_name == step_name).order_by(desc(FlowStepRunModel.created_at)).limit(limit)).scalars())

    def by_status(self, status: str, limit: int = 100) -> list[FlowStepRunModel]:
        """Get step runs by status."""
        return list(self.s.execute(select(FlowStepRunModel).where(FlowStepRunModel.status == status).order_by(desc(FlowStepRunModel.created_at)).limit(limit)).scalars())

    def count_by_flow_run(self, flow_run_id: uuid.UUID) -> int:
        """Count steps in a flow run."""
        result = self.s.execute(select(FlowStepRunModel.id).where(FlowStepRunModel.flow_run_id == flow_run_id))
        return len(list(result.scalars()))
