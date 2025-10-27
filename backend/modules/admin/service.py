# /backend/modules/admin/service.py
"""
Admin Module - Service Layer

Minimal service for admin dashboard functionality.
Returns DTOs for all admin functionality.
"""

from datetime import UTC, datetime
from typing import Any
import uuid

from modules.catalog.public import CatalogProvider
from modules.content.public import ContentProvider
from modules.conversation_engine.public import ConversationEngineProvider
from modules.flow_engine.public import FlowEngineAdminProvider
from modules.learning_coach.public import LearningCoachProvider
from modules.learning_session.public import LearningSession, LearningSessionProvider
from modules.llm_services.public import LLMServicesAdminProvider
from modules.user.public import UserProvider, UserRead

from .models import (
    FlowRunDetails,
    FlowRunsListResponse,
    FlowRunSummary,
    FlowStepDetails,
    LearningCoachConversationDetail,
    LearningCoachConversationsListResponse,
    LearningCoachConversationSummaryAdmin,
    LearningCoachMessageAdmin,
    LearningSessionSummary,
    LearningSessionsListResponse,
    LessonDetails,
    LessonsListResponse,
    LessonSummary,
    LLMRequestDetails,
    LLMRequestsListResponse,
    LLMRequestSummary,
    UserAssociationSummary,
    UserConversationSummary,
    UserDetail,
    UserListResponse,
    UserLLMRequestSummary,
    UserOwnedUnitSummary,
    UserSessionSummary,
    UserSummary,
    UserUpdateRequest,
)

LEARNING_COACH_CONVERSATION_TYPE = "learning_coach"


class AdminService:
    """Minimal service layer for admin dashboard functionality."""

    def __init__(
        self,
        flow_engine_admin: FlowEngineAdminProvider,
        llm_services_admin: LLMServicesAdminProvider,
        catalog: CatalogProvider,
        content: ContentProvider,
        users: UserProvider,
        learning_sessions: LearningSessionProvider | None = None,
        learning_coach: LearningCoachProvider | None = None,
        conversation_engine: ConversationEngineProvider | None = None,
    ) -> None:
        """Initialize admin service with required dependencies."""
        self.flow_engine_admin = flow_engine_admin
        self.llm_services_admin = llm_services_admin
        self.catalog = catalog
        self.content = content
        self.users = users
        self.learning_sessions = learning_sessions
        self.learning_coach = learning_coach
        self.conversation_engine = conversation_engine

    # ---- User Management ----

    async def get_users(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
    ) -> UserListResponse:
        """Return paginated user summaries with association counts."""

        all_users = self.users.list_users(search=search)
        total = len(all_users)
        page = max(page, 1)
        start = (page - 1) * page_size
        end = start + page_size
        visible = all_users[start:end]

        summaries: list[UserSummary] = []
        for user in visible:
            associations = await self._build_user_associations(user)
            summaries.append(
                UserSummary(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    role=user.role,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    associations=associations,
                )
            )

        has_next = end < total
        return UserListResponse(
            users=summaries,
            total_count=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    async def get_user_detail(self, user_id: int) -> UserDetail | None:
        """Return detailed user profile with associations for admin view."""

        user = self.users.get_profile(user_id)
        if not user:
            return None

        associations = await self._build_user_associations(user)

        owned_units_data = await self.content.list_units_for_user(user.id, limit=100)
        owned_units = [
            UserOwnedUnitSummary(
                id=unit.id,
                title=unit.title,
                is_global=bool(getattr(unit, "is_global", False)),
                updated_at=unit.updated_at,
                art_image_url=getattr(unit, "art_image_url", None),
                art_image_description=getattr(unit, "art_image_description", None),
            )
            for unit in owned_units_data
        ]

        recent_sessions = await self._get_recent_sessions(user)
        recent_llm_requests = self._get_recent_llm_requests(user)
        user_id_int = self._coerce_user_int(user)
        recent_conversations = await self.get_user_conversations(user_id_int) if user_id_int is not None else []

        return UserDetail(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            associations=associations,
            owned_units=owned_units,
            recent_sessions=recent_sessions,
            recent_llm_requests=recent_llm_requests,
            recent_conversations=recent_conversations,
        )

    async def update_user(self, user_id: int, payload: UserUpdateRequest) -> UserDetail | None:
        """Apply admin-controlled updates and return refreshed detail."""

        try:
            self.users.update_user_admin(
                user_id,
                name=payload.name,
                role=payload.role,
                is_active=payload.is_active,
            )
        except ValueError:
            return None

        return await self.get_user_detail(user_id)

    async def list_learning_coach_conversations(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
    ) -> LearningCoachConversationsListResponse:
        """Return paginated learning coach conversations for QA."""

        if not self.conversation_engine:
            return LearningCoachConversationsListResponse(
                conversations=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False,
            )

        page = max(page, 1)
        page_size = max(page_size, 1)
        offset = (page - 1) * page_size

        summaries = await self._fetch_learning_coach_conversations(
            limit=page_size + 1,
            offset=offset,
            status=status,
        )

        has_next = len(summaries) > page_size
        visible = summaries[:page_size]

        conversations = [
            LearningCoachConversationSummaryAdmin(
                id=summary.id,
                user_id=summary.user_id,
                title=summary.title,
                status=summary.status,
                message_count=summary.message_count,
                created_at=summary.created_at,
                updated_at=summary.updated_at,
                last_message_at=summary.last_message_at,
                metadata=dict(summary.metadata or {}),
            )
            for summary in visible
        ]

        total_count = await self._count_learning_coach_conversations(status=status)

        return LearningCoachConversationsListResponse(
            conversations=conversations,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    async def get_learning_coach_conversation(self, conversation_id: str) -> LearningCoachConversationDetail | None:
        """Return transcript-level detail for a learning coach conversation."""

        if not self.conversation_engine:
            return None

        try:
            conversation_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return None

        detail = await self.conversation_engine.get_conversation(conversation_uuid)

        messages = [
            LearningCoachMessageAdmin(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                metadata=dict(message.metadata or {}),
                tokens_used=message.tokens_used,
                cost_estimate=message.cost_estimate,
                llm_request_id=message.llm_request_id,
                message_order=message.message_order,
            )
            for message in detail.messages
        ]

        metadata = dict(detail.metadata or {})

        return LearningCoachConversationDetail(
            conversation_id=detail.id,
            messages=messages,
            metadata=metadata,
            proposed_brief=self._dict_or_none(metadata.get("proposed_brief")),
            accepted_brief=self._dict_or_none(metadata.get("accepted_brief")),
        )

    async def get_user_conversations(self, user_id: int, *, limit: int = 5) -> list[UserConversationSummary]:
        """Return recent learning coach conversations for a user."""

        if not self.conversation_engine:
            return []

        summaries = await self.conversation_engine.list_conversations_for_user(
            user_id,
            limit=limit,
            offset=0,
            conversation_type=LEARNING_COACH_CONVERSATION_TYPE,
        )

        return [
            UserConversationSummary(
                id=summary.id,
                title=summary.title,
                status=summary.status,
                message_count=summary.message_count,
                last_message_at=summary.last_message_at,
            )
            for summary in summaries
        ]

    async def _fetch_learning_coach_conversations(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        user_id: int | None = None,
    ) -> list[Any]:
        if not self.conversation_engine:
            return []

        if user_id is not None:
            return await self.conversation_engine.list_conversations_for_user(
                user_id,
                limit=limit,
                offset=offset,
                conversation_type=LEARNING_COACH_CONVERSATION_TYPE,
                status=status,
            )

        return await self.conversation_engine.list_conversations_by_type(
            LEARNING_COACH_CONVERSATION_TYPE,
            limit=limit,
            offset=offset,
            status=status,
        )

    async def _has_learning_coach_conversation_at_offset(
        self,
        offset: int,
        *,
        status: str | None = None,
        user_id: int | None = None,
    ) -> bool:
        if offset < 0:
            return False
        conversations = await self._fetch_learning_coach_conversations(
            limit=1,
            offset=offset,
            status=status,
            user_id=user_id,
        )
        return bool(conversations)

    async def _count_learning_coach_conversations(
        self,
        *,
        status: str | None = None,
        user_id: int | None = None,
    ) -> int:
        if not self.conversation_engine:
            return 0

        if not await self._has_learning_coach_conversation_at_offset(0, status=status, user_id=user_id):
            return 0

        low = 1
        high = 2

        while await self._has_learning_coach_conversation_at_offset(high - 1, status=status, user_id=user_id):
            low = high
            high *= 2

        left = low
        right = high

        while left < right:
            mid = (left + right) // 2
            if await self._has_learning_coach_conversation_at_offset(mid, status=status, user_id=user_id):
                left = mid + 1
            else:
                right = mid

        return left

    async def _build_user_associations(self, user: UserRead) -> UserAssociationSummary:
        """Aggregate association counts for a user."""

        owned_units = await self.content.list_units_for_user(user.id, limit=100)
        owned_global_unit_count = sum(1 for unit in owned_units if getattr(unit, "is_global", False))
        learning_session_count = await self._get_learning_session_count(user)
        llm_request_count = self._get_llm_request_count(user)
        return UserAssociationSummary(
            owned_unit_count=len(owned_units),
            owned_global_unit_count=owned_global_unit_count,
            learning_session_count=learning_session_count,
            llm_request_count=llm_request_count,
        )

    async def _get_learning_session_count(self, user: UserRead) -> int:
        if not self.learning_sessions:
            return 0
        try:
            response = await self.learning_sessions.get_user_sessions(
                user_id=str(user.id),
                limit=1,
                offset=0,
            )
        except Exception:
            return 0
        return response.total

    async def _get_recent_sessions(self, user: UserRead, limit: int = 5) -> list[UserSessionSummary]:
        if not self.learning_sessions:
            return []
        try:
            response = await self.learning_sessions.get_user_sessions(
                user_id=str(user.id),
                limit=limit,
                offset=0,
            )
        except Exception:
            return []

        summaries: list[UserSessionSummary] = []
        for session in response.sessions:
            summaries.append(
                UserSessionSummary(
                    id=session.id,
                    lesson_id=session.lesson_id,
                    status=session.status,
                    started_at=session.started_at,
                    completed_at=session.completed_at,
                    progress_percentage=session.progress_percentage,
                )
            )
        return summaries

    def _get_llm_request_count(self, user: UserRead) -> int:
        user_uuid = self._coerce_user_uuid(user)
        if not user_uuid:
            return 0
        try:
            return self.llm_services_admin.get_request_count_by_user(user_uuid)
        except Exception:
            return 0

    def _get_recent_llm_requests(self, user: UserRead, limit: int = 5) -> list[UserLLMRequestSummary]:
        user_uuid = self._coerce_user_uuid(user)
        if not user_uuid:
            return []
        try:
            requests = self.llm_services_admin.get_user_requests(user_uuid, limit=limit, offset=0)
        except Exception:
            return []

        return [
            UserLLMRequestSummary(
                id=str(request.id),
                model=request.model,
                status=request.status,
                created_at=request.created_at,
                tokens_used=request.tokens_used,
            )
            for request in requests
        ]

    def _coerce_user_int(self, user: UserRead) -> int | None:
        if isinstance(user.id, int):
            return user.id
        if isinstance(user.id, str):
            try:
                return int(user.id)
            except ValueError:
                return None
        return None

    def _coerce_user_uuid(self, user: UserRead) -> uuid.UUID | None:
        if isinstance(user.id, uuid.UUID):
            return user.id
        if isinstance(user.id, str):
            try:
                return uuid.UUID(user.id)
            except ValueError:
                return None
        return None

    def _dict_or_none(self, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        return None

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                if value.endswith("Z"):
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        except TypeError:
            return None
        return None

    def _to_learning_session_summary(self, session: LearningSession) -> LearningSessionSummary:
        started_at = self._parse_datetime(session.started_at) or datetime.fromtimestamp(0, UTC)
        completed_at = self._parse_datetime(session.completed_at)
        return LearningSessionSummary(
            id=session.id,
            lesson_id=session.lesson_id,
            unit_id=session.unit_id,
            user_id=session.user_id,
            status=session.status,
            started_at=started_at,
            completed_at=completed_at,
            current_exercise_index=session.current_exercise_index,
            total_exercises=session.total_exercises,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data or {},
        )

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

    # ---- Learning Session Management ----

    async def get_learning_sessions(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        user_id: str | None = None,
        lesson_id: str | None = None,
    ) -> LearningSessionsListResponse:
        """Return paginated learning sessions for the admin dashboard."""

        page = max(page, 1)
        page_size = max(page_size, 1)
        offset = (page - 1) * page_size

        if not self.learning_sessions:
            return LearningSessionsListResponse(
                sessions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False,
            )

        try:
            response = await self.learning_sessions.list_sessions(
                user_id=user_id,
                status=status,
                lesson_id=lesson_id,
                limit=page_size,
                offset=offset,
            )
        except Exception:
            return LearningSessionsListResponse(
                sessions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_next=False,
            )

        session_summaries = [self._to_learning_session_summary(session) for session in response.sessions]
        has_next = offset + len(session_summaries) < response.total

        return LearningSessionsListResponse(
            sessions=session_summaries,
            total_count=response.total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    async def get_learning_session_detail(self, session_id: str) -> LearningSessionSummary | None:
        """Return detailed learning session data for a specific session."""

        if not self.learning_sessions:
            return None

        try:
            session = await self.learning_sessions.get_session_admin(session_id)
        except Exception:
            return None

        if not session:
            return None

        return self._to_learning_session_summary(session)

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
            search_response = await self.catalog.search_lessons(
                query=search,
                learner_level=learner_level,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

            # Convert lesson catalog DTOs to admin DTOs
            lesson_summaries = []
            for lesson in search_response.lessons:
                # Get the full lesson data from content module to access package_version, created_at, etc.
                full_lesson = await self.content.get_lesson(lesson.id)
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
            lesson = await self.content.get_lesson(lesson_id)
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
