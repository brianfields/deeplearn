"""Configuration classes and factory functions for LLM providers."""

import os
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .types import ImageQuality, LLMProviderType, WebSearchConfig

__all__ = ["LLMConfig", "create_llm_config_from_env"]


_CLAUDE_BEDROCK_MODEL_IDS = {
    # Claude 4.5 models require inference profiles (not direct model IDs)
    "claude-haiku-4-5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-sonnet-4-5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claude-opus-4-1": "us.anthropic.claude-opus-4-1-20250805-v1:0",
}


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""

    provider: LLMProviderType = Field(default=LLMProviderType.OPENAI, description="LLM provider to use")
    model: str = Field(default="gpt-5", description="Model name to use")
    api_key: str | None = Field(default=None, description="API key for the provider")
    base_url: str | None = Field(default=None, description="Custom base URL for API calls")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str | None = Field(default=None, description="Default Claude model name")
    claude_provider: str | None = Field(default=None, description="Claude provider: 'anthropic' or 'bedrock'")
    aws_access_key_id: str | None = Field(default=None, description="AWS access key for Bedrock")
    aws_secret_access_key: str | None = Field(default=None, description="AWS secret key for Bedrock")
    aws_session_token: str | None = Field(default=None, description="AWS session token for Bedrock")
    aws_region: str | None = Field(default=None, description="AWS region for Bedrock access")
    bedrock_model_id: str | None = Field(default=None, description="Bedrock-specific model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_output_tokens: int | None = Field(default=None, gt=0, description="Maximum output tokens per request")
    timeout: int = Field(default=180, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retries")

    # Image generation settings
    image_model: str = Field(default="dall-e-3", description="Image generation model")
    image_quality: ImageQuality = Field(default=ImageQuality.STANDARD, description="Image quality setting")
    audio_model: str | None = Field(default=None, description="Default audio generation model")

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

    @field_validator("max_output_tokens")
    @classmethod
    def validate_max_output_tokens(cls, v: int | None) -> int | None:
        """Validate max_output_tokens is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("max_output_tokens must be positive")
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
        if (
            self.provider
            in {
                LLMProviderType.OPENAI,
                LLMProviderType.ANTHROPIC,
                LLMProviderType.AZURE_OPENAI,
                LLMProviderType.GEMINI,
            }
            and not self.api_key
        ):
            raise ValueError("API key is required for OpenAI, Anthropic, Azure OpenAI, and Gemini providers")

        if self.provider == LLMProviderType.ANTHROPIC and not (self.anthropic_api_key or self.api_key):
            raise ValueError("Anthropic provider requires ANTHROPIC_API_KEY to be set")

        if self.provider == LLMProviderType.AZURE_OPENAI and not self.base_url:
            raise ValueError("Azure OpenAI requires base_url to be set")

        if self.provider == LLMProviderType.BEDROCK:
            if not self.aws_region:
                raise ValueError("Bedrock provider requires AWS region")
            if not self.bedrock_model_id:
                raise ValueError("Bedrock provider requires a model identifier")

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return self.model_dump()


def create_llm_config_from_env(
    provider_override: LLMProviderType | None = None,
    model_override: str | None = None,
) -> LLMConfig:
    """
    Create LLM configuration from environment variables.

    Provider Selection:
    - When a model is requested (e.g., "gpt-5-mini", "claude-haiku-4-5"), the provider
      is automatically selected based on the model prefix.
    - GPT models (gpt-*) use OpenAI or Azure OpenAI
    - Claude models (claude-*) use the provider specified by CLAUDE_PROVIDER:
      - 'anthropic' (default): Direct Anthropic API
      - 'bedrock': AWS Bedrock
    - NO FALLBACKS: If the required provider isn't configured, requests will fail explicitly

    Environment Variables:
    - OPENAI_API_KEY: OpenAI API key (required for GPT models)
    - OPENAI_MODEL: Default model name (default: gpt-5)
    - OPENAI_BASE_URL: Custom base URL
    - AZURE_OPENAI_API_KEY: Azure OpenAI API key
    - AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint
    - ANTHROPIC_API_KEY: Anthropic API key (required for Claude models with CLAUDE_PROVIDER=anthropic)
    - ANTHROPIC_MODEL: Default Claude model (default: claude-haiku-4-5)
    - CLAUDE_PROVIDER: Choose 'anthropic' or 'bedrock' for Claude models (default: anthropic)
    - AWS_ACCESS_KEY_ID: AWS access key (required for CLAUDE_PROVIDER=bedrock)
    - AWS_SECRET_ACCESS_KEY: AWS secret key (required for CLAUDE_PROVIDER=bedrock)
    - AWS_REGION: AWS region (default: us-west-2)
    - TEMPERATURE: Generation temperature (default: 0.7)
    - MAX_OUTPUT_TOKENS: Maximum output tokens
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
    provider_hint = (provider_override.value if provider_override else os.getenv("LLM_PROVIDER", "")).lower()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_base_url = os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    gemini_tts_model = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    claude_provider = os.getenv("CLAUDE_PROVIDER", "anthropic").lower()  # 'anthropic' or 'bedrock'

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    aws_region = os.getenv("AWS_REGION", "us-west-2")
    bedrock_model_id = os.getenv("BEDROCK_MODEL_ID")

    temperature = float(os.getenv("TEMPERATURE", "0.7"))
    max_output_tokens_env = os.getenv("MAX_OUTPUT_TOKENS")
    max_output_tokens = int(max_output_tokens_env) if max_output_tokens_env is not None else None
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

    audio_model_env = os.getenv("AUDIO_MODEL")

    # Logging settings
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_requests = os.getenv("LOG_REQUESTS", "true").lower() == "true"

    # Determine provider based on overrides and available credentials
    provider: LLMProviderType
    api_key: str | None = None
    base_url: str | None = None
    model_name: str

    def wants(provider_type: LLMProviderType, *aliases: str) -> bool:
        if provider_override is not None:
            return provider_override == provider_type
        normalized_hint = provider_hint
        return bool(normalized_hint and normalized_hint in aliases)

    def is_gemini_model(name: str | None) -> bool:
        if not name:
            return False
        lowered = name.lower()
        return lowered.startswith("gemini-2.5") or lowered.startswith("imagen")

    if provider_override == LLMProviderType.ANTHROPIC and not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY must be set to use the Anthropic provider")
    if provider_override == LLMProviderType.BEDROCK and not (aws_access_key_id and aws_secret_access_key) and not os.getenv("AWS_PROFILE"):
        raise ValueError("AWS credentials are required to use the Bedrock provider")
    if provider_override == LLMProviderType.GEMINI and not gemini_api_key:
        raise ValueError("GEMINI_API_KEY must be set to use the Gemini provider")

    if azure_openai_api_key and azure_openai_endpoint and wants(LLMProviderType.AZURE_OPENAI, "azure", "azure_openai"):
        provider = LLMProviderType.AZURE_OPENAI
        api_key = azure_openai_api_key
        base_url = azure_openai_endpoint
        model_name = model_override or openai_model
    elif gemini_api_key and (wants(LLMProviderType.GEMINI, "gemini", "google", "google_ai") or is_gemini_model(model_override)):
        provider = LLMProviderType.GEMINI
        api_key = gemini_api_key
        base_url = gemini_base_url
        model_name = model_override or gemini_model
    elif wants(LLMProviderType.ANTHROPIC, "anthropic", "claude") and anthropic_api_key:
        provider = LLMProviderType.ANTHROPIC
        api_key = anthropic_api_key
        base_url = anthropic_base_url
        model_name = model_override or anthropic_model
    elif wants(LLMProviderType.BEDROCK, "bedrock") and ((aws_access_key_id and aws_secret_access_key) or os.getenv("AWS_PROFILE")):
        provider = LLMProviderType.BEDROCK
        model_name = model_override or anthropic_model
    elif openai_api_key and provider_override == LLMProviderType.OPENAI:
        provider = LLMProviderType.OPENAI
        api_key = openai_api_key
        base_url = openai_base_url
        model_name = model_override or openai_model
    elif azure_openai_api_key and azure_openai_endpoint and provider_override == LLMProviderType.AZURE_OPENAI:
        provider = LLMProviderType.AZURE_OPENAI
        api_key = azure_openai_api_key
        base_url = azure_openai_endpoint
        model_name = model_override or openai_model
    elif anthropic_api_key and provider_override == LLMProviderType.ANTHROPIC:
        provider = LLMProviderType.ANTHROPIC
        api_key = anthropic_api_key
        base_url = anthropic_base_url
        model_name = model_override or anthropic_model
    elif gemini_api_key and provider_override == LLMProviderType.GEMINI:
        provider = LLMProviderType.GEMINI
        api_key = gemini_api_key
        base_url = gemini_base_url
        model_name = model_override or gemini_model
    elif provider_override == LLMProviderType.BEDROCK and ((aws_access_key_id and aws_secret_access_key) or os.getenv("AWS_PROFILE")):
        provider = LLMProviderType.BEDROCK
        model_name = model_override or anthropic_model
    elif azure_openai_api_key and azure_openai_endpoint:
        provider = LLMProviderType.AZURE_OPENAI
        api_key = azure_openai_api_key
        base_url = azure_openai_endpoint
        model_name = model_override or openai_model
    elif anthropic_api_key and not openai_api_key:
        provider = LLMProviderType.ANTHROPIC
        api_key = anthropic_api_key
        base_url = anthropic_base_url
        model_name = model_override or anthropic_model
    elif (aws_access_key_id and aws_secret_access_key) and not openai_api_key:
        provider = LLMProviderType.BEDROCK
        model_name = model_override or anthropic_model
    elif gemini_api_key:
        provider = LLMProviderType.GEMINI
        api_key = gemini_api_key
        base_url = gemini_base_url
        model_name = model_override or gemini_model
    elif openai_api_key:
        provider = LLMProviderType.OPENAI
        api_key = openai_api_key
        base_url = openai_base_url
        model_name = model_override or openai_model
    else:
        raise ValueError(
            "No LLM provider credentials found. Please set OPENAI_API_KEY, AZURE_OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, or AWS credentials",
        )

    # Create and validate config
    resolved_bedrock_model_id = _CLAUDE_BEDROCK_MODEL_IDS.get(model_name, bedrock_model_id) if provider == LLMProviderType.BEDROCK else bedrock_model_id

    # Always use OpenAI's DALL-E for image generation (don't use Gemini)
    resolved_image_model = image_model
    resolved_audio_model = audio_model_env
    # Note: Gemini audio model can still be used if explicitly configured
    if provider == LLMProviderType.GEMINI and audio_model_env is None:
        resolved_audio_model = gemini_tts_model

    config = LLMConfig(
        provider=provider,
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        anthropic_api_key=anthropic_api_key,
        anthropic_model=anthropic_model,
        claude_provider=claude_provider,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        aws_region=aws_region if provider == LLMProviderType.BEDROCK else None,
        bedrock_model_id=resolved_bedrock_model_id,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        timeout=request_timeout,
        max_retries=max_retries,
        image_model=resolved_image_model,
        image_quality=image_quality,
        audio_model=resolved_audio_model,
        web_search_config=web_search_config,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
        log_level=log_level,
        log_requests=log_requests,
    )

    config.validate_config()
    return config
