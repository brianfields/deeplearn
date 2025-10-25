# /backend/modules/admin/models.py
"""
Admin Module - Data Transfer Objects (DTOs)

DTOs for admin module data aggregation and API responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

# ---- Flow Management DTOs ----


class FlowRunSummary(BaseModel):
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


class FlowRunDetails(BaseModel):
    id: str
    flow_name: str
    status: str
    execution_mode: str
    user_id: str | None
    current_step: str | None
    step_progress: int
    total_steps: int | None
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
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
    steps: list["FlowStepDetails"]


class FlowStepDetails(BaseModel):
    id: str
    flow_run_id: str
    llm_request_id: str | None
    step_name: str
    step_order: int
    status: str  # pending, running, completed, failed
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    tokens_used: int
    cost_estimate: float
    execution_time_ms: int | None
    error_message: str | None
    step_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class FlowRunsListResponse(BaseModel):
    flows: list[FlowRunSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool


# ---- LLM Request DTOs ----


class LLMRequestSummary(BaseModel):
    id: str
    user_id: str | None
    api_variant: str
    provider: str
    model: str
    status: str  # pending, completed, failed
    tokens_used: int | None
    input_tokens: int | None
    output_tokens: int | None
    cost_estimate: float | None
    execution_time_ms: int | None
    cached: bool
    created_at: datetime
    error_message: str | None


class LLMRequestDetails(BaseModel):
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
    updated_at: datetime


class LLMRequestsListResponse(BaseModel):
    requests: list[LLMRequestSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool


# ---- Learning Coach Conversations ----


class LearningCoachMessageAdmin(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]
    tokens_used: int | None = None
    cost_estimate: float | None = None
    llm_request_id: str | None = None
    message_order: int | None = None


class LearningCoachConversationDetail(BaseModel):
    conversation_id: str
    messages: list[LearningCoachMessageAdmin]
    metadata: dict[str, Any]
    proposed_brief: dict[str, Any] | None = None
    accepted_brief: dict[str, Any] | None = None


class LearningCoachConversationSummaryAdmin(BaseModel):
    id: str
    user_id: int | None
    title: str | None
    status: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None
    metadata: dict[str, Any]


class LearningCoachConversationsListResponse(BaseModel):
    conversations: list[LearningCoachConversationSummaryAdmin]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class UserConversationSummary(BaseModel):
    id: str
    title: str | None
    status: str
    message_count: int
    last_message_at: datetime | None


# ---- Lesson Management DTOs ----


class LessonSummary(BaseModel):
    id: str
    title: str
    learner_level: str
    package_version: int
    created_at: datetime
    updated_at: datetime


class LessonDetails(BaseModel):
    id: str
    title: str
    learner_level: str
    source_material: str | None
    package: dict[str, Any]  # LessonPackage as dict
    package_version: int
    flow_run_id: str | None
    created_at: datetime
    updated_at: datetime


class LessonsListResponse(BaseModel):
    lessons: list[LessonSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool


# ---- User Management DTOs ----


class UserAssociationSummary(BaseModel):
    owned_unit_count: int
    owned_global_unit_count: int
    learning_session_count: int
    llm_request_count: int


class UserOwnedUnitSummary(BaseModel):
    id: str
    title: str
    is_global: bool
    updated_at: datetime
    art_image_url: str | None = None
    art_image_description: str | None = None


class UserSessionSummary(BaseModel):
    id: str
    lesson_id: str
    status: str
    started_at: str
    completed_at: str | None
    progress_percentage: float


class UserLLMRequestSummary(BaseModel):
    id: str
    model: str
    status: str
    created_at: datetime
    tokens_used: int | None


class UserSummary(BaseModel):
    id: int | str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    associations: UserAssociationSummary


class UserDetail(UserSummary):
    owned_units: list[UserOwnedUnitSummary]
    recent_sessions: list[UserSessionSummary]
    recent_llm_requests: list[UserLLMRequestSummary]
    recent_conversations: list[UserConversationSummary]


class UserUpdateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserListResponse(BaseModel):
    users: list[UserSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool
