"""Factory for creating LLM provider instances."""

from sqlalchemy.orm import Session

from ..config import LLMConfig
from ..types import LLMProviderType
from .base import LLMProvider

# Import provider classes
from .claude import AnthropicProvider, BedrockProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

__all__ = ["LLMProviderError", "create_llm_provider"]


class LLMProviderError(Exception):
    """Raised when there's an error creating or using an LLM provider."""

    pass


def create_llm_provider(config: LLMConfig, db_session: Session) -> LLMProvider:
    """
    Create an LLM provider instance based on configuration.

    Args:
        config: LLM configuration
        db_session: Database session for logging

    Returns:
        LLM provider instance

    Raises:
        LLMProviderError: If provider type is not supported
    """
    if config.provider == LLMProviderType.OPENAI:
        return OpenAIProvider(config, db_session)
    if config.provider == LLMProviderType.AZURE_OPENAI:
        # Azure OpenAI uses the same provider with different base URL
        return OpenAIProvider(config, db_session)
    if config.provider == LLMProviderType.ANTHROPIC:
        return AnthropicProvider(config, db_session)
    if config.provider == LLMProviderType.BEDROCK:
        return BedrockProvider(config, db_session)
    if config.provider == LLMProviderType.GEMINI:
        return GeminiProvider(config, db_session)
    else:
        raise LLMProviderError(f"Unsupported provider: {config.provider}")


def get_available_providers() -> list[LLMProviderType]:
    """
    Get list of available provider types.

    Returns:
        List of supported provider types
    """
    return [
        LLMProviderType.OPENAI,
        LLMProviderType.AZURE_OPENAI,
        LLMProviderType.ANTHROPIC,
        LLMProviderType.BEDROCK,
        LLMProviderType.GEMINI,
    ]
