"""API routes for the learning coach module."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from modules.infrastructure.public import infrastructure_provider

from .dtos import LearningCoachMessage, LearningCoachSessionState
from .service import LearningCoachService

router = APIRouter(prefix="/api/v1/learning_coach", tags=["learning_coach"])


class LearningCoachMessageModel(BaseModel):
    """Response model mirroring a single conversation message."""

    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]


class LearningCoachSessionStateModel(BaseModel):
    """Response model for the conversation state."""

    conversation_id: str
    messages: list[LearningCoachMessageModel]
    metadata: dict[str, Any]
    finalized_topic: str | None = None
    unit_title: str | None = None
    learning_objectives: list[str] | None = None
    suggested_lesson_count: int | None = None
    proposed_brief: dict[str, Any] | None = None
    accepted_brief: dict[str, Any] | None = None


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


def get_learning_coach_service() -> LearningCoachService:
    """Resolve the learning coach service with shared infrastructure."""

    infra = infrastructure_provider()
    infra.initialize()
    return LearningCoachService(infrastructure=infra)


@router.post("/session/start", response_model=LearningCoachSessionStateModel, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: StartSessionRequest,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Create a new learning coach conversation and return the opening state."""

    state = await service.start_session(topic=request.topic, user_id=request.user_id)
    return _serialize_state(state)


@router.post("/session/message", response_model=LearningCoachSessionStateModel)
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


@router.post("/session/accept", response_model=LearningCoachSessionStateModel)
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


@router.get("/session/{conversation_id}", response_model=LearningCoachSessionStateModel)
async def get_session_state(
    conversation_id: str,
    include_system_messages: bool = False,
    service: LearningCoachService = Depends(get_learning_coach_service),
) -> LearningCoachSessionStateModel:
    """Fetch the latest state for a learning coach conversation."""

    state = await service.get_session_state(conversation_id, include_system_messages=include_system_messages)
    return _serialize_state(state)


def _serialize_state(state: LearningCoachSessionState) -> LearningCoachSessionStateModel:
    """Convert an internal DTO into an API response model."""

    return LearningCoachSessionStateModel(
        conversation_id=state.conversation_id,
        messages=[_serialize_message(message) for message in state.messages],
        metadata=state.metadata,
        finalized_topic=state.finalized_topic,
        unit_title=state.unit_title,
        learning_objectives=state.learning_objectives,
        suggested_lesson_count=state.suggested_lesson_count,
        proposed_brief=state.proposed_brief,
        accepted_brief=state.accepted_brief,
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


__all__ = [
    "router",
]
