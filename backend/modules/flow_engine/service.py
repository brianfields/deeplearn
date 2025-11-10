"""Internal service layer for flow engine infrastructure."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
import uuid

from ..llm_services.public import LLMServicesProvider
from .models import FlowRunModel, FlowStepRunModel
from .repo import FlowRunRepo, FlowStepRunRepo


# DTOs for external consumption
@dataclass
class FlowRunSummaryDTO:
    """DTO for flow run summary data."""

    id: str
    flow_name: str
    status: str
    execution_mode: str
    arq_task_id: str | None
    user_id: int | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    execution_time_ms: int | None
    total_tokens: int
    total_cost: float
    step_count: int
    error_message: str | None


@dataclass
class FlowStepDetailsDTO:
    """DTO for flow step details."""

    id: str
    flow_run_id: str
    llm_request_id: str | None
    step_name: str
    step_order: int
    status: str
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    tokens_used: int
    cost_estimate: float
    execution_time_ms: int | None
    error_message: str | None
    step_metadata: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


@dataclass
class FlowRunDetailsDTO:
    """DTO for complete flow run details."""

    id: str
    flow_name: str
    status: str
    execution_mode: str
    arq_task_id: str | None
    user_id: int | None
    current_step: str | None
    step_progress: int
    total_steps: int | None
    progress_percentage: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_heartbeat: datetime | None
    execution_time_ms: int | None
    total_tokens: int
    total_cost: float
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    flow_metadata: dict[str, Any] | None
    error_message: str | None
    steps: list[FlowStepDetailsDTO]


__all__ = ["FlowEngineService", "FlowRunDetailsDTO", "FlowRunQueryService", "FlowRunSummaryDTO", "FlowStepDetailsDTO"]


class FlowEngineService:
    """
    Internal service layer for flow engine infrastructure.

    Note: This is not exposed in public.py - flows and steps use the base classes directly.
    This service provides infrastructure support for the base classes.
    """

    def __init__(self, flow_run_repo: FlowRunRepo, step_run_repo: FlowStepRunRepo, llm_services: LLMServicesProvider) -> None:
        self.flow_run_repo = flow_run_repo
        self.step_run_repo = step_run_repo
        self.llm_services = llm_services

    def _commit_changes(self) -> None:
        """
        Commit pending changes to make them visible to other database sessions.

        This is critical for real-time visibility in the admin dashboard during
        long-running flows executed in ARQ tasks.
        """
        # Access the session through the repo (sync commit for immediate visibility)
        self.flow_run_repo.s.commit()

    async def create_flow_run_record(
        self,
        flow_name: str,
        inputs: dict[str, Any],
        user_id: int | None = None,
        *,
        execution_mode: str = "sync",
        arq_task_id: str | None = None,
    ) -> uuid.UUID:
        """Create a new flow run record (internal use)."""
        flow_run = FlowRunModel(
            user_id=user_id,
            flow_name=flow_name,
            inputs=inputs,
            status="running" if execution_mode == "sync" else "pending",
            execution_mode=execution_mode,
            started_at=datetime.now(UTC) if execution_mode == "sync" else None,
            arq_task_id=arq_task_id,
        )

        created_run = self.flow_run_repo.create(flow_run)
        assert created_run.id is not None

        # Commit immediately so the flow run is visible in admin dashboard
        self._commit_changes()

        return created_run.id

    async def create_step_run_record(
        self, flow_run_id: uuid.UUID, step_name: str, step_order: int, inputs: dict[str, Any], retry_attempt: int = 0, retry_of_step_run_id: uuid.UUID | None = None
    ) -> uuid.UUID:
        """Create a new step run record (internal use)."""
        step_run = FlowStepRunModel(
            flow_run_id=flow_run_id,
            step_name=step_name,
            step_order=step_order,
            inputs=inputs,
            status="running",
            retry_attempt=retry_attempt,
            retry_of_step_run_id=retry_of_step_run_id,
        )

        created_step = self.step_run_repo.create(step_run)
        assert created_step.id is not None

        # Commit immediately so the step is visible in admin dashboard
        self._commit_changes()

        return created_step.id

    async def mark_step_run_retry(self, step_run_id: uuid.UUID, error_message: str) -> None:
        """Mark step run as retrying after a failure (internal use)."""
        step_run = self.step_run_repo.by_id(step_run_id)
        if step_run:
            step_run.error_message = error_message
            step_run.status = "retrying"
            step_run.completed_at = datetime.now(UTC)
            self.step_run_repo.save(step_run)

            # Commit immediately so retry status is visible
            self._commit_changes()

    async def update_step_run_success(self, step_run_id: uuid.UUID, outputs: dict[str, Any], tokens_used: int, cost_estimate: float, execution_time_ms: int, llm_request_id: uuid.UUID | None = None) -> None:
        """Update step run with success data (internal use)."""
        step_run = self.step_run_repo.by_id(step_run_id)
        if step_run:
            step_run.outputs = outputs
            step_run.tokens_used = tokens_used
            step_run.cost_estimate = cost_estimate
            step_run.execution_time_ms = execution_time_ms
            step_run.llm_request_id = llm_request_id
            step_run.status = "completed"
            step_run.completed_at = datetime.now(UTC)
            self.step_run_repo.save(step_run)

            # Commit immediately so step completion is visible in admin dashboard
            self._commit_changes()

    async def update_step_run_error(self, step_run_id: uuid.UUID, error_message: str, execution_time_ms: int) -> None:
        """Update step run with error data (internal use)."""
        step_run = self.step_run_repo.by_id(step_run_id)
        if step_run:
            step_run.error_message = error_message
            step_run.execution_time_ms = execution_time_ms
            step_run.status = "failed"
            step_run.completed_at = datetime.now(UTC)
            self.step_run_repo.save(step_run)

            # Commit immediately so step failure is visible in admin dashboard
            self._commit_changes()

    async def update_flow_progress(self, flow_run_id: uuid.UUID, current_step: str, step_progress: int, progress_percentage: float | None = None) -> None:
        """Update flow run progress (internal use)."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if flow_run:
            flow_run.current_step = current_step
            flow_run.step_progress = step_progress
            flow_run.last_heartbeat = datetime.now(UTC)

            if progress_percentage is not None:
                flow_run.progress_percentage = progress_percentage
            elif flow_run.total_steps and flow_run.total_steps > 0:
                flow_run.progress_percentage = min(100.0, (step_progress / flow_run.total_steps) * 100)

            self.flow_run_repo.save(flow_run)

            # Commit immediately so progress updates are visible in admin dashboard
            self._commit_changes()

    async def complete_flow_run(self, flow_run_id: uuid.UUID, outputs: dict[str, Any]) -> None:
        """Complete a flow run (internal use)."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if flow_run:
            flow_run.outputs = outputs
            flow_run.status = "completed"
            flow_run.completed_at = datetime.now(UTC)
            flow_run.progress_percentage = 100.0

            # Calculate total metrics from steps
            steps = self.step_run_repo.by_flow_run_id(flow_run_id)
            total_tokens = sum(step.tokens_used or 0 for step in steps)
            total_cost = sum(step.cost_estimate or 0.0 for step in steps)

            flow_run.total_tokens = total_tokens
            flow_run.total_cost = total_cost

            # Calculate execution time
            if flow_run.started_at is not None and flow_run.completed_at is not None:
                started_at = cast(datetime, flow_run.started_at)
                completed_at = cast(datetime, flow_run.completed_at)
                flow_run.execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

            self.flow_run_repo.save(flow_run)

            # Commit immediately so completion is visible in admin dashboard
            self._commit_changes()

    async def fail_flow_run(self, flow_run_id: uuid.UUID, error_message: str) -> None:
        """Mark a flow run as failed (internal use)."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if flow_run:
            flow_run.error_message = error_message
            flow_run.status = "failed"
            flow_run.completed_at = datetime.now(UTC)

            # Calculate execution time
            if flow_run.started_at is not None and flow_run.completed_at is not None:
                started_at = cast(datetime, flow_run.started_at)
                completed_at = cast(datetime, flow_run.completed_at)
                flow_run.execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

            self.flow_run_repo.save(flow_run)

            # Commit immediately so failure is visible in admin dashboard
            self._commit_changes()

    def get_llm_services(self) -> LLMServicesProvider:
        """Get LLM services provider (internal use)."""
        return self.llm_services


class FlowRunQueryService:
    """
    Query service for flow run data.

    NOTE: This service is specifically designed for admin module use only.
    It provides read-only access to flow execution data for monitoring and analytics.
    """

    def __init__(self, flow_run_repo: FlowRunRepo, step_run_repo: FlowStepRunRepo) -> None:
        self.flow_run_repo = flow_run_repo
        self.step_run_repo = step_run_repo

    def get_flow_run_by_id(self, flow_run_id: uuid.UUID) -> FlowRunDetailsDTO | None:
        """Get flow run by ID. FOR ADMIN USE ONLY."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if not flow_run:
            return None

        # Collect steps to compute totals and include details
        steps = self.step_run_repo.by_flow_run_id(flow_run.id)
        step_dtos = [
            FlowStepDetailsDTO(
                id=str(step.id),
                flow_run_id=str(step.flow_run_id),
                llm_request_id=str(step.llm_request_id) if step.llm_request_id else None,
                step_name=step.step_name,
                step_order=step.step_order,
                status=step.status,
                inputs=step.inputs or {},
                outputs=step.outputs,
                tokens_used=step.tokens_used or 0,
                cost_estimate=step.cost_estimate or 0.0,
                execution_time_ms=step.execution_time_ms,
                error_message=step.error_message,
                step_metadata=step.step_metadata,
                created_at=step.created_at,
                completed_at=step.completed_at,
            )
            for step in steps
        ]

        total_tokens = sum(step.tokens_used or 0 for step in steps)
        total_cost = sum(step.cost_estimate or 0.0 for step in steps)

        return FlowRunDetailsDTO(
            id=str(flow_run.id),
            flow_name=flow_run.flow_name,
            status=flow_run.status,
            execution_mode=flow_run.execution_mode,
            arq_task_id=flow_run.arq_task_id,
            user_id=flow_run.user_id,
            current_step=flow_run.current_step,
            step_progress=flow_run.step_progress,
            total_steps=flow_run.total_steps,
            progress_percentage=flow_run.progress_percentage,
            created_at=flow_run.created_at,
            started_at=flow_run.started_at,
            completed_at=flow_run.completed_at,
            last_heartbeat=flow_run.last_heartbeat,
            execution_time_ms=flow_run.execution_time_ms,
            total_tokens=total_tokens,
            total_cost=total_cost,
            inputs=flow_run.inputs or {},
            outputs=flow_run.outputs,
            flow_metadata=flow_run.flow_metadata,
            error_message=flow_run.error_message,
            steps=step_dtos,
        )

    def get_flow_steps_by_run_id(self, flow_run_id: uuid.UUID) -> list[FlowStepDetailsDTO]:
        """Get all steps for a flow run. FOR ADMIN USE ONLY."""
        steps = self.step_run_repo.by_flow_run_id(flow_run_id)
        return [
            FlowStepDetailsDTO(
                id=str(step.id),
                flow_run_id=str(step.flow_run_id),
                llm_request_id=str(step.llm_request_id) if step.llm_request_id else None,
                step_name=step.step_name,
                step_order=step.step_order,
                status=step.status,
                inputs=step.inputs or {},
                outputs=step.outputs,
                tokens_used=step.tokens_used or 0,
                cost_estimate=step.cost_estimate or 0.0,
                execution_time_ms=step.execution_time_ms,
                error_message=step.error_message,
                step_metadata=step.step_metadata,
                created_at=step.created_at,
                completed_at=step.completed_at,
            )
            for step in steps
        ]

    def get_flow_step_by_id(self, step_run_id: uuid.UUID) -> FlowStepDetailsDTO | None:
        """Get flow step by ID. FOR ADMIN USE ONLY."""
        step = self.step_run_repo.by_id(step_run_id)
        if not step:
            return None

        return FlowStepDetailsDTO(
            id=str(step.id),
            flow_run_id=str(step.flow_run_id),
            llm_request_id=str(step.llm_request_id) if step.llm_request_id else None,
            step_name=step.step_name,
            step_order=step.step_order,
            status=step.status,
            inputs=step.inputs or {},
            outputs=step.outputs,
            tokens_used=step.tokens_used or 0,
            cost_estimate=step.cost_estimate or 0.0,
            execution_time_ms=step.execution_time_ms,
            error_message=step.error_message,
            step_metadata=step.step_metadata,
            created_at=step.created_at,
            completed_at=step.completed_at,
        )

    def get_recent_flow_runs(self, limit: int = 50, offset: int = 0) -> list[FlowRunSummaryDTO]:
        """Get recent flow runs with pagination. FOR ADMIN USE ONLY."""
        flow_runs = self.flow_run_repo.get_recent(limit, offset)
        return [
            FlowRunSummaryDTO(
                id=str(run.id),
                flow_name=run.flow_name,
                status=run.status,
                execution_mode=run.execution_mode,
                arq_task_id=run.arq_task_id,
                user_id=run.user_id,
                created_at=run.created_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                execution_time_ms=run.execution_time_ms,
                total_tokens=run.total_tokens or 0,
                total_cost=run.total_cost or 0.0,
                step_count=len(self.step_run_repo.by_flow_run_id(run.id)),
                error_message=run.error_message,
            )
            for run in flow_runs
        ]

    def count_flow_runs(self) -> int:
        """Get total count of flow runs. FOR ADMIN USE ONLY."""
        return self.flow_run_repo.count_all()

    def list_flow_runs(
        self,
        *,
        arq_task_id: str | None = None,
        unit_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FlowRunSummaryDTO]:
        """List flow runs filtered by admin observability parameters."""

        runs = self.flow_run_repo.list_by_filters(
            arq_task_id=arq_task_id,
            unit_id=unit_id,
            limit=limit,
            offset=offset,
        )
        result: list[FlowRunSummaryDTO] = []
        for run in runs:
            step_count = len(self.step_run_repo.by_flow_run_id(run.id))
            result.append(
                FlowRunSummaryDTO(
                    id=str(run.id),
                    flow_name=run.flow_name,
                    status=run.status,
                    execution_mode=run.execution_mode,
                    arq_task_id=run.arq_task_id,
                    user_id=run.user_id,
                    created_at=run.created_at,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    execution_time_ms=run.execution_time_ms,
                    total_tokens=run.total_tokens or 0,
                    total_cost=run.total_cost or 0.0,
                    step_count=step_count,
                    error_message=run.error_message,
                )
            )
        return result
