"""Flow execution context management."""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
import uuid

from .types import FlowExecutionKwargs

if TYPE_CHECKING:
    from .service import FlowEngineService

# Thread-safe context variable for storing flow context
_flow_context: ContextVar["FlowContext | None"] = ContextVar("flow_context", default=None)

__all__ = ["FlowContext"]


@dataclass
class FlowContext:
    """
    Execution context that provides infrastructure to steps during flow execution.

    This context is set once per flow execution and provides all the infrastructure
    components that steps need without requiring explicit parameter passing.
    """

    # Infrastructure components
    service: "FlowEngineService"
    flow_run_id: uuid.UUID
    user_id: uuid.UUID | None = None

    # Execution state
    step_counter: int = 0

    # Last step execution metrics (updated by steps)
    last_tokens_used: int = 0
    last_cost_estimate: float = 0.0

    @classmethod
    def set(cls, **kwargs: FlowExecutionKwargs) -> "FlowContext":
        """
        Set the current flow context for this async task.

        Args:
            **kwargs: Arguments to create FlowContext instance

        Returns:
            The created FlowContext instance
        """
        ctx = cls(**kwargs)
        _flow_context.set(ctx)
        return ctx

    @classmethod
    def current(cls) -> "FlowContext":
        """
        Get the current flow context for this async task.

        Returns:
            The current FlowContext instance

        Raises:
            RuntimeError: If no flow context is available
        """
        ctx = _flow_context.get()
        if ctx is None:
            raise RuntimeError("No flow context available. Steps must be executed within a flow. Make sure you're calling steps inside a flow's execute() method.")
        return ctx

    @classmethod
    def clear(cls) -> None:
        """
        Clear the current flow context.

        This is typically called during cleanup to ensure no context
        leakage between flow executions.
        """
        _flow_context.set(None)

    def get_next_step_order(self) -> int:
        """
        Get the next step order number and increment counter.

        Returns:
            The step order for the next step to be executed
        """
        self.step_counter += 1
        return self.step_counter

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary representation."""
        return {
            "flow_run_id": str(self.flow_run_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "step_counter": self.step_counter,
            "last_tokens_used": self.last_tokens_used,
            "last_cost_estimate": self.last_cost_estimate,
        }
