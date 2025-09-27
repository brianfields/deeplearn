"""Repository layer for LLM services."""

import contextlib
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session

from .models import LLMRequestModel

__all__ = ["LLMRequestRepo"]


class LLMRequestRepo:
    """Repository for LLM request database operations."""

    def __init__(self, session: Session) -> None:
        self.s = session

    def by_id(self, request_id: uuid.UUID) -> LLMRequestModel | None:
        """Get LLM request by ID."""
        return self.s.get(LLMRequestModel, request_id)

    def create(self, llm_request: LLMRequestModel) -> LLMRequestModel:
        """Create a new LLM request record."""
        self.s.add(llm_request)
        self.s.flush()  # Get the ID without committing
        return llm_request

    def save(self, llm_request: LLMRequestModel) -> None:
        """Save changes to an existing LLM request."""
        self.s.add(llm_request)

    def by_user_id(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[LLMRequestModel]:
        """Get LLM requests for a specific user."""
        return self.s.query(LLMRequestModel).filter(LLMRequestModel.user_id == user_id).order_by(desc(LLMRequestModel.created_at)).limit(limit).offset(offset).all()

    def by_status(self, status: str, limit: int = 100) -> list[LLMRequestModel]:
        """Get LLM requests by status."""
        return self.s.query(LLMRequestModel).filter(LLMRequestModel.status == status).order_by(desc(LLMRequestModel.created_at)).limit(limit).all()

    def by_provider(self, provider: str, limit: int = 100, offset: int = 0) -> list[LLMRequestModel]:
        """Get LLM requests by provider."""
        return self.s.query(LLMRequestModel).filter(LLMRequestModel.provider == provider).order_by(desc(LLMRequestModel.created_at)).limit(limit).offset(offset).all()

    def update_success(
        self,
        request_id: uuid.UUID,
        response_content: str,
        response_raw: dict[str, Any],
        tokens_used: int | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_estimate: float | None = None,
        execution_time_ms: int | None = None,
        cached: bool = False,
        provider_response_id: str | None = None,
        system_fingerprint: str | None = None,
        response_output: dict[str, Any] | list[dict[str, Any]] | None = None,
        response_created_at: datetime | None = None,
    ) -> None:
        """Update LLM request with successful response data."""
        request = self.by_id(request_id)
        if request:
            request.response_content = response_content
            request.response_raw = response_raw
            request.tokens_used = tokens_used
            request.input_tokens = input_tokens
            request.output_tokens = output_tokens
            request.cost_estimate = cost_estimate
            request.execution_time_ms = execution_time_ms
            request.cached = cached
            request.status = "completed"
            request.provider_response_id = provider_response_id
            request.system_fingerprint = system_fingerprint
            request.response_output = response_output
            request.response_created_at = response_created_at
            self.save(request)

    def update_error(self, request_id: uuid.UUID, error_message: str, error_type: str, execution_time_ms: int | None = None, retry_attempt: int = 1) -> None:
        """Update LLM request with error information."""
        request = self.by_id(request_id)
        if request:
            request.status = "failed"
            request.error_message = error_message
            request.error_type = error_type
            request.execution_time_ms = execution_time_ms
            request.retry_attempt = retry_attempt
            self.save(request)

    def count_by_user(self, user_id: uuid.UUID) -> int:
        """Count total requests for a user."""
        return self.s.query(LLMRequestModel).filter(LLMRequestModel.user_id == user_id).count()

    def count_by_status(self, status: str) -> int:
        """Count requests by status."""
        return self.s.query(LLMRequestModel).filter(LLMRequestModel.status == status).count()

    def get_recent(self, limit: int = 50, offset: int = 0) -> list[LLMRequestModel]:
        """Get recent LLM requests with pagination. FOR ADMIN USE ONLY."""
        return self.s.query(LLMRequestModel).order_by(desc(LLMRequestModel.created_at)).limit(limit).offset(offset).all()

    def count_all(self) -> int:
        """Get total count of LLM requests. FOR ADMIN USE ONLY."""
        return self.s.query(LLMRequestModel).count()

    def assign_user(self, request_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Ensure an LLM request is associated with the provided user."""

        request = self.by_id(request_id)
        if request is None:
            return

        if request.user_id == user_id:
            return

        request.user_id = user_id
        self.save(request)
        with contextlib.suppress(Exception):
            self.s.flush()
