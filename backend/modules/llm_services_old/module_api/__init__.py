"""
LLM Services Module API

This module provides the public interface for the LLM Services module.
Other modules should only import from this module_api package.
"""

# Main service class
# Domain types needed for prompt templates
from ..domain.entities.llm_provider import LLMMessage, MessageRole
from .llm_service import LLMService, create_llm_service

# Types for external use
from .types import (
    GenerationRequest,
    GenerationResponse,
    LLMConfig,
    LLMResponse,
    PromptContext,
)

# Public API exports
__all__ = [
    # Service
    "LLMService",
    "create_llm_service",
    # Types
    "LLMResponse",
    "PromptContext",
    "LLMConfig",
    "GenerationRequest",
    "GenerationResponse",
    # Domain types for prompts
    "LLMMessage",
    "MessageRole",
]
