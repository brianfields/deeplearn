"""Internal service layer for flow engine infrastructure."""

from datetime import UTC, datetime
from typing import Any
import uuid

from ..llm_services.public import LLMServicesProvider
from .models import FlowRunModel, FlowStepRunModel
from .repo import FlowRunRepo, FlowStepRunRepo

__all__ = ["FlowEngineService", "FlowRunQueryService"]


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

    async def create_flow_run_record(self, flow_name: str, inputs: dict[str, Any], user_id: uuid.UUID | None = None) -> uuid.UUID:
        """Create a new flow run record (internal use)."""
        flow_run = FlowRunModel(user_id=user_id, flow_name=flow_name, inputs=inputs, status="running", execution_mode="sync", started_at=datetime.now(UTC))

        created_run = self.flow_run_repo.create(flow_run)
        assert created_run.id is not None
        return created_run.id

    async def create_step_run_record(self, flow_run_id: uuid.UUID, step_name: str, step_order: int, inputs: dict[str, Any]) -> uuid.UUID:
        """Create a new step run record (internal use)."""
        step_run = FlowStepRunModel(flow_run_id=flow_run_id, step_name=step_name, step_order=step_order, inputs=inputs, status="running")

        created_step = self.step_run_repo.create(step_run)
        assert created_step.id is not None
        return created_step.id

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

    async def update_step_run_error(self, step_run_id: uuid.UUID, error_message: str, execution_time_ms: int) -> None:
        """Update step run with error data (internal use)."""
        step_run = self.step_run_repo.by_id(step_run_id)
        if step_run:
            step_run.error_message = error_message
            step_run.execution_time_ms = execution_time_ms
            step_run.status = "failed"
            step_run.completed_at = datetime.now(UTC)
            self.step_run_repo.save(step_run)

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
            if flow_run.started_at:
                flow_run.execution_time_ms = int((flow_run.completed_at - flow_run.started_at).total_seconds() * 1000)

            self.flow_run_repo.save(flow_run)

    async def fail_flow_run(self, flow_run_id: uuid.UUID, error_message: str) -> None:
        """Mark a flow run as failed (internal use)."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if flow_run:
            flow_run.error_message = error_message
            flow_run.status = "failed"
            flow_run.completed_at = datetime.now(UTC)

            # Calculate execution time
            if flow_run.started_at:
                flow_run.execution_time_ms = int((flow_run.completed_at - flow_run.started_at).total_seconds() * 1000)

            self.flow_run_repo.save(flow_run)

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

    def get_flow_run_by_id(self, flow_run_id: uuid.UUID) -> FlowRunModel | None:
        """Get flow run by ID. FOR ADMIN USE ONLY."""
        return self.flow_run_repo.by_id(flow_run_id)

    def get_flow_steps_by_run_id(self, flow_run_id: uuid.UUID) -> list[FlowStepRunModel]:
        """Get all steps for a flow run. FOR ADMIN USE ONLY."""
        return self.step_run_repo.by_flow_run_id(flow_run_id)

    def get_flow_step_by_id(self, step_run_id: uuid.UUID) -> FlowStepRunModel | None:
        """Get flow step by ID. FOR ADMIN USE ONLY."""
        return self.step_run_repo.by_id(step_run_id)

    def get_recent_flow_runs(self, limit: int = 50, offset: int = 0) -> list[FlowRunModel]:
        """Get recent flow runs with pagination. FOR ADMIN USE ONLY."""
        return self.flow_run_repo.get_recent(limit, offset)

    def count_flow_runs(self) -> int:
        """Get total count of flow runs. FOR ADMIN USE ONLY."""
        return self.flow_run_repo.count_all()
