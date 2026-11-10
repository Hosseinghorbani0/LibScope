"""
Configuration management for LibScope using Pydantic Settings.
"""
import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Service identity
    app_name: str = "LibScope"
    app_version: str = "0.1.0"
    environment: str = Field(default="production", alias="LIBSCOPE_ENVIRONMENT")
    debug: bool = Field(default=False, alias="LIBSCOPE_DEBUG")
    log_level: str = Field(default="INFO", alias="LIBSCOPE_LOG_LEVEL")

    # Server settings
    host: str = Field(default="0.0.0.0", alias="LIBSCOPE_HOST")
    port: int = Field(default=8000, alias="LIBSCOPE_PORT")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        alias="LIBSCOPE_CORS_ORIGINS",
    )
    api_key: str | None = Field(default=None, alias="LIBSCOPE_API_KEY")
    enable_demo_mode: bool = Field(default=False, alias="LIBSCOPE_ENABLE_DEMO_MODE")

    # Database settings
    database_url: str = Field(
        default="sqlite:///./data/libscope.db",
        alias="LIBSCOPE_DATABASE_URL",
    )

    # Network & Reliability
    request_timeout: float = Field(default=15.0, alias="LIBSCOPE_REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="LIBSCOPE_MAX_RETRIES")
    retry_backoff_factor: float = Field(default=1.5, alias="LIBSCOPE_RETRY_BACKOFF_FACTOR")
    cache_ttl_seconds: int = Field(default=3600, alias="LIBSCOPE_CACHE_TTL_SECONDS")
    analysis_timeout_seconds: float = Field(default=900.0, gt=0, le=86400, alias="LIBSCOPE_ANALYSIS_TIMEOUT")
    enforce_ssrf_protection: bool = Field(default=True, alias="LIBSCOPE_ENFORCE_SSRF_PROTECTION")

    # GitHub credentials (reads GITHUB_TOKEN or GH_TOKEN)
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    gh_token_fallback: str | None = Field(default=None, alias="GH_TOKEN")

    # AI Configuration
    ai_provider: str = Field(default="openrouter", alias="LIBSCOPE_AI_PROVIDER")
    ai_api_key: str | None = Field(default=None, alias="LIBSCOPE_AI_API_KEY")
    ai_model: str = Field(default="openai/gpt-4o-mini", alias="LIBSCOPE_AI_MODEL")
    ai_base_url: str | None = Field(default=None, alias="LIBSCOPE_AI_BASE_URL")
    ai_temperature: float = Field(default=0.2, alias="LIBSCOPE_AI_TEMPERATURE")
    ai_max_tokens: int = Field(default=2048, alias="LIBSCOPE_AI_MAX_TOKENS")

    # OpenRouter fallback
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    azure_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_api_version: str | None = Field(default=None, alias="AZURE_OPENAI_API_VERSION")
    azure_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT_NAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_github_token(self) -> str | None:
        """Resolve GitHub token from configured GITHUB_TOKEN, GH_TOKEN, or system environment."""
        token = self.github_token or self.gh_token_fallback or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        return token.strip() if token else None

    @property
    def effective_ai_api_key(self) -> str | None:
        """Resolve the configured provider's key without falling back across providers."""
        provider = self.ai_provider.lower().strip()
        provider_key = {
            "openrouter": self.openrouter_api_key or os.getenv("OPENROUTER_API_KEY"),
            "default": self.openrouter_api_key or os.getenv("OPENROUTER_API_KEY"),
            "openai": self.openai_api_key or os.getenv("OPENAI_API_KEY"),
            "anthropic": self.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"),
            "google": (
                self.google_api_key
                or os.getenv("GOOGLE_API_KEY")
                or self.gemini_api_key
                or os.getenv("GEMINI_API_KEY")
            ),
            "gemini": (
                self.google_api_key
                or os.getenv("GOOGLE_API_KEY")
                or self.gemini_api_key
                or os.getenv("GEMINI_API_KEY")
            ),
            "groq": self.groq_api_key or os.getenv("GROQ_API_KEY"),
            "azure": self.azure_api_key or os.getenv("AZURE_OPENAI_API_KEY"),
        }.get(provider)
        key = self.ai_api_key or provider_key
        return key.strip() if key else None

    @property
    def parsed_cors_origins(self) -> list[str]:
        if not self.cors_origins:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()

