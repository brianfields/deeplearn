"""Flow Engine module: wraps llm_flow_engine with our backend modular API.

This module provides:
- Pydantic DTOs for requests/responses
- Repository that talks to llm_flow_engine background/status APIs
- Service that exposes high-level use-cases and returns DTOs
- Public provider for DI (returns the service directly)
- FastAPI routes (HTTP-only concerns)
"""

__all__ = [
    "dto",
]
