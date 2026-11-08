"""
Native AI Client integration layer for LibScope using askai-python.
"""
from typing import Any, Optional, Type
from libscope.ai.config import AIConfig
from libscope.ai.exceptions import (
    LibScopeAIConfigError,
    LibScopeAIError,
    LibScopeAIProviderError,
    map_ask_ai_exception,
)
from libscope.ai.prompts.system import BASE_SYSTEM_PROMPT
from libscope.core.logging import get_logger

logger = get_logger("ai.client")


class AskAIClient:
    """
    Unified client abstraction wrapping askai-python.
    Decouples LibScope business logic from provider-specific SDK details.
    """

    def __init__(self, config: Optional[AIConfig] = None):
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
                self._provider_instance = Azure(api_key=key, model=model, timeout=timeout)
            else:
                logger.warning(f"Unrecognized provider '{prov_name}', defaulting to OpenRouter")
                self._provider_instance = OpenRouter(api_key=key, model=model, timeout=timeout)

            logger.info(f"Initialized askai-python provider: {self._provider_instance.__class__.__name__} ({model})")
            return self._provider_instance

        except Exception as exc:
            self._init_error = str(exc)
            logger.error(f"Failed to instantiate askai-python provider '{prov_name}': {exc}")
            raise map_ask_ai_exception(exc, provider_name=prov_name) from exc

    async def ask_async(
        self,
        prompt: str,
        response_model: Optional[Type] = None,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
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
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
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
        response_model: Optional[Type] = None,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
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

