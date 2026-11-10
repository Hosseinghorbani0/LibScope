"""
AI Subsystem Configuration for LibScope.
"""
import os
from dataclasses import dataclass

from libscope.core.config import get_settings


@dataclass
class AIConfig:
    """Configuration container for askai-python integration."""
    provider: str = "openrouter"
    model: str = "openai/gpt-4o-mini"
    api_key: str | None = None
    base_url: str | None = None
    azure_endpoint: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = None
    timeout: float = 30.0
    retry_count: int = 2
    validation_retries: int = 2
    temperature: float = 0.2
    max_tokens: int = 2048
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "AIConfig":
        settings = get_settings()
        key = settings.effective_ai_api_key

        # Check if enabled explicitly
        is_disabled = (
            settings.ai_provider.lower() in ("disabled", "off", "none")
            or os.getenv("LIBSCOPE_AI_DISABLED", "false").lower() in ("true", "1", "yes")
        )

        return cls(
            provider=settings.ai_provider.lower(),
            model=settings.ai_model,
            api_key=key,
            base_url=settings.ai_base_url,
            azure_endpoint=settings.azure_endpoint,
            azure_api_version=settings.azure_api_version,
            azure_deployment=settings.azure_deployment,
            timeout=float(os.getenv("LIBSCOPE_AI_TIMEOUT", "30.0")),
            retry_count=int(os.getenv("LIBSCOPE_AI_RETRIES", "2")),
            validation_retries=int(os.getenv("LIBSCOPE_AI_VALIDATION_RETRIES", "2")),
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            enabled=not is_disabled and bool(key and key.strip()),
        )

