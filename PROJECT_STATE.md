# LibScope Project State

## Purpose and architecture

LibScope analyzes software packages and repositories and produces evidence-based intelligence reports.

- **Backend/API:** Python 3.11+, FastAPI, SQLAlchemy, and Pydantic. API routes live under `apps/api/libscope/api/`; the orchestrator coordinates providers, analyzers, scoring, and persistence.
- **Providers and analyzers:** `packages/providers/` retrieves registry, GitHub, and OSV data; `packages/analyzers/` normalizes adoption, downloads, repository health, and security evidence.
- **Scoring and reports:** `packages/scoring/` calculates deterministic scores; `packages/reporting/` emits Markdown, JSON, and HTML.
- **AI:** `packages/ai/` wraps the published `askai-python` dependency. Provider SDKs are optional and installed with the `ai` extra. AI is interpretive; metrics and scores remain deterministic.
- **CLI:** Typer commands are in `apps/cli/`.
- **Dashboard:** Framework-free HTML, CSS, and JavaScript live in `apps/api/libscope/api/dashboard_static/`. FastAPI serves `/` and `/dashboard-assets/`; assets are included in the Python package. There is no frontend build or runtime dependency.
- **Persistence:** SQLAlchemy models are in `packages/core/libscope/core/models.py`; SQLite is the local default, PostgreSQL is supported.

## Important current behavior

- Production analysis, report-generation, and demo-seeding requests require `LIBSCOPE_API_KEY`; expensive API operations are rate-limited.
- The dashboard accepts an operator-provided bearer key in Settings and retains it in JavaScript memory only. It is not written to local storage, cookies, or the built bundle. This is intended for trusted single-operator use; multi-user deployments should use an authenticated gateway or managed identity.
- Dashboard API calls use same-origin relative URLs and the browser Fetch API, with consistent HTTP/network/timeout/invalid-JSON errors.
- Overview, analysis, comparison, adoption, package-detail tabs, history charts, security/health/AI details, report export, and settings are implemented with native DOM and SVG.
- `GET /api/v1/dashboard/summary` returns database-backed package, scored-package, repository, update-time, and recent-job summaries; recent-job fields intentionally exclude error messages.
- `GET /api/v1/packages/{id}/score-history` returns at most 200 stored score records. The dashboard renders a trend chart only when at least two numeric historical scores exist; it does not invent history.
- Package comparisons calculate the age of the latest commit and release from stored timestamps, treating naive timestamps as UTC and clamping future timestamps to zero days.
- Adoption results are only confirmed after supported manifest contents are fetched and parsed. Discovery status distinguishes checked, partial, unavailable, and failed searches from a checked empty sample.
- Security lookup status distinguishes checked results from partial, failed, rate-limited, unsupported, or not-yet-checked results.
- HTML reports escape dynamic content and only link to validated HTTPS URLs. Markdown reports distinguish missing values from verified clean results.
- Historical analytics are bounded and paginated; a separate history endpoint returns a bounded recent window.
- The integration uses installed `askai-python`; the local `ask-ai/` reference workspace is not part of the project.

## Git and release state

- Current branch: `engineering/remediation-v0.1.0`
- Current HEAD/base: `b8e1771025325e8ceb50d386e5b2e9ae0804ea11`
- `v0.1.0`, `backup/pre-rebuild`, and `safety/pre-remediation-v0.1.0` are preserved.
- Remediation changes are uncommitted. No commits, pushes, tag changes, or history rewrites have been made.
- The working tree includes source, test, dashboard, and documentation changes; inspect `git status` before continuing.
- Tests use a temporary SQLite database. The ignored project database was not used intentionally or removed.

## Validation completed

- `python -m pytest -p no:cacheprovider -o addopts= -q` — **84 passed**.
- Targeted `tests/integration/test_api.py` — **12 passed**, including dashboard summary, score history, and comparison age behavior.
- Ruff on `apps/api/libscope/api/main.py`, `packages/core/libscope/core/schemas.py`, and `tests/integration/test_api.py` — **passed**.
- `ruff check .` — **10 existing lint findings remain** in six untouched test modules (`test_ai_live.py`, `test_cli.py`, `test_providers.py`, `test_ai_services.py`, `test_downloads.py`, and `test_health_and_repo.py`).
- `node --check` on `app.js`, `api.js`, and `i18n.js` — **passed**; Node is optional and is not used to serve or deploy the dashboard.
- Locale validation — **382 matching keys** across English, Persian, and Arabic; all static translation references and placeholders match.
- Browser smoke checks — **passed** for dashboard summary, package score-history empty/single-record behavior, package comparison output, Persian RTL, and a 390px mobile viewport with no horizontal page overflow. The exercised flows had no application console errors or failed API responses.
- `python -m build --outdir <temporary-directory>` — **passed**; wheel and source distribution each contain all three locale files.
- Current native static assets (14 files): **194,572 bytes raw / 49,438 bytes gzip** (gzip level 9 applied per file). The retained pre-migration Vite measurement is **238,694 bytes raw / 67,449 bytes gzip**, making the current payload about **18.5% smaller raw and 26.7% smaller compressed** by these measurements.
- Docker/Compose validation was unavailable because the Docker CLI is not installed.

## Remaining work

1. Keep production deployments behind HTTPS and a trusted ingress. The built-in rate limiter is process-local; use shared gateway throttling for multiple workers or replicas.
2. Use a stronger identity integration than a shared API key before exposing the dashboard to multiple users.
3. Address the repository-wide Ruff findings in the untouched tests as a separate cleanup.
4. Add automated browser regression tests for the JavaScript UI; current interaction checks were performed in the integrated browser.
5. Validate Docker/Compose behavior in an environment with Docker installed.
6. Preserve the current release tag and Git history; do not commit or push without explicit approval.

## Detailed remediation notes

See [the engineering remediation report](docs/reviews/ENGINEERING_REMEDIATION_REPORT.md).
