"""Configuration classes and factory functions for LLM providers."""

import os

from pydantic import BaseModel, Field, field_validator

from .types import ImageQuality, LLMProviderType, WebSearchConfig

__all__ = ["LLMConfig", "create_llm_config_from_env"]


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""

    provider: LLMProviderType = Field(default=LLMProviderType.OPENAI, description="LLM provider to use")
    model: str = Field(default="gpt-5", description="Model name to use")
    api_key: str | None = Field(default=None, description="API key for the provider")
    base_url: str | None = Field(default=None, description="Custom base URL for API calls")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=16384, gt=0, description="Maximum tokens per request")
    timeout: int = Field(default=180, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retries")

    # Image generation settings
    image_model: str = Field(default="dall-e-3", description="Image generation model")
    image_quality: ImageQuality = Field(default=ImageQuality.STANDARD, description="Image quality setting")

    # Web search settings
    web_search_config: WebSearchConfig = Field(default_factory=WebSearchConfig, description="Web search configuration")

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_dir: str = Field(default=".llm_cache", description="Cache directory path")

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_requests: bool = Field(default=True, description="Log API requests and responses")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within acceptable range"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens is positive"""
        if v <= 0:
            raise ValueError("max_tokens must be positive")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is positive"""
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries is non-negative"""
        if v < 0:
            raise ValueError("max_retries must be non-negative")
        return v

    def validate_config(self) -> bool:
        """Validate that configuration is complete and valid"""
        if not self.api_key:
            raise ValueError("API key is required")

        if self.provider == LLMProviderType.AZURE_OPENAI and not self.base_url:
            raise ValueError("Azure OpenAI requires base_url to be set")

        return True

    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return self.model_dump()


def create_llm_config_from_env() -> LLMConfig:
    """
    Create LLM configuration from environment variables.

    Reads the following environment variables:
    - OPENAI_API_KEY: OpenAI API key
    - OPENAI_MODEL: Model name (default: gpt-5)
    - OPENAI_BASE_URL: Custom base URL
    - AZURE_OPENAI_API_KEY: Azure OpenAI API key
    - AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint
    - TEMPERATURE: Generation temperature (default: 0.7)
    - MAX_TOKENS: Maximum tokens (default: 16384)
    - REQUEST_TIMEOUT: Request timeout (default: 180)
    - MAX_RETRIES: Maximum retries (default: 3)
    - IMAGE_MODEL: Image generation model (default: dall-e-3)
    - IMAGE_QUALITY: Image quality (default: standard)
    - ENABLE_WEB_SEARCH: Enable web search (default: false)
    - WEB_SEARCH_CONTEXT_SIZE: Search context size (default: medium)
    - LLM_CACHE_ENABLED: Enable caching (default: true)
    - LLM_CACHE_DIR: Cache directory (default: .llm_cache)
    - LOG_LEVEL: Logging level (default: INFO)

    Returns:
        LLMConfig: Configured LLM instance

    Raises:
        ValueError: If no API key is found or configuration is invalid
    """
    # Read environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    temperature = float(os.getenv("TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("MAX_TOKENS", "16384"))
    request_timeout = int(os.getenv("REQUEST_TIMEOUT", "180"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))

    # Image generation settings
    image_model = os.getenv("IMAGE_MODEL", "dall-e-3")
    image_quality_str = os.getenv("IMAGE_QUALITY", "standard")
    image_quality = ImageQuality.HD if image_quality_str == "hd" else ImageQuality.STANDARD

    # Web search settings
    web_search_enabled = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
    web_search_context_size = os.getenv("WEB_SEARCH_CONTEXT_SIZE", "medium")
    web_search_config = WebSearchConfig(
        enabled=web_search_enabled,
        context_size=web_search_context_size,  # type: ignore
    )

    # Cache settings
    cache_enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
    cache_dir = os.getenv("LLM_CACHE_DIR", ".llm_cache")

    # Logging settings
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_requests = os.getenv("LOG_REQUESTS", "true").lower() == "true"

    # Determine provider based on available keys
    if azure_openai_api_key and azure_openai_endpoint:
        provider = LLMProviderType.AZURE_OPENAI
        api_key = azure_openai_api_key
        base_url = azure_openai_endpoint
    elif openai_api_key:
        provider = LLMProviderType.OPENAI
        api_key = openai_api_key
        base_url = openai_base_url
    else:
        raise ValueError("No API key found. Please set OPENAI_API_KEY or AZURE_OPENAI_API_KEY")

    # Create and validate config
    config = LLMConfig(
        provider=provider,
        model=openai_model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=request_timeout,
        max_retries=max_retries,
        image_model=image_model,
        image_quality=image_quality,
        web_search_config=web_search_config,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
        log_level=log_level,
        log_requests=log_requests,
    )

    config.validate_config()
    return config
