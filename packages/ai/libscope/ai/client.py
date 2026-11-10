"""
Native AI Client integration layer for LibScope using askai-python.
"""
import asyncio
from typing import Any
from urllib.parse import urlsplit

import httpx
from libscope.ai.config import AIConfig
from libscope.ai.exceptions import (
    LibScopeAIConfigError,
    map_ask_ai_exception,
)
from libscope.ai.prompts.system import BASE_SYSTEM_PROMPT
from libscope.core.config import get_settings
from libscope.core.logging import get_logger
from libscope.core.security import validate_safe_url

logger = get_logger("ai.client")


class AskAIClient:
    """
    Unified client abstraction wrapping askai-python.
    Decouples LibScope business logic from provider-specific SDK details.
    """

    def __init__(self, config: AIConfig | None = None):
        self.config = config or AIConfig.from_env()
        self._provider_instance = None
        self._init_error = None

    @property
    def is_available(self) -> bool:
        """Return True if AI is enabled and credentials are configured."""
        return self.config.enabled and bool(self.config.api_key and self.config.api_key.strip())

    def _get_provider(self):
        """Lazily instantiate the configured askai-python provider."""
        if not self.is_available:
            raise LibScopeAIConfigError(
                "AI is disabled or no valid API key is configured. Deterministic fallback should be used."
            )

        if self._provider_instance is not None:
            return self._provider_instance

        prov_name = self.config.provider.lower().strip()
        key = self.config.api_key
        model = self.config.model
        timeout = self.config.timeout

        try:
            supported_providers = {"openrouter", "default", "openai", "anthropic", "google", "gemini", "groq", "azure"}
            if prov_name not in supported_providers:
                raise LibScopeAIConfigError(f"Unsupported AI provider '{prov_name}'.")
            if prov_name == "azure":
                if not self.config.azure_endpoint:
                    raise LibScopeAIConfigError("Azure OpenAI requires AZURE_OPENAI_ENDPOINT.")
                if not self.config.azure_endpoint.lower().startswith("https://") or not validate_safe_url(
                    self.config.azure_endpoint
                ):
                    raise LibScopeAIConfigError("Azure OpenAI endpoint is not permitted by the outbound URL policy.")
            if self.config.base_url:
                if prov_name not in {"openrouter", "default", "openai"}:
                    raise LibScopeAIConfigError(
                        f"Custom base URLs are supported only for OpenAI-compatible providers, not '{prov_name}'."
                    )
                try:
                    scheme = urlsplit(self.config.base_url).scheme.lower()
                except ValueError as exc:
                    raise LibScopeAIConfigError("Configured AI base URL is invalid.") from exc
                if scheme != "https" and get_settings().environment.lower() == "production":
                    raise LibScopeAIConfigError("Custom AI base URLs must use HTTPS in production.")
                if not validate_safe_url(self.config.base_url):
                    raise LibScopeAIConfigError("Configured AI base URL is not permitted by the outbound URL policy.")

            from ask_ai import Anthropic, Azure, Google, Groq, OpenAI, OpenRouter

            if prov_name in ("openrouter", "default"):
                self._provider_instance = OpenRouter(api_key=key, model=model, timeout=timeout)
            elif prov_name == "openai":
                self._provider_instance = OpenAI(api_key=key, model=model, timeout=timeout)
            elif prov_name == "anthropic":
                self._provider_instance = Anthropic(api_key=key, model=model, timeout=timeout)
            elif prov_name in ("google", "gemini"):
                self._provider_instance = Google(api_key=key, model=model, timeout=timeout)
            elif prov_name == "groq":
                self._provider_instance = Groq(api_key=key, model=model, timeout=timeout)
            elif prov_name == "azure":
                self._provider_instance = Azure(
                    api_key=key,
                    model=self.config.azure_deployment or model,
                    deployment_name=self.config.azure_deployment,
                    endpoint=self.config.azure_endpoint,
                    api_version=self.config.azure_api_version,
                    timeout=timeout,
                )

            if self.config.base_url:
                self._configure_openai_compatible_base_url(self._provider_instance, key, timeout)

            logger.info(f"Initialized askai-python provider: {self._provider_instance.__class__.__name__} ({model})")
            return self._provider_instance

        except LibScopeAIConfigError:
            raise
        except Exception as exc:
            self._init_error = str(exc)
            logger.error(f"Failed to instantiate askai-python provider '{prov_name}': {exc}")
            raise map_ask_ai_exception(exc, provider_name=prov_name) from exc

    def _configure_openai_compatible_base_url(self, provider: Any, api_key: str | None, timeout: float) -> None:
        import openai

        base_url = self.config.base_url

        def validate_sync_request(request: httpx.Request) -> None:
            if not validate_safe_url(str(request.url)):
                raise httpx.RequestError("Outbound AI URL rejected by SSRF policy", request=request)

        async def validate_async_request(request: httpx.Request) -> None:
            allowed = await asyncio.to_thread(validate_safe_url, str(request.url))
            if not allowed:
                raise httpx.RequestError("Outbound AI URL rejected by SSRF policy", request=request)

        sync_client = httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            event_hooks={"request": [validate_sync_request]},
        )
        async_client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            event_hooks={"request": [validate_async_request]},
        )
        provider.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,
            http_client=sync_client,
        )
        provider._async_client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,
            http_client=async_client,
        )

    async def ask_async(
        self,
        prompt: str,
        response_model: type | None = None,
        system_message: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """
        Execute an asynchronous LLM completion using askai-python.
        """
        provider = self._get_provider()
        sys_msg = system_message or BASE_SYSTEM_PROMPT
        temp = temperature if temperature is not None else self.config.temperature

        kwargs = {
            "system_message": sys_msg,
            "temperature": temp,
            "timeout": self.config.timeout,
            "retry": self.config.retry_count,
        }
        kwargs["max_tokens"] = max_tokens if max_tokens is not None else self.config.max_tokens
        if response_model is not None:
            kwargs["response_model"] = response_model
            kwargs["validation_retries"] = self.config.validation_retries

        try:
            resp = await provider.ask_async(prompt, **kwargs)
            if response_model is not None:
                # Return parsed structured object from ask-ai
                return resp.parsed
            return resp.text
        except Exception as exc:
            mapped = map_ask_ai_exception(exc, provider_name=self.config.provider)
            logger.warning(f"askai-python execution failure: {mapped}")
            raise mapped from exc

    def ask_sync(
        self,
        prompt: str,
        response_model: type | None = None,
        system_message: str | None = None,
        temperature: float | None = None,
    ) -> Any:
        """Synchronous version for CLI or scripts."""
        provider = self._get_provider()
        sys_msg = system_message or BASE_SYSTEM_PROMPT
        temp = temperature if temperature is not None else self.config.temperature

        kwargs = {
            "system_message": sys_msg,
            "temperature": temp,
            "timeout": self.config.timeout,
            "retry": self.config.retry_count,
            "max_tokens": self.config.max_tokens,
        }
        if response_model is not None:
            kwargs["response_model"] = response_model
            kwargs["validation_retries"] = self.config.validation_retries

        try:
            resp = provider.ask(prompt, **kwargs)
            if response_model is not None:
                return resp.parsed
            return resp.text
        except Exception as exc:
            mapped = map_ask_ai_exception(exc, provider_name=self.config.provider)
            logger.warning(f"askai-python sync execution failure: {mapped}")
            raise mapped from exc


# Backwards compatibility alias
AIClient = AskAIClient
