"""Conversation orchestration primitives mirroring the flow engine."""

from __future__ import annotations

from collections.abc import Callable
import functools
import inspect
import json
from pathlib import Path
from typing import Any, ParamSpec, Protocol, TypeVar
import uuid

from pydantic import BaseModel

from ..infrastructure.public import infrastructure_provider
from ..llm_services.public import ToolDefinition, llm_services_provider
from .context import ConversationContext
from .repo import ConversationMessageRepo, ConversationRepo
from .service import ConversationEngineService, ConversationMessageDTO, ConversationSummaryDTO

__all__ = ["BaseConversation", "ToolHandler", "conversation_session"]

P = ParamSpec("P")
T = TypeVar("T", bound=BaseModel)


def _coerce_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    """Coerce a value to UUID for conversation_id."""

    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _coerce_user_id(value: int | str | uuid.UUID | None) -> int | None:
    """Coerce a value to int for user_id.

    Accepts int, str (numeric), or None. This supports migration from UUID-based user_ids.
    """

    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        # Try to parse as int
        try:
            return int(value)
        except ValueError:
            # If it's not a valid int string, return None
            return None
    if isinstance(value, uuid.UUID):
        # For backwards compatibility during migration, extract int from UUID
        # This handles UUIDs created by _int_to_uuid
        int_value = value.int & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        return int_value if int_value > 0 else None
    return None


def conversation_session(func: Callable[P, Any]) -> Callable[P, Any]:
    """Decorator that initialises infrastructure for a conversation handler."""

    signature = inspect.signature(func)
    accepts_conversation_id = "conversation_id" in signature.parameters
    accepts_private_conversation_id = "_conversation_id" in signature.parameters

    @functools.wraps(func)
    async def wrapper(self: BaseConversation, *args: P.args, **kwargs: P.kwargs) -> Any:  # type: ignore[misc]
        infra = infrastructure_provider()
        infra.initialize()
        llm_services = llm_services_provider()

        user_arg = kwargs.get("user_id")
        if user_arg is None and "_user_id" in kwargs:
            user_arg = kwargs["_user_id"]
        user_int_id = _coerce_user_id(user_arg)  # type: ignore[arg-type]

        conversation_arg = kwargs.get("conversation_id")
        if conversation_arg is None and "_conversation_id" in kwargs:
            conversation_arg = kwargs["_conversation_id"]
        conversation_uuid = _coerce_uuid(conversation_arg)  # type: ignore[arg-type]

        metadata: dict[str, Any] | None = kwargs.get("conversation_metadata")  # type: ignore[assignment]
        if metadata is None and "_conversation_metadata" in kwargs:
            metadata = kwargs["_conversation_metadata"]  # type: ignore[assignment]

        title: str | None = kwargs.get("conversation_title")  # type: ignore[assignment]
        if title is None and "_conversation_title" in kwargs:
            title = kwargs["_conversation_title"]  # type: ignore[assignment]

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
                    user_id=user_int_id,
                    title=title,
                    metadata=metadata,
                )
                conversation_uuid = uuid.UUID(created.id)
                summary = created
                # Always inject as _conversation_id (the magic parameter convention)
                kwargs["_conversation_id"] = created.id  # type: ignore[index]
            else:
                summary = await service.get_conversation_summary(conversation_uuid)
                if summary.conversation_type != self.conversation_type:
                    raise ValueError(f"Conversation type mismatch for BaseConversation subclass: expected '{self.conversation_type}', got '{summary.conversation_type}'")

            conversation_id_str = str(conversation_uuid) if conversation_uuid else None
            if accepts_conversation_id:
                kwargs["conversation_id"] = conversation_id_str  # type: ignore[index]
            elif "conversation_id" in kwargs:
                kwargs.pop("conversation_id")

            if accepts_private_conversation_id:
                kwargs["_conversation_id"] = conversation_id_str  # type: ignore[index]
            elif "_conversation_id" in kwargs:
                kwargs.pop("_conversation_id")

            context_metadata = dict(summary.metadata or {}) if summary else None

            ConversationContext.set(
                service=service,
                conversation_id=conversation_uuid,
                user_id=user_int_id,
                metadata=context_metadata,
            )

            try:
                result = await func(self, *args, **kwargs)
            finally:
                ConversationContext.clear()

            return result

    return wrapper


class ToolHandler(Protocol):
    """Protocol for tool implementations."""

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool with the given arguments.

        Args:
            arguments: Tool arguments from the LLM

        Returns:
            Tool execution result (should be JSON-serializable)
        """
        ...


class BaseConversation:
    """Base helper for implementing conversational experiences."""

    conversation_type: str
    system_prompt_file: str | None = None

    def __init__(self) -> None:
        if not getattr(self, "conversation_type", None):
            raise ValueError("conversation_type must be set on subclasses of BaseConversation")

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

    def _load_prompt_from_file(self, filename: str) -> str:
        """
        Load a prompt from a markdown file.

        This method looks for the prompt file in the same module's directory
        as the conversation class, mirroring the flow_engine pattern.

        Args:
            filename: Name of the prompt file relative to the module directory
                     (e.g., "prompts/system_prompt.md")

        Returns:
            Content of the prompt file as a string

        Raises:
            FileNotFoundError: If the prompt file cannot be found
        """
        # Get the file path where the conversation subclass is defined
        # Use inspect to get the actual file of the subclass, not BaseConversation
        import inspect

        conversation_file = inspect.getfile(self.__class__)
        conversation_dir = Path(conversation_file).parent

        # Build path to the prompt file relative to the conversation's directory
        prompt_file_path = conversation_dir / filename

        # Try to read the file
        try:
            with prompt_file_path.open(encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Conversation prompt file '{filename}' not found. Looked in: {prompt_file_path}") from e

    def get_system_prompt(self) -> str | None:
        """Return the configured system prompt, if any."""

        if self.system_prompt_file is None:
            return None
        return self._load_prompt_from_file(self.system_prompt_file)

    def get_available_tools(self) -> dict[str, tuple[ToolDefinition, ToolHandler]]:
        """Return available tools for this conversation type.

        Subclasses should override this to register tools.

        Returns:
            Dict mapping tool name to (definition, handler)
        """
        return {}

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

    async def generate_structured_reply(
        self,
        response_model: type[T],
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[T, uuid.UUID, dict[str, Any]]:
        """Generate a structured response using a Pydantic model (does not record message).

        This is a convenience method that combines:
        1. Building LLM messages from conversation history
        2. Calling llm_services.generate_structured_response()

        Note: This method does NOT automatically record the assistant message.
        After calling this, you typically want to call record_assistant_message()
        with the appropriate content extracted from the structured response.

        Args:
            response_model: Pydantic model class for structured output
            system_prompt: Override system prompt (uses self.get_system_prompt() if None)
            model: LLM model to use (e.g., "gpt-5-mini")
            temperature: Temperature for generation
            max_output_tokens: Maximum output tokens
            **kwargs: Additional LLM provider parameters

        Returns:
            Tuple of (structured response object, LLM request ID, raw response dict)

        Example:
            class CoachResponse(BaseModel):
                message: str
                confidence: float

            response, request_id, raw = await self.generate_structured_reply(
                CoachResponse,
                model="gpt-5-mini",
            )

            # Record the message field as the assistant message
            await self.record_assistant_message(
                response.message,
                llm_request_id=request_id,
                tokens_used=raw.get("usage", {}).get("total_tokens"),
            )

            # Use other fields for metadata updates
            if response.confidence > 0.8:
                await self.update_conversation_metadata({"high_confidence": True})
        """
        ctx = ConversationContext.current()
        prompt = system_prompt or self.get_system_prompt()

        # Build message history for LLM
        llm_messages = await ctx.service.build_llm_messages(
            ctx.conversation_id,
            system_prompt=prompt,
            include_system=False,
        )

        # Get structured response and return all details
        return await ctx.service.llm_services.generate_structured_response(
            messages=llm_messages,
            response_model=response_model,
            user_id=ctx.user_id,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )

    async def generate_with_tools(
        self,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        max_tool_iterations: int = 5,
        **kwargs: Any,
    ) -> ConversationMessageDTO:
        """Generate response with automatic tool execution loop.

        This handles the full tool calling cycle:
        1. LLM generates response (may include tool calls)
        2. Execute tool calls
        3. Feed results back to LLM
        4. Repeat until LLM returns text (or max iterations hit)

        Args:
            system_prompt: Override system prompt (uses self.get_system_prompt() if None)
            model: LLM model to use
            temperature: Temperature for generation
            max_output_tokens: Maximum output tokens
            max_tool_iterations: Maximum number of tool execution cycles (default 5)
            **kwargs: Additional LLM provider parameters

        Returns:
            The final assistant message after tool execution completes

        Raises:
            RuntimeError: If tool execution exceeds max iterations
        """
        from ..llm_services.types import MessageRole

        ctx = ConversationContext.current()
        tools = self.get_available_tools()
        tool_definitions = [defn for defn, _ in tools.values()]

        # Build message history
        prompt = system_prompt or self.get_system_prompt()
        llm_messages = await ctx.service.build_llm_messages(
            ctx.conversation_id,
            system_prompt=prompt,
            include_system=False,
        )

        # Tool execution loop
        for _iteration in range(max_tool_iterations):
            response, tool_calls, request_id = await ctx.service.llm_services.generate_response_with_tools(
                messages=llm_messages,
                tools=tool_definitions,
                user_id=ctx.user_id,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                **kwargs,
            )

            if not tool_calls:
                # LLM returned final text response
                return await self.record_assistant_message(
                    response.content,
                    llm_request_id=request_id,
                    tokens_used=response.tokens_used,
                    cost_estimate=response.cost_estimate,
                )

            # Execute tool calls
            for tool_call in tool_calls:
                if tool_call.name not in tools:
                    # Tool not found - record error
                    result = {"error": f"Tool {tool_call.name} not found"}
                else:
                    _, handler = tools[tool_call.name]
                    try:
                        result = await handler.execute(tool_call.arguments)
                    except Exception as e:
                        result = {"error": str(e)}

                # Add tool result to message history
                from ..llm_services.service import LLMMessage as LLMMessageDTO

                llm_messages.append(
                    LLMMessageDTO(
                        role=MessageRole.TOOL.value,
                        content=json.dumps(result),
                        name=tool_call.name,
                    )
                )

        raise RuntimeError(f"Tool execution exceeded max iterations ({max_tool_iterations})")

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
