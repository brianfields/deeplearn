"""LLM-specific exceptions."""

__all__ = [
    "LLMAuthenticationError",
    "LLMError",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMValidationError",
]


class LLMError(Exception):
    """Base exception for all LLM-related errors"""

    def __init__(self, message: str, provider: str | None = None, model: str | None = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model


class LLMAuthenticationError(LLMError):
    """Raised when LLM provider authentication fails"""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM provider rate limits are exceeded"""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Raised when LLM provider requests timeout"""

    pass


class LLMValidationError(LLMError):
    """Raised when LLM request or response validation fails"""

    pass


class LLMProviderError(LLMError):
    """Raised when LLM provider returns an error"""

    def __init__(self, message: str, error_code: str | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.error_code = error_code
