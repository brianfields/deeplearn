"""HTTP routes exposing LLM services functionality."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from modules.infrastructure.public import infrastructure_provider

from .exceptions import LLMError
from .public import llm_services_provider
from .service import LLMMessage, LLMRequest, LLMResponse, LLMService

router = APIRouter(prefix="/api/v1/llm", tags=["LLM Services"])


def get_session() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""

    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as session:
        yield session


def get_llm_service(session: Session = Depends(get_session)) -> LLMService:
    """Build the LLM service instance for this request."""

    return cast(LLMService, llm_services_provider(session))


class MessagePayload(BaseModel):
    """Incoming payload for conversation messages."""

    role: str = Field(..., min_length=1, description="Message role such as system or user")
    content: str = Field(..., min_length=1, description="Message content to send to the model")
    name: str | None = Field(default=None, description="Optional speaker name")
    function_call: dict[str, Any] | None = Field(default=None, description="Serialized function call payload")
    tool_calls: list[dict[str, Any]] | None = Field(default=None, description="Serialized tool call payloads")

    def to_message(self) -> LLMMessage:
        """Convert the payload into the service DTO."""

        return LLMMessage(
            role=self.role,
            content=self.content,
            name=self.name,
            function_call=self.function_call,
            tool_calls=self.tool_calls,
        )


class GenerateResponseRequest(BaseModel):
    """Request body for text generation requests."""

    messages: list[MessagePayload]
    user_id: uuid.UUID | None = Field(default=None, description="Authenticated user identifier")
    model: str | None = Field(default=None, description="Optional model override")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Optional temperature override")
    max_output_tokens: int | None = Field(default=None, gt=0, description="Optional max output tokens override")
    provider_kwargs: dict[str, Any] | None = Field(
        default=None,
        description="Additional provider-specific keyword arguments",
    )


class GenerateResponseResponse(BaseModel):
    """Response body for text generation requests."""

    request_id: uuid.UUID
    response: LLMResponse


@router.post("/responses", response_model=GenerateResponseResponse, status_code=status.HTTP_200_OK)
async def generate_response(
    payload: GenerateResponseRequest,
    service: LLMService = Depends(get_llm_service),
) -> GenerateResponseResponse:
    """Invoke the LLM for a conversational response while tracking the user context."""

    messages = [message.to_message() for message in payload.messages]
    extra_kwargs = payload.provider_kwargs or {}

    try:
        response, request_id = await service.generate_response(
            messages=messages,
            user_id=payload.user_id,
            model=payload.model,
            temperature=payload.temperature,
            max_output_tokens=payload.max_output_tokens,
            **extra_kwargs,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return GenerateResponseResponse(request_id=request_id, response=response)


@router.get("/requests", response_model=list[LLMRequest])
def list_user_requests(
    user_id: uuid.UUID = Query(..., description="User to filter requests for"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of requests to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: LLMService = Depends(get_llm_service),
) -> list[LLMRequest]:
    """Return the recent LLM requests for the provided user."""

    return service.get_user_requests(user_id=user_id, limit=limit, offset=offset)


@router.get("/requests/{request_id}", response_model=LLMRequest)
def get_request_details(
    request_id: uuid.UUID,
    service: LLMService = Depends(get_llm_service),
) -> LLMRequest:
    """Return a single LLM request record."""

    request = service.get_request(request_id)
    if request is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="LLM request not found")
    return request
