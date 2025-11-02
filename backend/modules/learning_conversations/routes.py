"""API routes for learning conversations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from modules.infrastructure.public import infrastructure_provider

from .dtos import (
    UNSET,
    LearningCoachMessage,
    LearningCoachResource,
    LearningCoachSessionState,
    TeachingAssistantContext,
    TeachingAssistantMessage,
    TeachingAssistantSessionState,
)
from .service import LearningCoachService

router = APIRouter(prefix="/api/v1/learning_conversations", tags=["learning_conversations"])


class LearningCoachMessageModel(BaseModel):
    """Response model mirroring a single conversation message."""

    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]


class LearningObjectiveModel(BaseModel):
    """Response model for a unit learning objective."""

    id: str
    title: str
    description: str


class LearningCoachSessionStateModel(BaseModel):
    """Response model for the conversation state."""

    conversation_id: str
    messages: list[LearningCoachMessageModel]
    metadata: dict[str, Any]
    finalized_topic: str | None = None
    unit_title: str | None = None
    learning_objectives: list[LearningObjectiveModel] | None = None
    suggested_lesson_count: int | None = None
    proposed_brief: dict[str, Any] | None = None
    accepted_brief: dict[str, Any] | None = None
    resources: list[ResourceSummaryModel] = Field(default_factory=list)
    uncovered_learning_objective_ids: list[str] | None = Field(
        default=PydanticUndefined,
        description="Learning objective identifiers that require supplemental coverage.",
    )


class StartSessionRequest(BaseModel):
    """Payload to kick off a learning coach session."""

    topic: str | None = Field(default=None, description="Optional topic hint supplied by the learner")
    user_id: int | None = Field(default=None, description="Authenticated learner identifier", ge=1)


class LearnerTurnRequest(BaseModel):
    """Payload capturing a learner response."""

    conversation_id: str = Field(..., description="Existing learning coach conversation identifier")
    message: str = Field(..., min_length=1, description="Learner message content")
    user_id: int | None = Field(default=None, description="Authenticated learner identifier", ge=1)


class AcceptBriefRequest(BaseModel):
    """Payload confirming acceptance of a proposed brief."""

    conversation_id: str = Field(..., description="Existing learning coach conversation identifier")
    brief: dict[str, Any] = Field(..., description="Structured brief supplied by the coach")
    user_id: int | None = Field(default=None, description="Authenticated learner identifier", ge=1)


class AttachResourceRequest(BaseModel):
    """Payload to associate an uploaded resource with a conversation."""

    resource_id: uuid.UUID = Field(..., description="Identifier of the resource to attach")
    user_id: int | None = Field(default=None, description="Authenticated learner identifier", ge=1)


class ResourceSummaryModel(BaseModel):
    """Response model describing a conversation resource."""

    id: uuid.UUID
    resource_type: str
    filename: str | None = None
    source_url: str | None = None
    file_size: int | None = None
    created_at: datetime
    preview_text: str


class TeachingAssistantMessageModel(BaseModel):
    """Serialized teaching assistant message."""

    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]
    suggested_quick_replies: list[str] = Field(default_factory=list)


class TeachingAssistantContextModel(BaseModel):
    """Structured context included with teaching assistant responses."""

    unit_id: str
    lesson_id: str | None = None
    session_id: str | None = None
    session: dict[str, Any] | None = None
    exercise_attempt_history: list[dict[str, Any]] = Field(default_factory=list)
    lesson: dict[str, Any] | None = None
    unit: dict[str, Any] | None = None
    unit_session: dict[str, Any] | None = None
    unit_resources: list[dict[str, Any]] = Field(default_factory=list)


class TeachingAssistantSessionStateModel(BaseModel):
    """API response model for teaching assistant session state."""

    conversation_id: str
    unit_id: str
    lesson_id: str | None
    session_id: str | None
    messages: list[TeachingAssistantMessageModel]
    suggested_quick_replies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any]
    context: TeachingAssistantContextModel


class TeachingAssistantStartRequest(BaseModel):
    """Request payload for starting or resuming a teaching assistant session."""

    unit_id: str = Field(..., description="Unit identifier that scopes the conversation")
    lesson_id: str | None = Field(default=None, description="Current lesson identifier")
    session_id: str | None = Field(default=None, description="Active learning session identifier")
    user_id: int | None = Field(default=None, ge=1, description="Authenticated learner identifier")


class TeachingAssistantQuestionRequest(BaseModel):
    """Request payload for submitting a teaching assistant question."""

    conversation_id: str = Field(..., description="Existing teaching assistant conversation identifier")
    message: str = Field(..., min_length=1, description="Learner message content")
    unit_id: str = Field(..., description="Unit identifier that scopes the conversation")
    lesson_id: str | None = Field(default=None, description="Current lesson identifier")
    session_id: str | None = Field(default=None, description="Active learning session identifier")
    user_id: int | None = Field(default=None, ge=1, description="Authenticated learner identifier")


def get_learning_coach_service() -> LearningCoachService:
    """Resolve the learning coach service with shared infrastructure."""

    infra = infrastructure_provider()
    infra.initialize()
    return LearningCoachService(infrastructure=infra)


@router.post("/coach/session/start", response_model=LearningCoachSessionStateModel, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: StartSessionRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Create a new learning coach conversation and return the opening state."""

    state = await service.start_session(topic=request.topic, user_id=request.user_id)
    return _serialize_state(state)


@router.post("/coach/session/message", response_model=LearningCoachSessionStateModel)
async def submit_learner_turn(
    request: LearnerTurnRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Append a learner message and return the updated conversation state."""

    state = await service.submit_learner_turn(
        conversation_id=request.conversation_id,
        message=request.message,
        user_id=request.user_id,
    )
    return _serialize_state(state)


@router.post("/coach/session/accept", response_model=LearningCoachSessionStateModel)
async def accept_brief(
    request: AcceptBriefRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Mark the coach's current proposal as accepted."""

    if not isinstance(request.brief, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Brief must be an object")

    state = await service.accept_brief(
        conversation_id=request.conversation_id,
        brief=request.brief,
        user_id=request.user_id,
    )
    return _serialize_state(state)


@router.get("/coach/session/{conversation_id}", response_model=LearningCoachSessionStateModel)
async def get_session_state(
    conversation_id: str,
    include_system_messages: bool = False,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Fetch the latest state for a learning coach conversation."""

    state = await service.get_session_state(conversation_id, include_system_messages=include_system_messages)
    return _serialize_state(state)


@router.post(
    "/coach/conversations/{conversation_id}/resources",
    response_model=LearningCoachSessionStateModel,
    status_code=status.HTTP_200_OK,
)
async def attach_resource(
    conversation_id: str,
    request: AttachResourceRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Attach a learner resource to the specified learning coach conversation."""

    try:
        state = await service.attach_resource(
            conversation_id=conversation_id,
            resource_id=request.resource_id,
            user_id=request.user_id,
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return _serialize_state(state)


@router.post(
    "/teaching_assistant/start",
    response_model=TeachingAssistantSessionStateModel,
    status_code=status.HTTP_201_CREATED,
)
async def start_teaching_assistant(
    request: TeachingAssistantStartRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> TeachingAssistantSessionStateModel:
    """Start or resume a teaching assistant conversation."""

    state = await service.start_teaching_assistant_session(
        unit_id=request.unit_id,
        lesson_id=request.lesson_id,
        session_id=request.session_id,
        user_id=request.user_id,
    )
    return _serialize_teaching_assistant_state(state)


@router.post(
    "/teaching_assistant/ask",
    response_model=TeachingAssistantSessionStateModel,
)
async def submit_teaching_assistant_question(
    request: TeachingAssistantQuestionRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> TeachingAssistantSessionStateModel:
    """Submit a learner turn to the teaching assistant."""

    try:
        state = await service.submit_teaching_assistant_question(
            conversation_id=request.conversation_id,
            message=request.message,
            unit_id=request.unit_id,
            lesson_id=request.lesson_id,
            session_id=request.session_id,
            user_id=request.user_id,
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _serialize_teaching_assistant_state(state)


@router.get(
    "/teaching_assistant/{conversation_id}",
    response_model=TeachingAssistantSessionStateModel,
)
async def get_teaching_assistant_session_state(
    conversation_id: str,
    unit_id: str = Query(..., description="Unit identifier that scopes the conversation"),
    lesson_id: str | None = Query(None, description="Current lesson identifier"),
    session_id: str | None = Query(None, description="Active learning session identifier"),
    user_id: int | None = Query(None, ge=1, description="Authenticated learner identifier"),
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> TeachingAssistantSessionStateModel:
    """Return the latest teaching assistant session state."""

    try:
        state = await service.get_teaching_assistant_session_state(
            conversation_id=conversation_id,
            unit_id=unit_id,
            lesson_id=lesson_id,
            session_id=session_id,
            user_id=user_id,
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _serialize_teaching_assistant_state(state)


def _serialize_state(state: LearningCoachSessionState) -> LearningCoachSessionStateModel:
    """Convert an internal DTO into an API response model."""
    payload: dict[str, Any] = {
        "conversation_id": state.conversation_id,
        "messages": [_serialize_message(message) for message in state.messages],
        "metadata": state.metadata,
        "finalized_topic": state.finalized_topic,
        "unit_title": state.unit_title,
        "learning_objectives": [LearningObjectiveModel(id=obj.id, title=obj.title, description=obj.description) for obj in state.learning_objectives or []] if state.learning_objectives else None,
        "suggested_lesson_count": state.suggested_lesson_count,
        "proposed_brief": state.proposed_brief,
        "accepted_brief": state.accepted_brief,
        "resources": [_serialize_resource(resource) for resource in state.resources],
    }

    fields_set = set(payload.keys())
    if state.uncovered_learning_objective_ids is not UNSET:
        payload["uncovered_learning_objective_ids"] = state.uncovered_learning_objective_ids
        fields_set.add("uncovered_learning_objective_ids")

    return LearningCoachSessionStateModel.model_construct(
        _fields_set=fields_set,
        **payload,
    )


def _serialize_message(message: LearningCoachMessage) -> LearningCoachMessageModel:
    """Convert an internal message DTO to API representation."""

    return LearningCoachMessageModel(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        metadata=message.metadata,
    )


def _serialize_teaching_assistant_state(state: TeachingAssistantSessionState) -> TeachingAssistantSessionStateModel:
    """Convert the teaching assistant DTO into an API response model."""

    return TeachingAssistantSessionStateModel(
        conversation_id=state.conversation_id,
        unit_id=state.unit_id,
        lesson_id=state.lesson_id,
        session_id=state.session_id,
        messages=[_serialize_teaching_assistant_message(message) for message in state.messages],
        suggested_quick_replies=state.suggested_quick_replies,
        metadata=state.metadata,
        context=_serialize_teaching_assistant_context(state.context),
    )


def _serialize_teaching_assistant_message(message: TeachingAssistantMessage) -> TeachingAssistantMessageModel:
    """Convert a teaching assistant message DTO into response format."""

    return TeachingAssistantMessageModel(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        metadata=message.metadata,
        suggested_quick_replies=message.suggested_quick_replies,
    )


def _serialize_teaching_assistant_context(context: TeachingAssistantContext) -> TeachingAssistantContextModel:
    """Convert teaching assistant context data into the API model."""

    return TeachingAssistantContextModel(
        unit_id=context.unit_id,
        lesson_id=context.lesson_id,
        session_id=context.session_id,
        session=context.session,
        exercise_attempt_history=context.exercise_attempt_history,
        lesson=context.lesson,
        unit=context.unit,
        unit_session=context.unit_session,
        unit_resources=context.unit_resources,
    )


def _serialize_resource(resource: LearningCoachResource) -> ResourceSummaryModel:
    """Convert a resource DTO into the API response model."""

    return ResourceSummaryModel(
        id=uuid.UUID(str(resource.id)),
        resource_type=resource.resource_type,
        filename=resource.filename,
        source_url=resource.source_url,
        file_size=resource.file_size,
        created_at=resource.created_at,
        preview_text=resource.preview_text,
    )


__all__ = [
    "router",
]
