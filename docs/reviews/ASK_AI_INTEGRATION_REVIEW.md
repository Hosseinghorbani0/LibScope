# Ask-AI (askai-python) Technical Audit & Integration Review
**Document Version:** 1.0.0  
**Target Library:** `askai-python` (version 0.6.0)  
**Author / Reviewer:** Principal Software Architect & AI Systems Engineer (LibScope)  
**Date:** 2026-11-08  

---

## Executive Summary

`askai-python` (import name: `ask_ai`, distribution name: `askai-python`) is a lightweight Python unified abstraction layer for multiple Large Language Model (LLM) and multimodal API providers. Its stated philosophy is *"AI Made Stupid Simple"*—providing a one-line entry point to switch between model providers (OpenAI, OpenRouter, Anthropic, Google, Groq, Azure) with uniform invocation, configuration, and structured output handling.

This audit evaluates the codebase located at `D:\github_fork\ask-ai`, analyzing its architectural design, public interface contracts, provider drivers, streaming implementations, type safety, error hierarchy, and security posture. It establishes how LibScope can natively integrate `askai-python` as its primary AI intelligence engine while preserving LibScope's strict non-negotiable guarantees: deterministic factual metrics, prompt injection defense, offline resiliency, and clean open-source packaging.

---

## A. Architecture Understanding

The internal architecture of `ask_ai` follows an object-oriented provider pattern with functional hooks and optional observability middleware.

### 1. Module Composition
```
ask_ai/
├── __init__.py          # Public exports (providers, config, exceptions, events, router)
├── base.py              # BaseProvider ABC, Response wrapper, execution & retry loops
├── capabilities.py      # Capabilities dataclass (streaming, structured_output, tools, etc.)
├── config.py            # AdvancedConfig, CONFIG_OPTION_NAMES, validate_option_names
├── events.py            # Typed streaming events: TextDelta, ToolCall, UsageUpdate, Completed, Error
├── exceptions.py        # Exception hierarchy (AskAIError, ProviderError, StructuredValidationError)
├── media.py             # ImageObject, AudioObject abstractions
├── media_security.py    # MediaPolicy, download validation (SSRF and MIME restrictions)
├── observability.py     # Observability middleware, ResponseMetadata, Usage token metrics
├── router.py            # Deterministic multi-provider routing (most_reliable, cheapest, fastest)
├── session.py           # Multi-turn ConversationSession manager with sliding window
├── structured.py        # Strict JSON Schema normalization, dataclass/Pydantic validation
├── utils.py             # String hygiene (clean_markdown, strip_tags, extract_code)
└── providers/           # Concrete provider drivers
    ├── openai_provider.py
    ├── openrouter_provider.py
    ├── anthropic_provider.py
    ├── google_provider.py
    ├── groq_provider.py
    └── azure_provider.py
```

### 2. Execution Pipeline
When a request is initiated via `provider.ask(query, **kwargs)` or `await provider.ask_async(query, **kwargs)`:
1. **Fallback Resolution:** Checks for `providers` or `fallback` parameters to handle cascading failover across provider instances.
2. **Configuration Merging:** Merges instance-level `AdvancedConfig` with per-request keyword arguments (`_build_final_config`).
3. **Message Preparation:** Formats input into OpenAI-style chat messages `[{"role": "system", ...}, {"role": "user", ...}]`.
4. **Driver Dispatch:** Calls `_send_request` or `_send_request_async` in the concrete provider class.
5. **Schema-Constrained Generation:** If `response_model` is specified, `strict_json_schema` generates an OpenAI-compatible JSON schema or falls back to prompt injection schema if unsupported by the backend.
6. **Validation & Correction Loop:** If the response violates the schema, catches `StructuredValidationError` and re-prompts the model up to `validation_retries` times with the validation error message.
7. **Metadata & Observability:** Injects `ResponseMetadata` (latency, retries, usage tokens) and fires events to attached `Observability` middleware.

---

## B. Verified Public API

Based strictly on source inspection and test coverage (specifically `ask_ai/base.py`, `ask_ai/structured.py`, and `ask_ai/providers/`), the following public interfaces are verified for production usage:

### 1. Provider Instantiation
```python
from ask_ai import OpenRouter, OpenAI, Anthropic, Google, Groq, Azure

# OpenRouter (recommended for LibScope: unified access to Claude, GPT-4o, Gemini, Llama)
client = OpenRouter(
    api_key="sk-or-v1-...",        # or reads OPENROUTER_API_KEY from environment
    model="openai/gpt-4o-mini",   # default is openai/gpt-4o
    timeout=30.0,
)

# OpenAI
client = OpenAI(
    api_key="sk-...",             # or reads OPENAI_API_KEY from environment
    model="gpt-4o-mini",
    timeout=20.0,
)
```

### 2. Synchronous & Asynchronous Invocations
```python
# Sync invocation
response = client.ask("Analyze package telemetry", temperature=0.2)
print(response.text)

# Native async invocation (uses AsyncOpenAI / native async driver, non-blocking)
response = await client.ask_async("Analyze package telemetry", temperature=0.2)
print(response.text)
```

### 3. Structured Outputs (`response_model`)
Verified against `ask_ai/structured.py` and `tests/test_native_structured.py`:
- Supports Pydantic v1 (`parse_obj`) and Pydantic v2 (`model_validate`, `model_json_schema`).
- Supports standard Python `@dataclass`.
- Supports `typing.TypedDict`.
- Supports raw JSON Schema dictionaries with optional `jsonschema` validation.

```python
from pydantic import BaseModel
from ask_ai import OpenRouter

class RiskAssessment(BaseModel):
    risk_level: str
    reasons: list[str]

client = OpenRouter()
resp = await client.ask_async(
    "Evaluate repository commit gaps",
    response_model=RiskAssessment,
    validation_retries=2,
)
# Access validated Pydantic model directly:
result: RiskAssessment = resp.parsed  # or resp.pydantic
print(result.risk_level, result.reasons)
```

### 4. Router Multi-Provider Resiliency
```python
from ask_ai import Router, OpenRouter, OpenAI

# Configures multi-provider failover
router = Router(
    providers=[OpenRouter(), OpenAI()],
    policy="most_reliable",  # or "cheapest", "fastest"
)
resp = await router.ask_async("Synthesize maintainer recommendations")
```

---

## C. Provider Compatibility Matrix

| Provider Class | Underlying SDK | Env Var | Async Native? | Structured Output? | Streaming? | Vision/Media? |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **OpenRouter** | `openai` | `OPENROUTER_API_KEY` | **Yes** (`AsyncOpenAI`) | **Yes** (Strict Schema) | **Yes** | Image gen only |
| **OpenAI** | `openai` | `OPENAI_API_KEY` | **Yes** (`AsyncOpenAI`) | **Yes** (Strict Schema) | **Yes** | **Yes** |
| **Anthropic** | `anthropic` | `ANTHROPIC_API_KEY` | **Yes** (`AsyncAnthropic`)| **Yes** (Tool/Schema) | **Yes** | Vision only |
| **Google** | `google-genai` | `GEMINI_API_KEY` / `GOOGLE_API_KEY` | **Yes** | **Yes** | **Yes** | **Yes** |
| **Groq** | `groq` | `GROQ_API_KEY` | **Yes** (`AsyncGroq`) | **Yes** | **Yes** | No |
| **Azure** | `openai` | `AZURE_OPENAI_API_KEY` | **Yes** (`AsyncAzureOpenAI`)| **Yes** | **Yes** | **Yes** |

---

## D. Integration Opportunities for LibScope

1. **Elimination of Hand-Crafted HTTP Chat Payloads:** LibScope previously made raw HTTP calls in `libscope/ai/client.py`. Replacing this with `askai-python` eliminates boilerplate, standardizes retries, and leverages built-in model routing.
2. **Unified Multi-Provider Selection:** LibScope users can seamlessly toggle between OpenRouter, OpenAI, Groq, Google, and Anthropic simply by passing environment variables without LibScope maintaining individual provider drivers.
3. **Native Pydantic Structured Output Validation:** Instead of manually extracting markdown backticks `` ```json ... ``` ``, LibScope can leverage `response_model=PydanticModel` with automated `validation_retries` built into `askai-python`.
4. **Multi-Provider Failover:** LibScope can configure `Router(providers=[...])` so if a provider experiences 429 rate limits or network degradation, queries automatically failover without crashing report generation.

---

## E. Problems, Weaknesses, and Risks in askai-python

The following findings were uncovered through direct source audit of `ask-ai`:

### Finding ASK-01: Hard Dependency on `openai` Library in Base Providers
- **Severity:** High
- **Affected Component:** `ask_ai/providers/openrouter_provider.py` (Line 4-7, 31-32), `ask_ai/providers/openai_provider.py`
- **Technical Explanation:** In `pyproject.toml`, `dependencies = []` (core is zero-dependency). However, `OpenRouterProvider` and `OpenAIProvider` immediately fail at runtime with `ProviderError("OpenAI client library not installed. Run: pip install openai")` if `openai>=1.0.0` is not installed.
- **Evidence:** `openrouter_provider.py:31`:
  ```python
  if openai is None:
      raise ProviderError("OpenAI client library not installed. Run: pip install openai")
  ```
- **Impact on LibScope:** LibScope's `pyproject.toml` must explicitly declare `askai-python` and include the provider extras or `openai>=1.0.0` so end users do not encounter runtime import errors.
- **Recommended Solution:** LibScope must declare `dependencies = [..., "askai-python>=0.6.0", "openai>=1.0.0"]`.

---

### Finding ASK-02: Base Provider Init Immediately Evaluates API Key Presence
- **Severity:** Medium
- **Affected Component:** `ask_ai/providers/openrouter_provider.py` (Line 35-36), `ask_ai/providers/openai_provider.py` (Line 43-44)
- **Technical Explanation:** When `OpenRouter()` or `OpenAI()` is instantiated without an `api_key` argument, it immediately checks `os.environ.get(...)` and raises `APIKeyError` inside `__init__`. This prevents creating provider singleton instances at application startup if the user has not configured API keys.
- **Evidence:** `openrouter_provider.py:35-36`:
  ```python
  self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
  if not self.api_key:
      raise APIKeyError("OpenRouter API Key is missing. Set OPENROUTER_API_KEY env var or pass api_key=")
  ```
- **Impact on LibScope:** LibScope must NOT eagerly instantiate `ask_ai` provider classes when AI is disabled or when keys are absent. Instantiation must be lazy and guarded by credential checks.
- **Recommended Solution:** LibScope's `AIClient` layer must lazily instantiate the `ask_ai` provider only when credentials are confirmed, and catch `AskAIConfigError` / `APIKeyError` gracefully.

---

### Finding ASK-03: `strict_options` Deprecation Warnings on Extra Parameters
- **Severity:** Low
- **Affected Component:** `ask_ai/config.py` (Line 32-46)
- **Technical Explanation:** `AdvancedConfig` validates option names against `CONFIG_OPTION_NAMES`. If custom kwargs are passed that are not in the predefined frozenset, `validate_option_names` emits a Python `UserWarning`.
- **Evidence:** `config.py:45`: `warnings.warn(message, UserWarning, stacklevel=3)`
- **Impact on LibScope:** LibScope should only pass parameters recognized in `CONFIG_OPTION_NAMES` (`temperature`, `max_tokens`, `system_message`, `timeout`, `retry`, `response_model`, `validation_retries`).
- **Recommended Solution:** Pass clean kwargs strictly conforming to `CONFIG_OPTION_NAMES`.

---

### Finding ASK-04: Non-Strict Schema Fallback Behavior on Unrecognized Errors
- **Severity:** Medium
- **Affected Component:** `ask_ai/structured.py` (Line 177-206)
- **Technical Explanation:** `is_unsupported_response_schema_error` checks for specific keywords in error messages (like `response_format`, `json_schema`, `structured_output`). If a provider returns a non-standard 400 error message, the fallback to prompt-injected schema is not triggered, and an exception is raised.
- **Impact on LibScope:** LibScope's output validator must be defensive: catch `AskAIError` / `StructuredValidationError` and fall back to LibScope's deterministic heuristic analysis if the schema exchange fails.
- **Recommended Solution:** Wrap all `ask_ai` structured calls in LibScope service boundary handlers with graceful degradation.

---

## F. Improvement Suggestions for askai-python Maintainers

*(Note: In accordance with instructions, askai-python source files remain completely untouched).*

1. **Lazy Client Construction in Providers:** Defer `openai.OpenAI(...)` client creation until the first `.ask()` or `.ask_async()` call, rather than raising `APIKeyError` during `__init__`. This allows dependency injection and lazy configuration.
2. **First-Class OpenRouter Base URL Overrides:** `OpenRouterProvider` hardcodes `base_url="https://openrouter.ai/api/v1"`. Permitting an optional `base_url` parameter would allow testing against mock servers or enterprise proxies.
3. **Structured Output Fallback Diagnostics:** In `structured.py`, attach the raw invalid text to `StructuredValidationError` as an attribute `error.raw_text` so calling applications can log or salvage partial responses without re-parsing.

---

## G. Integration Decision & Architecture Boundary

Based on verified capabilities:

1. **What askai-python will handle:**
   - Provider abstraction: dynamically instantiating `OpenRouter`, `OpenAI`, `Anthropic`, `Groq`, `Google`, or `Azure`.
   - Async network transport: using native `ask_async()`.
   - Structured JSON schema generation and validation: passing Pydantic models via `response_model`.
   - Self-correction retries: using `validation_retries=2`.
   - Per-request configuration: `temperature=0.2`, `timeout=30.0`.

2. **What LibScope will handle at its boundary:**
   - **Deterministic evidence compilation:** LibScope gathers telemetry from PyPI, GitHub, and OSV, and compiles structured evidence *before* invoking AI.
   - **Prompt injection defense:** LibScope sanitizes untrusted READMEs/metadata and wraps them in `<untrusted_external_content>` tags before sending them to `askai-python`.
   - **Credential validation & Offline fallback:** LibScope checks if credentials exist; if not, LibScope bypasses `askai-python` and generates rule-based deterministic intelligence reports.
   - **Output validation:** LibScope validates all returned Pydantic schemas and guards against truncated or malformed responses.

---
*Report verified against askai-python 0.6.0.*

