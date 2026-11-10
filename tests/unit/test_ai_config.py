import pytest
from libscope.core.config import Settings


@pytest.mark.parametrize(
    ("provider", "key_name", "key_value"),
    [
        ("openrouter", "OPENROUTER_API_KEY", "openrouter-test"),
        ("openai", "OPENAI_API_KEY", "openai-test"),
        ("anthropic", "ANTHROPIC_API_KEY", "anthropic-test"),
        ("google", "GOOGLE_API_KEY", "google-test"),
        ("gemini", "GEMINI_API_KEY", "gemini-test"),
        ("groq", "GROQ_API_KEY", "groq-test"),
        ("azure", "AZURE_OPENAI_API_KEY", "azure-test"),
    ],
)
def test_ai_key_resolution_uses_selected_provider(monkeypatch, provider, key_name, key_value):
    key_names = (
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "AZURE_OPENAI_API_KEY",
    )
    for name in key_names:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LIBSCOPE_AI_PROVIDER", provider)
    monkeypatch.setenv(key_name, key_value)

    assert Settings(_env_file=None).effective_ai_api_key == key_value


def test_ai_key_does_not_fall_back_to_another_provider(monkeypatch):
    monkeypatch.setenv("LIBSCOPE_AI_PROVIDER", "anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LIBSCOPE_AI_API_KEY", raising=False)

    assert Settings(_env_file=None).effective_ai_api_key is None


def test_explicit_ai_key_overrides_provider_specific_key(monkeypatch):
    monkeypatch.setenv("LIBSCOPE_AI_PROVIDER", "openai")
    monkeypatch.setenv("LIBSCOPE_AI_API_KEY", "explicit-test")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")

    assert Settings(_env_file=None).effective_ai_api_key == "explicit-test"

