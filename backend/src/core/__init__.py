"""
Core infrastructure for the learning system.

This package contains base classes, shared utilities, and infrastructure
that is used across multiple modules.
"""

from .prompt_base import PromptTemplate, PromptContext
from .service_base import ModuleService, ServiceConfig
from .llm_client import LLMClient

__all__ = [
    'PromptTemplate',
    'PromptContext',
    'ModuleService',
    'ServiceConfig',
    'LLMClient'
]