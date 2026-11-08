# Contributing to LibScope

Thank you for your interest in contributing to **LibScope**! We welcome contributions from developers, security researchers, and data engineers.

---

## 1. Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all contributors with respect and professionalism.

---

## 2. Architectural Principles

Before contributing code, please keep our fundamental design constraints in mind:

1. **Evidence-Based & Fact-Driven**: Calculations, telemetry measurements, and scoring MUST remain strictly deterministic. Never fabricate metrics or present estimates as facts.
2. **AI as Interpretation, Not Fact Generation**: AI models synthesize and interpret verified telemetry. AI must never generate telemetry numbers.
3. **Graceful Fallback**: All AI-assisted capabilities must have fully functional, deterministic offline fallbacks that activate seamlessly when credentials or network connectivity are absent.
4. **Security by Default**: All network requests to external APIs must pass through our SSRF and host validation layer (`libscope.core.security`). Untrusted content (READMEs, issue text) must be sanitized before passing into prompts.
5. **No Vendoring of External Libraries**: External libraries such as `askai-python` must be consumed exclusively via standard package management (`pip install`). Never vendor their local repositories or include their source directories in git tracking.

---

## 3. Development Setup

### Prerequisites
- Python 3.11 or higher
- Node.js 20+ and npm 10+ (for the Web Dashboard)
- Git

### Initializing the Workspace

```bash
# Clone the repository
git clone https://github.com/libscope/libscope.git
cd libscope

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies in editable mode
pip install -e ".[dev]"

# Install Dashboard dependencies
cd apps/dashboard
npm install
npm run build
cd ../..
```

---

## 4. Running Tests

LibScope maintains 100% passing unit and integration test suites:

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run full test suite with coverage
pytest tests/ -v
```

---

## 5. Coding Standards

- **Formatting & Linting**: We use [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting:
  ```bash
  ruff check .
  ruff format .
  ```
- **Type Annotations**: All public methods and functions must have type hints.
- **Pydantic Schemas**: Use Pydantic v2 schemas for all API payloads and AI structured outputs.

---

## 6. Extending LibScope

### Adding an Ecosystem Provider
To add a new ecosystem (e.g., npm, Crates.io, Go modules):
1. Create `packages/providers/libscope/providers/<ecosystem>.py`.
2. Inherit from `BaseProvider` in `libscope.providers.base`.
3. Implement `fetch_metadata`, `fetch_releases`, `fetch_downloads`, and `resolve_identity`.
4. Register the new provider class in `ProviderRegistry` (`packages/providers/libscope/providers/registry.py`).
5. Add unit and integration tests with mocked HTTP responses.

### Adding an AI Analysis Service
To add a new structured AI assessment:
1. Define output schema inheriting from `BaseAIOutput` in `packages/ai/libscope/ai/models.py`.
2. Create prompt templates in `packages/ai/libscope/ai/prompts/`.
3. Implement the service class in `packages/ai/libscope/ai/services/` with an obligatory `_build_deterministic_fallback` method.
4. Export the service in `packages/ai/libscope/ai/services/__init__.py`.
5. Add unit tests covering both the online (mocked provider) and offline (fallback) modes.

---

## 7. Submitting a Pull Request

1. Fork the repo and create a feature branch (`git checkout -b feature/my-enhancement`).
2. Verify all tests pass (`pytest tests/`).
3. Verify formatting and linting pass (`ruff check .`).
4. Commit your changes with concise, descriptive commit messages.
5. Push to your branch and open a Pull Request using the PR template.

