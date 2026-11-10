# Changelog

All notable changes to **LibScope** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- A bounded historical-analysis API endpoint with recent snapshot deltas and chart points.
- Optional `ai` installation extra for the provider SDKs supported by `askai-python`.

### Changed
- Replaced the React/TypeScript dashboard with a responsive, framework-free HTML/CSS/JavaScript interface served directly by FastAPI; frontend Node.js tooling is no longer required.
- Production analysis, report-generation, and demo-seeding routes require a configured bearer API key and are rate-limited.
- The dashboard can accept an operator-provided API key without persisting it in browser storage.
- Package comparisons are rate-limited, and analytics snapshots support bounded pagination.
- Dependency adoption is confirmed from supported manifest contents rather than repository filenames alone.
- Security lookup and report output distinguish clean results from incomplete or unavailable checks.
- Dashboard now handles failed package loads, queued-job duplicate submissions, and absent comparison scores.

### Fixed
- HTML reports escape untrusted data and only render validated HTTPS references.
- Markdown reports tolerate missing metrics and no longer represent an unperformed security check as clean.
- Repeated analyses update existing release records instead of inserting duplicate versions.

### Security
- Validated custom OpenAI-compatible and Azure AI endpoints against the outbound URL policy.

---

## [0.1.0] - 2026-11-08

### Added
- **Core Architecture & Telemetry**:
  - Modular package workspace (`core`, `providers`, `analyzers`, `scoring`, `reporting`, `ai`, `api`, `dashboard`, `cli`).
  - SQLAlchemy 2.x persistence layer with SQLite and PostgreSQL support.
  - SSRF protection layer with DNS verification, cloud metadata blocks, and private IP rejection.
  - Safe HTTP client defaults with user-agent attribution and connect timeouts.
- **Ecosystem Providers**:
  - `PyPIProvider`: Full PyPI JSON metadata parsing, release chronology, and pypistats daily/weekly/monthly downloads.
  - `GitHubProvider`: GitHub repository metrics (stars, forks, open issues, watchers, commit cadence, release recency, community profile, code search for manifest citations).
  - `ProviderRegistry`: Central registry with dynamic provider lookup and capability reporting.
- **Intelligence Analyzers**:
  - `DownloadsAnalyzer`: Z-score anomaly detection, 7-day and 30-day moving averages, mirror-exclusive vs mirror-inclusive differentiation.
  - `RepositoryAnalyzer`: Activity indicators, commit frequency, maintenance freshness, and archival detection.
  - `AdoptionAnalyzer`: 5-tier classification (`Confirmed dependency`, `Confirmed usage`, `Possible usage`, `Mention only`, `Unverified`), deduplication, and self-repo filtering.
  - `HealthAnalyzer`: Automated checks for README, LICENSE, CONTRIBUTING, SECURITY.md, and CI workflows.
  - `SecurityAnalyzer`: Integration with OSV database for CVE and GHSA vulnerability auditing.
  - `CompetitorAnalyzer`: Multi-package side-by-side comparative matrices with caveats on low-level dependencies vs high-level frameworks.
  - `HistoricalAnalyzer`: Longitudinal snapshot comparison and growth delta calculation.
- **Scoring Engine (`v1.0.0`)**:
  - Deterministic 7-dimension explainable scoring model (Popularity, Growth, Adoption, Maintenance, Documentation, Quality, Security).
  - Explicit `"Insufficient data"` and confidence indicators (`HIGH`, `MODERATE`, `LOW`).
- **AI Intelligence Integration**:
  - Integration with `askai-python` as the primary AI engine.
  - Structured output schemas with Pydantic v2 and validation retry enforcement.
  - Lazy provider instantiation supporting OpenRouter, OpenAI, Anthropic, Google Gemini, Groq, and Azure.
  - Fallback synthesis mechanism ensuring 100% operation when AI engine or network is offline.
  - Sanitization barrier against prompt injection attacks via untrusted package READMEs.
- **Multi-Format Reporting**:
  - Markdown, JSON, and self-contained interactive HTML executive reports.
- **Applications**:
  - REST API with FastAPI, async background orchestration, and health checks.
  - Interactive Single-Page Application (SPA) dashboard built with React 18, TypeScript, Vite, Tailwind CSS, and Lucide icons.
  - Rich CLI built with Typer for terminal diagnostics, comparisons, reports, and offline demo benchmarking.
