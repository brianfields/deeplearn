# LLM Services Module — Agents Guide

This module is the single entry point for all Large Language Model (LLM) access in the backend. It abstracts provider differences behind a stable public interface so we can transparently change providers without touching calling code.

- **All LLM access must go through this module.** Do not call provider SDKs (e.g., OpenAI) directly from other modules, routes, or scripts.
- **Multiple-provider design.** The module is structured to support multiple providers; **OpenAI is the only provider implemented today**, but the abstraction allows adding others without API changes to consumers.
- **Stable public interface.** Other modules should import only from `modules.llm_services.public` and depend on the `LLMServicesProvider` protocol.

## How to use (cross-module)

- Import the provider factory and DTOs from the public surface:

```python
from modules.llm_services.public import (
    llm_services_provider,
    LLMMessage,
)

svc = llm_services_provider()  # returns a concrete service implementing LLMServicesProvider
response, request_id = await svc.generate_response([
    LLMMessage(role="system", content="You are helpful."),
    LLMMessage(role="user", content="Explain transformers in 2 sentences."),
])
```

- Use this in your module’s `service.py` (not routes) when composing behavior across modules, per architecture rules.
- Do not import internals like `providers/*`, `service.py`, or `repo.py` from outside this module.

## What this module provides

- Text generation, structured outputs (via Pydantic models), image generation, and optional web search.
- Request tracking and retrieval (returns a `request_id` alongside responses).
- Cost estimation helpers.

## Providers and extensibility

- Providers live under `modules/llm_services/providers/` and share common types defined in `providers/base.py`.
- Adding a new provider requires implementing the base interfaces and wiring configuration; consumers continue to use the same `LLMServicesProvider` methods.
- This design enables switching the backing provider (or using multiple) without changing calling code.

## Public entry points

- `llm_services_provider(session?: Session) -> LLMServicesProvider`
- `llm_services_admin_provider(session: Session) -> LLMServicesAdminProvider` (admin-only data access)

These factories return the concrete service which already implements the public protocol. Consumers should rely on the protocol and avoid importing internal implementation details.
