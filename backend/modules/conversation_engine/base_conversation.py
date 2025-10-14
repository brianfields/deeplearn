"""Conversation orchestration primitives mirroring the flow engine."""

from __future__ import annotations

from collections.abc import Callable
import functools
from pathlib import Path
from typing import Any, ParamSpec
import uuid

from ..infrastructure.public import infrastructure_provider
from ..llm_services.public import llm_services_provider
from .context import ConversationContext
from .repo import ConversationMessageRepo, ConversationRepo
from .service import ConversationEngineService, ConversationMessageDTO, ConversationSummaryDTO

__all__ = ["BaseConversation", "conversation_session"]

P = ParamSpec("P")


def _coerce_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def conversation_session(func: Callable[P, Any]) -> Callable[P, Any]:
    """Decorator that initialises infrastructure for a conversation handler."""

    @functools.wraps(func)
    async def wrapper(self: BaseConversation, *args: P.args, **kwargs: P.kwargs) -> Any:  # type: ignore[misc]
        infra = infrastructure_provider()
        infra.initialize()
        llm_services = llm_services_provider()

        user_uuid = _coerce_uuid(kwargs.get("user_id"))  # type: ignore[arg-type]
        conversation_uuid = _coerce_uuid(kwargs.get("conversation_id"))  # type: ignore[arg-type]
        metadata = kwargs.get("conversation_metadata")  # type: ignore[assignment]
        title = kwargs.get("conversation_title")  # type: ignore[assignment]

        with infra.get_session_context() as db_session:
            service = ConversationEngineService(
                ConversationRepo(db_session),
                ConversationMessageRepo(db_session),
                llm_services,
            )

            summary: ConversationSummaryDTO | None = None
            if conversation_uuid is None:
                created = await service.create_conversation(
                    conversation_type=self.conversation_type,
                    user_id=user_uuid,
                    title=title,
                    metadata=metadata,
                )
                conversation_uuid = uuid.UUID(created.id)
                kwargs["conversation_id"] = created.id  # type: ignore[index]
                summary = created
            else:
                summary = await service.get_conversation_summary(conversation_uuid)
                if summary.conversation_type != self.conversation_type:
                    raise ValueError(f"Conversation type mismatch for BaseConversation subclass: expected '{self.conversation_type}', got '{summary.conversation_type}'")

            context_metadata = dict(summary.metadata or {}) if summary else None

            ConversationContext.set(
                service=service,
                conversation_id=conversation_uuid,
                user_id=user_uuid,
                metadata=context_metadata,
            )

            try:
                result = await func(self, *args, **kwargs)
            finally:
                ConversationContext.clear()

            return result

    return wrapper


class BaseConversation:
    """Base helper for implementing conversational experiences."""

    conversation_type: str
    system_prompt_file: str | None = None

    def __init__(self) -> None:
        if not getattr(self, "conversation_type", None):
            raise ValueError("conversation_type must be set on subclasses of BaseConversation")
        self._prompts_dir = Path(__file__).resolve().parent.parent / "prompts" / "conversations"

    @property
    def conversation_id(self) -> str:
        """Return the active conversation identifier as a string."""

        ctx = ConversationContext.current()
        return str(ctx.conversation_id)

    @property
    def conversation_metadata(self) -> dict[str, Any] | None:
        """Return the metadata associated with the active conversation."""

        ctx = ConversationContext.current()
        return ctx.metadata

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self._prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Conversation prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def get_system_prompt(self) -> str | None:
        """Return the configured system prompt, if any."""

        if self.system_prompt_file is None:
            return None
        return self._load_prompt(self.system_prompt_file)

    async def record_user_message(self, content: str, *, metadata: dict[str, Any] | None = None) -> ConversationMessageDTO:
        """Record a user message against the active conversation."""

        ctx = ConversationContext.current()
        return await ctx.service.record_user_message(ctx.conversation_id, content, metadata=metadata)

    async def record_system_message(self, content: str, *, metadata: dict[str, Any] | None = None) -> ConversationMessageDTO:
        """Record a system message against the active conversation."""

        ctx = ConversationContext.current()
        return await ctx.service.record_system_message(ctx.conversation_id, content, metadata=metadata)

    async def record_assistant_message(
        self,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
        llm_request_id: uuid.UUID | None = None,
        tokens_used: int | None = None,
        cost_estimate: float | None = None,
    ) -> ConversationMessageDTO:
        """Record an assistant message for the active conversation."""

        ctx = ConversationContext.current()
        return await ctx.service.record_assistant_message(
            ctx.conversation_id,
            content,
            metadata=metadata,
            llm_request_id=llm_request_id,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
        )

    async def generate_assistant_reply(
        self,
        *,
        system_prompt: str | None = None,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[ConversationMessageDTO, uuid.UUID]:
        """Generate an assistant reply via the LLM and persist it."""

        ctx = ConversationContext.current()
        prompt = system_prompt or self.get_system_prompt()
        message_dto, request_id, _ = await ctx.service.generate_assistant_response(
            ctx.conversation_id,
            system_prompt=prompt,
            user_id=ctx.user_id,
            metadata=metadata,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )
        return message_dto, request_id

    async def update_conversation_metadata(
        self,
        metadata: dict[str, Any],
        *,
        merge: bool = True,
    ) -> ConversationSummaryDTO:
        """Update metadata for the active conversation."""

        ctx = ConversationContext.current()
        summary = await ctx.service.update_conversation_metadata(ctx.conversation_id, metadata, merge=merge)
        ctx.metadata = dict(summary.metadata or {})
        return summary

    async def update_conversation_title(self, title: str | None) -> ConversationSummaryDTO:
        """Update the active conversation title."""

        ctx = ConversationContext.current()
        summary = await ctx.service.update_conversation_title(ctx.conversation_id, title)
        return summary

    async def get_conversation_summary(self) -> ConversationSummaryDTO:
        """Fetch the latest conversation summary and refresh context metadata."""

        ctx = ConversationContext.current()
        summary = await ctx.service.get_conversation_summary(ctx.conversation_id)
        ctx.metadata = dict(summary.metadata or {})
        return summary
