<div align="center">

# LibScope

**Open-Source Software Intelligence. Beyond Downloads.**

[![CI Pipeline](https://github.com/libscope/libscope/actions/workflows/ci.yml/badge.svg)](https://github.com/libscope/libscope/actions)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![AI Engine: askai-python](https://img.shields.io/badge/AI%20Engine-askai--python-purple.svg)](https://pypi.org/project/askai-python/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

*A production-grade, extensible open-source software intelligence platform that analyzes software packages and repositories, discovers real-world adoption evidence, measures ecosystem health, tracks trends, and produces objective, evidence-based intelligence reports.*

[Features](#features) • [Architecture](#architecture) • [Quickstart](#quickstart) • [CLI Usage](#cli-usage) • [REST API & Dashboard](#web-dashboard--rest-api) • [AI Engine Integration](#ai-engine-integration-askai-python) • [Docker](#docker-deployment) • [Contributing](#contributing)

</div>

---

## The Problem

Software engineering teams and open-source consumers frequently select packages using misleading vanity metrics:
- **Raw download counts** are heavily distorted by automated CI/CD pipelines, mirrors, cloud build agents, and automated bots.
- **GitHub stars** reflect social media virality rather than real-world production reliability.
- **Dormant repositories** appear active due to automated dependabot commits while maintainers have completely moved on.
- **Security vulnerabilities** remain hidden until downstream systems are compromised.

**LibScope** solves this by providing empirical, multi-dimensional software intelligence. It goes **beyond downloads** to verify whether independent projects are actually importing a package, evaluates engineering discipline, scores packages deterministically, and synthesizes structured reports.

---

## Features

- **Empirical Adoption Discovery**:
  Scans public repository manifests (e.g. `pyproject.toml`, `requirements.txt`, `setup.cfg`) and classifies citations into 5 rigorous tiers (`Confirmed dependency`, `Confirmed usage`, `Possible usage`, `Mention only`, `Unverified`), automatically deduplicating citations and filtering self-repositories.

- **Deterministic 7-Dimension Scoring (`v1.0.0`)**:
  Computes fully explainable scores across **Popularity**, **Growth**, **Adoption**, **Maintenance**, **Documentation**, **Quality**, and **Security**. Explicitly indicates `"Insufficient data"` and confidence levels rather than guessing.

- **Download Anomaly & Trend Detection**:
  Calculates 7-day and 30-day moving averages and uses Z-score statistical anomaly detection to distinguish natural growth from bot-driven download spikes. Distinguishes mirror-inclusive vs mirror-exclusive statistics.

- **Engineering Hygiene & OSV Auditing**:
  Inspects commit cadence, release frequency, OSI licenses, documentation completeness (`README`, `CONTRIBUTING`, `SECURITY.md`), and audits open CVEs/GHSAs using the Google Open Source Vulnerabilities (OSV) database.

- **Native AI Analyst Powered by `askai-python`**:
  Integrates `askai-python` for structured interpretation, executive summaries, risk assessments, and maintainer recommendations. Backed by strict prompt injection sanitization and **100% deterministic offline fallback** when AI credentials are absent.

- **Multi-Interface Delivery**:
  - **Terminal CLI**: Rich interactive console with side-by-side package comparisons, table visualizations, and offline benchmarking.
  - **REST API**: Production FastAPI backend with background job orchestration and OpenAPI / Swagger documentation.
  - **Web Dashboard**: Framework-free HTML, CSS, and modern JavaScript served directly by FastAPI; no frontend build or Node.js runtime is required.
  - **Executive Reports**: Multi-format generation in Markdown, JSON, and self-contained interactive HTML.

---

## Architecture

LibScope follows a strictly decoupled, modular architecture designed for high extensibility:

```mermaid
flowchart TD
    subgraph Data Providers
        PyPI[PyPI Provider<br/>JSON API + pypistats]
        GH[GitHub Provider<br/>Metrics + Code Search]
        OSV[OSV Database<br/>Vulnerability Auditing]
    end

    subgraph Analyzers
        DL[Downloads Analyzer<br/>Z-Score + Moving Averages]
        Repo[Repository Analyzer<br/>Commit & Release Cadence]
        Adopt[Adoption Analyzer<br/>5-Tier Manifest Classifier]
        Health[Health Analyzer<br/>Hygiene & Community Files]
        Sec[Security Analyzer<br/>Advisory Severity Auditor]
        Comp[Competitor Analyzer<br/>Matrix Normalization]
    end

    subgraph Scoring Engine
        Score[Deterministic Scoring v1.0.0<br/>7 Dimensions + Confidence Rating]
    end

    subgraph Native AI Engine
        AskAI["askai-python Integration Layer<br/>(OpenRouter / OpenAI / Anthropic / Gemini / Groq)"]
        Sanitize[Security Sanitizer<br/>Prompt Injection Barrier]
        Fallback[Deterministic Fallback Engine<br/>100% Air-gapped Offline Guarantee]
    end

    subgraph Delivery & Interfaces
        CLI[Typer CLI<br/>Rich Visualizations]
        API[FastAPI REST Engine<br/>Background Orchestration]
        UI[Native HTML/CSS/JavaScript Dashboard<br/>Served by FastAPI]
        Reports[Multi-Format Reports<br/>Markdown / JSON / HTML]
    end

    PyPI --> DL
    PyPI --> Health
    GH --> Repo
    GH --> Adopt
    GH --> Health
    OSV --> Sec

    DL --> Score
    Repo --> Score
    Adopt --> Score
    Health --> Score
    Sec --> Score

    Score --> Sanitize
    Sanitize --> AskAI
    AskAI -.->|If Offline or Error| Fallback
    AskAI --> Reports
    Fallback --> Reports

    Score --> API
    Score --> CLI
    Reports --> API
    Reports --> CLI
    API --> UI
```

---

## Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/libscope/libscope.git
cd libscope

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install libscope with core dependencies
pip install -e .
```

To enable live AI provider calls, install the optional provider SDKs as well:

```bash
pip install -e ".[ai]"
```

### 2. Run the Offline Demo Benchmark

Verify the entire scoring, comparison, and reporting engine without needing external API tokens:

```bash
# Seed the benchmark dataset (fastapi, requests, askai-python)
libscope demo

# Compare packages side-by-side
libscope compare fastapi requests

# Generate an intelligence report
libscope report 1 --format markdown
```

---

## CLI Usage

LibScope provides a full-featured terminal interface:

```bash
# Analyze a package from PyPI
libscope analyze fastapi

# Analyze a package with GitHub token for higher rate limits
GITHUB_TOKEN="ghp_xxx" libscope analyze askai-python

# Compare multiple competing packages
libscope compare fastapi flask django

# List registered ecosystem providers and their capabilities
libscope providers

# View active environment and database configuration
libscope config

# Inspect historical snapshot trends for a package
libscope history fastapi
```

---

## Web Dashboard & REST API

### Launching the Web Server

```bash
# Install LibScope and launch the FastAPI application.
# Dashboard assets are included with the API package; no Node.js or frontend build is needed.
pip install -e .
# Local-only development mode (production requires an API key)
export LIBSCOPE_ENVIRONMENT=development
uvicorn libscope.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive Dashboard**: Navigate to [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger UI)**: Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: `curl http://localhost:8000/health`

The dashboard uses same-origin relative API URLs and native browser `fetch`. Its static HTML, CSS, and JavaScript are served from `/` and `/dashboard-assets/` and are included in the Python distribution. Browsers do not need Node.js or any frontend installation.

The dashboard interface is available in English, Persian, and Arabic. Persian and Arabic switch the page to right-to-left layout; the language preference is stored in this browser, while API keys remain memory-only.

### Key REST Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/health` | System health check and version status |
| `GET` | `/api/v1/dashboard/summary` | Exact package/repository/score totals and a bounded recent-job list |
| `GET` | `/api/v1/packages` | List analyzed packages with latest scores |
| `GET` | `/api/v1/packages/{id}` | Detailed package telemetry and findings |
| `GET` | `/api/v1/packages/{id}/analytics?limit=100&offset=0` | Paginated metric snapshots (1-500 per request) |
| `GET` | `/api/v1/packages/{id}/history?limit=100` | Bounded historical snapshots, chart points, and recent deltas |
| `GET` | `/api/v1/packages/{id}/score-history?limit=100` | Bounded, chronological stored score observations |
| `GET` | `/api/v1/packages/{id}/adoption/status` | Adoption discovery status and verification caveats |
| `POST` | `/api/v1/analyze` | Trigger asynchronous package analysis job |
| `GET` | `/api/v1/jobs/{id}` | Inspect analysis job progress and status |
| `POST` | `/api/v1/compare` | Multi-package comparative analysis |
| `POST` | `/api/v1/reports/generate` | Generate Markdown, JSON, or HTML reports |
| `POST` | `/api/v1/demo/seed` | Seed benchmark dataset |

In production, set `LIBSCOPE_API_KEY` to a strong secret. The dashboard's **Settings → API Access** form accepts an operator-provided key and keeps it only in tab memory; it is not embedded in the frontend bundle or persisted to browser storage. Use a managed identity or authenticated gateway for multi-user deployments, and provide this shared key only to trusted operators.

---

## AI Engine Integration (`askai-python`)

LibScope integrates [`askai-python`](https://pypi.org/project/askai-python/) as its native AI integration layer.

### Why `askai-python`?
- **Unified Provider Abstraction**: Seamlessly interface with OpenRouter, OpenAI, Anthropic, Google Gemini, Groq, and Azure OpenAI using a single, consistent API.
- **Native Structured Outputs**: Guarantees typed Pydantic output schemas via `response_model` with automatic retry logic.
- **Async & Sync Support**: Powers both asynchronous FastAPI pipelines and synchronous CLI commands.

### Configuring AI Credentials

The base installation includes the `askai-python` integration but not its optional provider SDKs. Install `.[ai]` to enable all supported providers. Azure OpenAI additionally requires its endpoint, API version, and deployment settings. Custom base URLs are supported only for OpenRouter and OpenAI-compatible providers and remain subject to the outbound URL policy.

Set your desired provider credentials in your environment or `.env` file:

```bash
# Enable OpenRouter (Recommended: access Claude 3.5, GPT-4o, Llama 3 via one key)
export OPENROUTER_API_KEY="sk-or-v1-..."
export LIBSCOPE_AI_PROVIDER="openrouter"
export LIBSCOPE_AI_MODEL="anthropic/claude-3.5-sonnet"

# Or configure OpenAI directly
export OPENAI_API_KEY="sk-..."
export LIBSCOPE_AI_PROVIDER="openai"
export LIBSCOPE_AI_MODEL="gpt-4o"

# Or configure Google Gemini
export GEMINI_API_KEY="AIzaSy..."
export LIBSCOPE_AI_PROVIDER="google"
export LIBSCOPE_AI_MODEL="gemini-1.5-pro"

# Or configure Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_VERSION="2024-10-21"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"
export LIBSCOPE_AI_PROVIDER="azure"
```

### 100% Offline / Air-Gapped Guarantee

If no AI keys are configured or if the external AI provider is unreachable, LibScope **automatically falls back to deterministic analysis**:
- All scores, metrics, and findings remain 100% available.
- Reports generate with an explicit `[Deterministic Intelligence Report - AI Engine Offline]` advisory tag.
- AI is **never** permitted to generate or guess factual telemetry numbers.

---

## Docker Deployment

Deploy LibScope with a single command:

```bash
# Set a strong secret before starting the production container
export LIBSCOPE_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Build and run with docker compose
docker compose up -d

# Check service logs
docker compose logs -f libscope

# Verify health status
curl http://localhost:8000/health
```

For production, expose the service through an HTTPS-terminating reverse proxy; do not transmit bearer keys over plain HTTP.

---

## Security

LibScope enforces strict defensive controls:
- **SSRF Protection**: LibScope-managed provider requests validate resolved IP addresses and block cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`) and private/loopback IP address ranges. Custom OpenAI-compatible and Azure AI endpoints are validated before use.
- **API Access Control**: Production analysis, report-generation, and demo-seeding routes require `Authorization: Bearer <key>` and are rate-limited. Never place the server key in static frontend assets or source control.
- **Prompt Injection Defense**: Sanitizes and enforces character boundaries on all untrusted user content (e.g. package descriptions, READMEs) before passing them to the AI analyst.
- **Deterministic Separation**: Math, metrics, and scores are calculated purely in Python code; AI is restricted to interpretive synthesis.

For vulnerability disclosure instructions, see [SECURITY.md](SECURITY.md).

---

## Contributing

We welcome community contributions! Please review our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before opening a pull request.

---

## License

LibScope is released under the **[Apache-2.0 License](LICENSE)**.
