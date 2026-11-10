"""
Unit tests for LibScope AI client and configuration powered by askai-python.
"""
import asyncio
from types import SimpleNamespace

import pytest
from libscope.ai.client import AIClient, AskAIClient
from libscope.ai.config import AIConfig
from libscope.ai.exceptions import (
    LibScopeAIAuthenticationError,
    LibScopeAIConfigError,
    LibScopeAIRateLimitError,
    LibScopeAITimeoutError,
    map_ask_ai_exception,
)
from libscope.ai.models import PackageAnalysisOutput
from libscope.ai.output_validator import AIOutputValidator


def test_ai_config_defaults():
    cfg = AIConfig()
    assert cfg.enabled is True
    assert cfg.provider == "openrouter"
    assert cfg.model == "openai/gpt-4o-mini"
    assert cfg.timeout == 30.0
    assert cfg.retry_count == 2
    assert cfg.validation_retries == 2


def test_ai_client_availability():
    # Client with empty API key is not available
    cfg_empty = AIConfig(api_key="")
    client_empty = AskAIClient(config=cfg_empty)
    assert client_empty.is_available is False

    # Client with valid key is available
    cfg_active = AIConfig(api_key="test-api-key-12345")
    client_active = AskAIClient(config=cfg_active)
    assert client_active.is_available is True

    # Backwards compatibility alias
    assert AIClient is AskAIClient


def test_ai_client_get_provider_raises_when_unavailable():
    client = AskAIClient(config=AIConfig(api_key=""))
    assert not client.is_available

    with pytest.raises(LibScopeAIConfigError) as exc_info:
        client._get_provider()
    assert "no valid API key" in str(exc_info.value)


def test_unknown_ai_provider_fails_with_configuration_error():
    client = AskAIClient(config=AIConfig(provider="unknown", api_key="test-key"))

    with pytest.raises(LibScopeAIConfigError, match="Unsupported AI provider"):
        client._get_provider()


def test_custom_ai_base_url_requires_https_in_production(monkeypatch):
    monkeypatch.setattr(
        "libscope.ai.client.get_settings",
        lambda: SimpleNamespace(environment="production"),
    )
    monkeypatch.setattr("libscope.ai.client.validate_safe_url", lambda _url: True)
    client = AskAIClient(
        config=AIConfig(
            provider="openai",
            api_key="test-key",
            base_url="http://llm.example.com/v1",
        )
    )

    with pytest.raises(LibScopeAIConfigError, match="must use HTTPS"):
        client._get_provider()


@pytest.mark.parametrize(
    ("endpoint", "allowed", "message"),
    [
        (None, False, "requires AZURE_OPENAI_ENDPOINT"),
        ("http://azure.example.com", True, "not permitted"),
        ("https://127.0.0.1", False, "not permitted"),
    ],
)
def test_azure_endpoint_is_required_and_restricted(monkeypatch, endpoint, allowed, message):
    monkeypatch.setattr("libscope.ai.client.validate_safe_url", lambda _url: allowed)
    client = AskAIClient(
        config=AIConfig(
            provider="azure",
            api_key="test-key",
            azure_endpoint=endpoint,
        )
    )

    with pytest.raises(LibScopeAIConfigError, match=message):
        client._get_provider()


def test_provider_specific_ai_dependency_and_max_tokens(monkeypatch):
    provider = SimpleNamespace(ask_async=None)

    async def ask_async(_prompt, **kwargs):
        provider.kwargs = kwargs
        return SimpleNamespace(text="ok")

    provider.ask_async = ask_async
    config = AIConfig(api_key="test-key", max_tokens=123)
    client = AskAIClient(config=config)
    client._provider_instance = provider

    assert asyncio.run(client.ask_async("hello")) == "ok"
    assert provider.kwargs["max_tokens"] == 123


def test_exception_mapping():
    # Simulate ask-ai exceptions
    class MockAuthError(Exception):
        pass

    class MockRateError(Exception):
        pass

    class MockTimeoutError(Exception):
        pass

    MockAuthError.__name__ = "AuthenticationError"
    MockRateError.__name__ = "RateLimitError"
    MockTimeoutError.__name__ = "TimeoutError"

    err1 = map_ask_ai_exception(MockAuthError("Invalid key"), provider_name="openrouter")
    assert isinstance(err1, LibScopeAIAuthenticationError)

    err2 = map_ask_ai_exception(MockRateError("Quota exceeded"), provider_name="openai")
    assert isinstance(err2, LibScopeAIRateLimitError)

    err3 = map_ask_ai_exception(MockTimeoutError("Timed out"), provider_name="google")
    assert isinstance(err3, LibScopeAITimeoutError)


def test_output_validator_with_valid_model():
    data = PackageAnalysisOutput(
        summary="A high quality framework.",
        risks="Low risk.",
        opportunities="High adoption.",
        maintainer_recommendations="Keep releases regular.",
        competitive_position="Market leader.",
    )
    validated = AIOutputValidator.validate_model(data, PackageAnalysisOutput)
    assert validated.summary == "A high quality framework."
    assert validated.competitive_position == "Market leader."


def test_output_validator_with_dict():
    raw_dict = {
        "summary": "Synthesized summary.",
        "risks": "Minimal risks.",
        "opportunities": "Growth opportunity.",
        "maintainer_recommendations": "Add tests.",
        "competitive_position": "Top tier.",
        "extra_ignored_field": 123,
    }
    validated = AIOutputValidator.validate_model(raw_dict, PackageAnalysisOutput)
    assert validated.summary == "Synthesized summary."
    assert validated.maintainer_recommendations == "Add tests."
