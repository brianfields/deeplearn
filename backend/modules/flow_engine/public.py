"""Flow Engine public API

This module is the narrow, importable contract for the flow engine module
per backend.md. Import ONLY from `modules.flow_engine.public` in other modules.

What it provides:
- `FlowEngineProvider` Protocol: the service surface area (returns DTOs)
- `flow_engine_provider()`: DI provider that returns the concrete service
- `flow_registry`: in-memory registry mapping names -> `BaseFlow` subclasses

Example: register a flow (at startup)

```python
from modules.flow_engine.public import flow_registry
from llm_flow_engine.examples.basic_flow_example import BlogFlow

flow_registry.register("blog_generation", BlogFlow)
```

Example: start a background flow from another module/service

```python
from modules.flow_engine.public import FlowEngineProvider, flow_engine_provider
from modules.flow_engine.service import StartFlowRequest

async def create_blog() -> str:
    svc: FlowEngineProvider = flow_engine_provider()
    await svc.initialize()
    resp = await svc.start(
        StartFlowRequest(
            flow_name="blog_generation",
            method_name="generate_blog_post",
            inputs={"topic": "The Future of AI", "style": "professional"},
            user_id="user-123",
            estimated_steps=1,
        )
    )
    return resp.flow_id
```

Example: query status

```python
from modules.flow_engine.public import flow_engine_provider

async def check(flow_id: str):
    svc = flow_engine_provider()
    await svc.initialize()
    status = await svc.status(flow_id)
    return status.status, status.progress.percentage
```
"""

from __future__ import annotations

from typing import Protocol

from llm_flow_engine.flows.base import BaseFlow

from .service import (
    FlowListResponseDTO,
    FlowStatusDTO,
    StartFlowRequest,
    StartFlowResponse,
    SystemMetricsDTO,
)


class FlowEngineProvider(Protocol):
    """Protocol for the flow engine service returned by the provider."""

    async def initialize(self) -> None: ...
    async def start(self, req: StartFlowRequest) -> StartFlowResponse: ...
    async def status(self, flow_id: str) -> FlowStatusDTO: ...
    async def list_running(self, user_id: str | None) -> FlowListResponseDTO: ...
    async def metrics(self) -> SystemMetricsDTO: ...
    async def cancel(self, flow_id: str) -> bool: ...


class FlowRegistry:
    """Simple in-memory registry of available flows.

    Register each `BaseFlow` subclass under a stable name. Other parts of the
    backend start flows by name to avoid direct imports.
    """

    def __init__(self) -> None:
        self._name_to_flow: dict[str, type[BaseFlow]] = {}

    def register(self, name: str, flow_class: type[BaseFlow]) -> None:
        """Register a flow class under `name`.

        - `name` should be stable, lowercase, and URL-safe.
        - `flow_class` must subclass `BaseFlow` from llm_flow_engine.
        """
        self._name_to_flow[name.strip().lower()] = flow_class

    def get(self, name: str) -> type[BaseFlow] | None:
        """Resolve a previously registered flow class by `name`."""
        return self._name_to_flow.get(name.strip().lower())

    def list_registered(self) -> list[str]:
        """Return all registered flow names (sorted)."""
        return sorted(self._name_to_flow.keys())


flow_registry = FlowRegistry()


def flow_engine_provider() -> FlowEngineProvider:
    """Return the concrete flow engine service instance.

    The returned object adheres to `FlowEngineProvider` and already returns DTOs,
    so routes and other modules can depend on this directly.
    """
    from .service import create_flow_engine_service

    return create_flow_engine_service()


__all__ = [
    "FlowEngineProvider",
    "flow_engine_provider",
    "flow_registry",
]
