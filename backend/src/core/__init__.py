"""
Core infrastructure for the learning system.

This package contains base classes, shared utilities, and infrastructure
that is used across multiple modules.
"""

from .llm_client import LLMClient
from .prompt_base import PromptContext, PromptTemplate
from .service_base import ModuleService, ServiceConfig

__all__ = [
    "LLMClient",
    "ModuleService",
    "PromptContext",
    "PromptTemplate",
    "ServiceConfig",
]
