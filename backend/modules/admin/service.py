# /backend/modules/admin/service.py
"""
Admin Module - Service Layer

Minimal service for admin dashboard functionality.
Returns DTOs for all admin functionality.
"""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel

from modules.content.public import ContentProvider
from modules.flow_engine.public import FlowEngineAdminProvider
from modules.learning_session.public import LearningSessionProvider
from modules.lesson_catalog.public import LessonCatalogProvider
from modules.llm_services.public import LLMServicesAdminProvider

# ---- DTOs for Admin Module ----


class FlowRunSummary(BaseModel):
    """Summary view of a flow run for list displays."""

    id: str
    flow_name: str
    status: str  # pending, running, completed, failed, cancelled
    execution_mode: str  # sync, async, background
    user_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    execution_time_ms: int | None
    total_tokens: int
    total_cost: float
    step_count: int
    error_message: str | None


class FlowStepDetails(BaseModel):
    """Detailed view of a flow step execution."""

    id: str
    flow_run_id: str
    llm_request_id: str | None
    step_name: str
    step_order: int
    status: str  # pending, running, completed, failed
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    tokens_used: int | None
    cost_estimate: float | None
    execution_time_ms: int | None
    error_message: str | None
    step_metadata: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


class FlowRunDetails(BaseModel):
    """Detailed view of a flow run with all steps."""

    id: str
    flow_name: str
    status: str
    execution_mode: str
    user_id: str | None
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    current_step: str | None
    step_progress: int
    total_steps: int | None
    progress_percentage: float | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    execution_time_ms: int | None
    last_heartbeat: datetime | None
    total_tokens: int
    total_cost: float
    error_message: str | None
    steps: list[FlowStepDetails]


class FlowRunsListResponse(BaseModel):
    """Paginated response for flow runs list."""

    flows: list[FlowRunSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class LLMRequestDetails(BaseModel):
    """Detailed view of an LLM request."""

    id: str
    user_id: str | None
    api_variant: str
    provider: str
    model: str
    provider_response_id: str | None
    system_fingerprint: str | None
    temperature: float
    max_output_tokens: int | None
    messages: list[dict[str, Any]]
    additional_params: dict[str, Any] | None
    request_payload: dict[str, Any] | None
    response_content: str | None
    response_raw: dict[str, Any] | None
    response_output: dict[str, Any] | list[dict[str, Any]] | None
    tokens_used: int | None
    input_tokens: int | None
    output_tokens: int | None
    cost_estimate: float | None
    response_created_at: datetime | None
    status: str
    execution_time_ms: int | None
    error_message: str | None
    error_type: str | None
    retry_attempt: int
    cached: bool
    created_at: datetime


# ---- Service Implementation ----


class AdminService:
    """Minimal service layer for admin dashboard functionality."""

    def __init__(
        self,
        flow_engine_admin: FlowEngineAdminProvider,
        llm_services_admin: LLMServicesAdminProvider,
        content: ContentProvider,
        lesson_catalog: LessonCatalogProvider,
        learning_sessions: LearningSessionProvider,
    ) -> None:
        self.flow_engine_admin = flow_engine_admin
        self.llm_services_admin = llm_services_admin
        self.content = content
        self.lesson_catalog = lesson_catalog
        self.learning_sessions = learning_sessions

    # ---- Flow Management ----

    async def get_flow_runs(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> FlowRunsListResponse:
        """Get paginated list of recent flow runs."""
        offset = (page - 1) * page_size

        # Get recent flow runs
        flow_models = self.flow_engine_admin.get_recent_flow_runs(limit=page_size, offset=offset)

        # Get total count for pagination
        total_count = self.flow_engine_admin.count_flow_runs()

        # Convert to DTOs
        flows = []
        for flow_model in flow_models:
            # Get step count for this flow
            if flow_model.id:
                steps = self.flow_engine_admin.get_flow_steps_by_run_id(flow_model.id)
            else:
                steps = []
            flows.append(
                FlowRunSummary(
                    id=str(flow_model.id),
                    flow_name=flow_model.flow_name or "Unknown",
                    status=flow_model.status or "unknown",
                    execution_mode=flow_model.execution_mode or "sync",
                    user_id=str(flow_model.user_id) if flow_model.user_id else None,
                    created_at=flow_model.created_at or datetime.now(),
                    started_at=flow_model.started_at,
                    completed_at=flow_model.completed_at,
                    execution_time_ms=flow_model.execution_time_ms,
                    total_tokens=flow_model.total_tokens or 0,
                    total_cost=flow_model.total_cost or 0.0,
                    step_count=len(steps),
                    error_message=flow_model.error_message,
                )
            )

        return FlowRunsListResponse(
            flows=flows,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size,
        )

    async def get_flow_run_details(self, flow_run_id: str) -> FlowRunDetails | None:
        """Get detailed view of a flow run with all steps."""
        try:
            flow_uuid = uuid.UUID(flow_run_id)
        except ValueError:
            return None

        flow_model = self.flow_engine_admin.get_flow_run_by_id(flow_uuid)
        if not flow_model:
            return None

        # Get all steps for this flow
        if flow_model.id:
            step_models = self.flow_engine_admin.get_flow_steps_by_run_id(flow_model.id)
        else:
            step_models = []

        steps = []
        for step_model in step_models:
            steps.append(
                FlowStepDetails(
                    id=str(step_model.id),
                    flow_run_id=str(step_model.flow_run_id),
                    llm_request_id=str(step_model.llm_request_id) if step_model.llm_request_id else None,
                    step_name=step_model.step_name or "Unknown",
                    step_order=step_model.step_order or 0,
                    status=step_model.status or "unknown",
                    inputs=step_model.inputs or {},
                    outputs=step_model.outputs,
                    tokens_used=step_model.tokens_used,
                    cost_estimate=step_model.cost_estimate,
                    execution_time_ms=step_model.execution_time_ms,
                    error_message=step_model.error_message,
                    step_metadata=step_model.step_metadata,
                    created_at=step_model.created_at or datetime.now(),
                    completed_at=step_model.completed_at,
                )
            )

        return FlowRunDetails(
            id=str(flow_model.id),
            flow_name=flow_model.flow_name or "Unknown",
            status=flow_model.status or "unknown",
            execution_mode=flow_model.execution_mode or "sync",
            user_id=str(flow_model.user_id) if flow_model.user_id else None,
            inputs=flow_model.inputs or {},
            outputs=flow_model.outputs,
            current_step=flow_model.current_step,
            step_progress=flow_model.step_progress or 0,
            total_steps=flow_model.total_steps,
            progress_percentage=flow_model.progress_percentage,
            created_at=flow_model.created_at or datetime.now(),
            started_at=flow_model.started_at,
            completed_at=flow_model.completed_at,
            execution_time_ms=flow_model.execution_time_ms,
            last_heartbeat=flow_model.last_heartbeat,
            total_tokens=flow_model.total_tokens or 0,
            total_cost=flow_model.total_cost or 0.0,
            error_message=flow_model.error_message,
            steps=steps,
        )

    async def get_flow_step_details(self, step_run_id: str) -> FlowStepDetails | None:
        """Get detailed view of a flow step."""
        try:
            step_uuid = uuid.UUID(step_run_id)
        except ValueError:
            return None

        step_model = self.flow_engine_admin.get_flow_step_by_id(step_uuid)
        if not step_model:
            return None

        return FlowStepDetails(
            id=str(step_model.id),
            flow_run_id=str(step_model.flow_run_id),
            llm_request_id=str(step_model.llm_request_id) if step_model.llm_request_id else None,
            step_name=step_model.step_name or "Unknown",
            step_order=step_model.step_order or 0,
            status=step_model.status or "unknown",
            inputs=step_model.inputs or {},
            outputs=step_model.outputs,
            tokens_used=step_model.tokens_used,
            cost_estimate=step_model.cost_estimate,
            execution_time_ms=step_model.execution_time_ms,
            error_message=step_model.error_message,
            step_metadata=step_model.step_metadata,
            created_at=step_model.created_at or datetime.now(),
            completed_at=step_model.completed_at,
        )

    # ---- LLM Request Management ----

    async def get_llm_request_details(self, request_id: str) -> LLMRequestDetails | None:
        """Get detailed view of an LLM request."""
        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return None

        # Get LLM request through public interface
        llm_request = self.llm_services_admin.get_request(request_uuid)
        if not llm_request:
            return None

        # Convert LLMRequest DTO to LLMRequestDetails DTO
        return LLMRequestDetails(
            id=str(llm_request.id),
            user_id=str(llm_request.user_id) if llm_request.user_id else None,
            api_variant=llm_request.api_variant,
            provider=llm_request.provider,
            model=llm_request.model,
            provider_response_id=llm_request.provider_response_id,
            system_fingerprint=llm_request.system_fingerprint,
            temperature=llm_request.temperature,
            max_output_tokens=llm_request.max_output_tokens,
            messages=llm_request.messages,
            additional_params=llm_request.additional_params,
            request_payload=llm_request.request_payload,
            response_content=llm_request.response_content,
            response_raw=llm_request.response_raw,
            response_output=getattr(llm_request, "response_output", None),
            tokens_used=llm_request.tokens_used,
            input_tokens=llm_request.input_tokens,
            output_tokens=llm_request.output_tokens,
            cost_estimate=llm_request.cost_estimate,
            response_created_at=llm_request.response_created_at,
            status=llm_request.status,
            execution_time_ms=llm_request.execution_time_ms,
            error_message=llm_request.error_message,
            error_type=llm_request.error_type,
            retry_attempt=llm_request.retry_attempt,
            cached=llm_request.cached,
            created_at=llm_request.created_at,
        )
