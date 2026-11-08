"""
LibScope AI Exception Hierarchy.
Normalizes askai-python exceptions to clean internal domain errors.
"""


class LibScopeAIError(Exception):
    """Base exception for all LibScope AI subsystem errors."""
    pass


class LibScopeAIConfigError(LibScopeAIError):
    """Raised when AI configuration or credentials are missing or invalid."""
    pass


class LibScopeAIAuthenticationError(LibScopeAIConfigError):
    """Raised when authentication credentials for an AI provider are invalid."""
    pass


class LibScopeAIProviderError(LibScopeAIError):
    """Raised when an external AI provider fails or times out."""
    def __init__(self, message: str, provider: str | None = None, original_error: Exception | None = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class LibScopeAIRateLimitError(LibScopeAIProviderError):
    """Raised when an AI provider returns rate limit / quota exhaustion (HTTP 429)."""
    pass


class LibScopeAITimeoutError(LibScopeAIProviderError):
    """Raised when an AI request times out."""
    pass


class LibScopeAIValidationError(LibScopeAIError):
    """Raised when AI structured output fails schema validation."""
    pass


def map_ask_ai_exception(exc: Exception, provider_name: str = "ask-ai") -> LibScopeAIError:
    """Map ask-ai library exceptions to LibScope AI exceptions."""
    try:
        from ask_ai.exceptions import (
            AskAIConfigError,
            AskAINetworkError,
            AskAIRateLimitError,
            ProviderAuthError,
            ProviderError,
            ProviderRateLimitError,
            ProviderTimeoutError,
            StructuredValidationError,
        )

        if isinstance(exc, (AskAIConfigError, ProviderAuthError)):
            return LibScopeAIAuthenticationError(f"AI Provider configuration/auth error ({provider_name}): {exc}")
        if isinstance(exc, StructuredValidationError):
            return LibScopeAIValidationError(f"AI response schema validation failed ({provider_name}): {exc}")
        if isinstance(exc, (ProviderTimeoutError, AskAINetworkError)):
            return LibScopeAITimeoutError(f"AI Provider timeout or network error ({provider_name}): {exc}", provider=provider_name, original_error=exc)
        if isinstance(exc, (ProviderRateLimitError, AskAIRateLimitError)):
            return LibScopeAIRateLimitError(f"AI Provider rate limit reached (429) ({provider_name}): {exc}", provider=provider_name, original_error=exc)
        if isinstance(exc, ProviderError):
            return LibScopeAIProviderError(f"AI Provider error ({provider_name}): {exc}", provider=provider_name, original_error=exc)
    except ImportError:
        pass

    # Check class name heuristics for unimported or duck-typed errors
    name = exc.__class__.__name__
    if "Auth" in name:
        return LibScopeAIAuthenticationError(f"AI Provider authentication error ({provider_name}): {exc}")
    if "RateLimit" in name:
        return LibScopeAIRateLimitError(f"AI Provider rate limit ({provider_name}): {exc}", provider=provider_name, original_error=exc)
    if "Timeout" in name:
        return LibScopeAITimeoutError(f"AI Provider timeout ({provider_name}): {exc}", provider=provider_name, original_error=exc)

    return LibScopeAIProviderError(f"AI operation failed ({provider_name}): {exc}", provider=provider_name, original_error=exc)
