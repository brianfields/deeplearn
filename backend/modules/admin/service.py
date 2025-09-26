# /backend/modules/admin/service.py
"""
Admin Module - Service Layer

Minimal service for admin dashboard functionality.
Returns DTOs for all admin functionality.
"""

from datetime import datetime
import uuid

from modules.catalog.public import CatalogProvider
from modules.content.public import ContentProvider
from modules.flow_engine.public import FlowEngineAdminProvider
from modules.llm_services.public import LLMServicesAdminProvider

from .models import (
    FlowRunDetails,
    FlowRunsListResponse,
    FlowRunSummary,
    FlowStepDetails,
    LessonDetails,
    LessonsListResponse,
    LessonSummary,
    LLMRequestDetails,
    LLMRequestsListResponse,
    LLMRequestSummary,
)


class AdminService:
    """Minimal service layer for admin dashboard functionality."""

    def __init__(
        self,
        flow_engine_admin: FlowEngineAdminProvider,
        llm_services_admin: LLMServicesAdminProvider,
        catalog: CatalogProvider,
        content: ContentProvider,
    ) -> None:
        """Initialize admin service with required dependencies."""
        self.flow_engine_admin = flow_engine_admin
        self.llm_services_admin = llm_services_admin
        self.catalog = catalog
        self.content = content

    # ---- Flow Management ----

    async def get_flow_runs(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> FlowRunsListResponse:
        """Get paginated list of flow runs (minimal implementation)."""
        try:
            # Get flow runs through public interface
            flow_models = self.flow_engine_admin.get_recent_flow_runs(limit=page_size, offset=(page - 1) * page_size)
            total_count = self.flow_engine_admin.count_flow_runs()

            # Convert to DTOs
            flow_summaries = []
            for flow_model in flow_models:
                # Get step count for this flow
                try:
                    flow_uuid = uuid.UUID(str(flow_model.id))
                    steps = self.flow_engine_admin.get_flow_steps_by_run_id(flow_uuid)
                except (ValueError, TypeError):
                    steps = []

                # Calculate totals from steps
                total_tokens = sum(step.tokens_used or 0 for step in steps)
                total_cost = sum(step.cost_estimate or 0 for step in steps)

                flow_summaries.append(
                    FlowRunSummary(
                        id=str(flow_model.id),
                        flow_name=flow_model.flow_name or "Unknown Flow",
                        status=flow_model.status or "unknown",
                        execution_mode=flow_model.execution_mode or "unknown",
                        user_id=str(flow_model.user_id) if flow_model.user_id else None,
                        created_at=flow_model.created_at or datetime.now(),
                        started_at=flow_model.started_at,
                        completed_at=flow_model.completed_at,
                        execution_time_ms=flow_model.execution_time_ms,
                        total_tokens=total_tokens,
                        total_cost=total_cost,
                        step_count=len(steps),
                        error_message=flow_model.error_message,
                    )
                )

            # Determine if there is a next page using total count
            has_next = ((page - 1) * page_size) + len(flow_summaries) < total_count

            return FlowRunsListResponse(
                flows=flow_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next,
            )

        except Exception:
            # Return empty response on error
            return FlowRunsListResponse(
                flows=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False,
            )

    async def get_flow_run_details(self, flow_run_id: str) -> FlowRunDetails | None:
        """Get detailed view of a flow run with all steps."""
        try:
            flow_uuid = uuid.UUID(flow_run_id)
        except ValueError:
            return None

        # Get flow run through public interface
        flow_model = self.flow_engine_admin.get_flow_run_by_id(flow_uuid)
        if not flow_model:
            return None

        # Get steps for this flow
        try:
            if flow_model.id:
                flow_uuid = uuid.UUID(flow_model.id) if isinstance(flow_model.id, str) else flow_model.id
                step_models = self.flow_engine_admin.get_flow_steps_by_run_id(flow_uuid)
            else:
                step_models = []
        except (ValueError, TypeError):
            step_models = []

        # Convert steps to DTOs
        step_details = []
        total_tokens = 0
        total_cost = 0.0

        for step_model in step_models:
            tokens_used = step_model.tokens_used or 0
            cost_estimate = step_model.cost_estimate or 0.0
            total_tokens += tokens_used
            total_cost += cost_estimate

            step_details.append(
                FlowStepDetails(
                    id=str(step_model.id),
                    flow_run_id=str(step_model.flow_run_id),
                    llm_request_id=str(step_model.llm_request_id) if step_model.llm_request_id else None,
                    step_name=step_model.step_name or "Unknown Step",
                    step_order=step_model.step_order or 0,
                    status=step_model.status or "unknown",
                    inputs=step_model.inputs or {},
                    outputs=step_model.outputs,
                    tokens_used=tokens_used,
                    cost_estimate=cost_estimate,
                    execution_time_ms=step_model.execution_time_ms,
                    error_message=step_model.error_message,
                    step_metadata=step_model.step_metadata,
                    created_at=step_model.created_at or datetime.now(),
                    updated_at=getattr(step_model, "updated_at", None) or (step_model.created_at or datetime.now()),
                    completed_at=step_model.completed_at,
                )
            )

        # Calculate progress
        completed_steps = len([s for s in step_details if s.status == "completed"])
        total_steps = len(step_details)
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return FlowRunDetails(
            id=str(flow_model.id),
            flow_name=flow_model.flow_name or "Unknown Flow",
            status=flow_model.status or "unknown",
            execution_mode=flow_model.execution_mode or "unknown",
            user_id=str(flow_model.user_id) if flow_model.user_id else None,
            current_step=flow_model.current_step,
            step_progress=completed_steps,
            total_steps=total_steps,
            progress_percentage=progress_percentage,
            created_at=flow_model.created_at or datetime.now(),
            updated_at=getattr(flow_model, "updated_at", None) or (flow_model.created_at or datetime.now()),
            started_at=flow_model.started_at,
            completed_at=flow_model.completed_at,
            last_heartbeat=flow_model.last_heartbeat,
            execution_time_ms=flow_model.execution_time_ms,
            total_tokens=total_tokens,
            total_cost=total_cost,
            inputs=flow_model.inputs or {},
            outputs=flow_model.outputs,
            flow_metadata=flow_model.flow_metadata,
            error_message=flow_model.error_message,
            steps=step_details,
        )

    async def get_flow_step_details(self, step_run_id: str) -> FlowStepDetails | None:
        """Get detailed view of a flow step."""
        try:
            step_uuid = uuid.UUID(step_run_id)
        except ValueError:
            return None

        # Get step through public interface
        step_model = self.flow_engine_admin.get_flow_step_by_id(step_uuid)
        if not step_model:
            return None

        return FlowStepDetails(
            id=str(step_model.id),
            flow_run_id=str(step_model.flow_run_id),
            llm_request_id=str(step_model.llm_request_id) if step_model.llm_request_id else None,
            step_name=step_model.step_name or "Unknown Step",
            step_order=step_model.step_order or 0,
            status=step_model.status or "unknown",
            inputs=step_model.inputs or {},
            outputs=step_model.outputs,
            tokens_used=step_model.tokens_used or 0,
            cost_estimate=step_model.cost_estimate or 0.0,
            execution_time_ms=step_model.execution_time_ms,
            error_message=step_model.error_message,
            step_metadata=step_model.step_metadata,
            created_at=step_model.created_at or datetime.now(),
            updated_at=getattr(step_model, "updated_at", None) or (step_model.created_at or datetime.now()),
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
            updated_at=getattr(llm_request, "updated_at", llm_request.created_at),
        )

    async def get_llm_requests(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> LLMRequestsListResponse:
        """Get paginated list of LLM requests."""
        try:
            # Get LLM requests through public interface
            llm_requests = self.llm_services_admin.get_recent_requests(limit=page_size, offset=(page - 1) * page_size)
            total_count = self.llm_services_admin.count_all_requests()

            # Convert to DTOs
            request_summaries = []
            for llm_request in llm_requests:
                request_summaries.append(
                    LLMRequestSummary(
                        id=str(llm_request.id),
                        user_id=str(llm_request.user_id) if llm_request.user_id else None,
                        api_variant=llm_request.api_variant,
                        provider=llm_request.provider,
                        model=llm_request.model,
                        status=llm_request.status,
                        tokens_used=llm_request.tokens_used,
                        input_tokens=llm_request.input_tokens,
                        output_tokens=llm_request.output_tokens,
                        cost_estimate=llm_request.cost_estimate,
                        execution_time_ms=llm_request.execution_time_ms,
                        cached=llm_request.cached,
                        created_at=llm_request.created_at,
                        error_message=llm_request.error_message,
                    )
                )

            # Determine if there is a next page using total count
            has_next = ((page - 1) * page_size) + len(request_summaries) < total_count

            return LLMRequestsListResponse(
                requests=request_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next,
            )

        except Exception:
            # Return empty response on error
            return LLMRequestsListResponse(
                requests=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False,
            )

    # ---- Lesson Management ----

    async def get_lessons(
        self,
        learner_level: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> LessonsListResponse:
        """Get paginated list of lessons with optional filtering."""
        try:
            # Use search_lessons to get lessons with filtering
            search_response = self.catalog.search_lessons(
                query=search,
                learner_level=learner_level,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

            # Convert lesson catalog DTOs to admin DTOs
            lesson_summaries = []
            for lesson in search_response.lessons:
                # Get the full lesson data from content module to access package_version, created_at, etc.
                full_lesson = self.content.get_lesson(lesson.id)
                if full_lesson:
                    lesson_summaries.append(
                        LessonSummary(
                            id=lesson.id,
                            title=lesson.title,
                            learner_level=getattr(lesson, "learner_level", "beginner"),
                            package_version=full_lesson.package_version,
                            created_at=full_lesson.created_at,
                            updated_at=full_lesson.updated_at,
                        )
                    )

            # Calculate if there are more results
            has_next = len(search_response.lessons) == page_size

            return LessonsListResponse(
                lessons=lesson_summaries,
                total_count=search_response.total,
                page=page,
                page_size=page_size,
                has_next=has_next,
            )

        except Exception:
            # Return empty response on error
            return LessonsListResponse(
                lessons=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False,
            )

    async def get_lesson_details(self, lesson_id: str) -> LessonDetails | None:
        """Get detailed information about a specific lesson including its package."""

        try:
            # Get lesson from content provider directly to get full package structure
            lesson = self.content.get_lesson(lesson_id)
            if not lesson:
                return None

            # Convert the LessonPackage to dict for JSON serialization
            # The package already has the proper structure with meta, objectives, etc.
            package = lesson.package.model_dump()

            return LessonDetails(
                id=lesson.id,
                title=lesson.title,
                learner_level=getattr(lesson, "learner_level", "beginner"),
                source_material=lesson.source_material,
                package=package,  # Full package structure from content
                package_version=lesson.package_version,
                flow_run_id=str(lesson.flow_run_id) if lesson.flow_run_id else None,
                created_at=lesson.created_at,
                updated_at=lesson.updated_at,
            )

        except Exception:
            return None
