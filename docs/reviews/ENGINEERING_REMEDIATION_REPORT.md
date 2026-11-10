# LibScope Engineering Remediation Report

## Executive summary

Remediation was performed on `engineering/remediation-v0.1.0`, based on `b8e1771025325e8ceb50d386e5b2e9ae0804ea11`. The worktree remains uncommitted. No release tag, published history, backup branch, or project database was intentionally changed.

The changes address verified reliability, security, and data-accuracy problems across the API, analysis pipeline, reports, CLI, dashboard, and packaging. The dashboard has since been migrated from React/TypeScript/Vite to native HTML, CSS, JavaScript, and browser APIs. The implementation continues to use the published `askai-python` package; it does not depend on or vendor the local `ask-ai/` directory.

## Remediation delivered

### API, persistence, and analysis

- Added production bearer-key enforcement for analysis, report generation, and demo seeding, plus process-local rate limiting. Comparison requests are rate-limited, and analytics/history reads are bounded.
- Added lifecycle handling for analysis timeout, cancellation, and unexpected failures. Job status receives sanitized errors rather than raw provider exceptions.
- Made release persistence an upsert by package/version and retained existing vulnerability findings when a fresh OSV lookup fails.
- Exposed bounded historical snapshot analysis and adoption-search status endpoints.
- Added production integration tests for protected routes, pagination, history, and status reporting.

### Evidence quality and scoring

- Adoption declarations are classified only after parsing supported manifest contents (`requirements*.txt/.in`, `pyproject.toml`, `setup.cfg`, Pipfile, and `package.json`). Missing, malformed, unsupported, or inaccessible content is not treated as a confirmed dependency.
- GitHub manifest fetches are bounded by path and size checks, decode validation, and explicit fetch status.
- Adoption discovery status now distinguishes a checked empty sample from unavailable, partial, failed, or non-applicable discovery.
- OSV responses have bounded retries, response-shape validation, explicit failure/partial/rate-limit states, and unknown-severity handling.
- Security scoring does not infer a clean posture from failed, unsupported, or otherwise incomplete checks.

### API, AI, and network controls

- Added provider-specific AI credential resolution, Azure endpoint requirements, production HTTPS enforcement for custom AI base URLs, and outbound URL validation.
- Added optional `ai` package extras for provider SDKs; documented provider installation and wired AI configuration through Docker Compose.
- Tightened request schemas, CORS behavior, and health/security status reporting.
- Added a browser Settings key prompt that keeps a trusted operator-provided key in tab memory only. It is not bundled or persisted. This is not a substitute for SSO or per-user authorization in multi-user deployments.

### Dashboard and reports

- Fixed comparison selection initialization after asynchronous package loading and the undefined score display.
- Prevented duplicate analysis submissions while queued/running and handled cancelled jobs.
- Added visible package-load error, retry, and navigation states; guarded against stale async package responses.
- HTML reports now escape dynamic content, only render safe HTTPS links, include health/security findings, and label incomplete checks.
- Markdown reports now handle missing values and do not render unchecked security as a clean result.

### Framework-free dashboard migration

- Replaced the React/TypeScript/Vite/Tailwind dashboard with semantic HTML, responsive CSS, modular vanilla JavaScript, Fetch API requests, and native SVG charts.
- Preserved overview/catalog search and demo loading; PyPI/GitHub analysis and job polling; multi-package comparison; adoption discovery and filtering; all eight package-detail sections; historical download chart and deltas; project health; security status; AI interpretation; HTML/Markdown/JSON report export; provider settings; and in-memory API-key handling.
- Added consistent handling for HTTP errors, network failures, timeouts, and invalid JSON, plus explicit loading, empty, retry, success, and error states.
- FastAPI now serves the dashboard at `/` and `/dashboard-assets/`. Assets are included in the Python wheel and source distribution; Docker no longer has a Node build stage.
- Removed all tracked React components, TypeScript sources, npm manifests/lockfile, and Vite/Tailwind/PostCSS/TypeScript configuration. End users and production deployments do not need Node.js or npm.
- Native line charts and score gauges use inline SVG; no charting or UI library was introduced.

### Distribution and dependencies

- Fixed explicit setuptools package mappings so CLI/API/core modules are included in built distributions.
- Removed tracked frontend npm dependency declarations/lockfile and build configuration; the dashboard now uses no third-party browser runtime or frontend build dependencies.
- Tests now use a disposable SQLite database and dispose the SQLAlchemy engine before cleanup.

## Validation results

| Check | Result |
|---|---|
| `python -m pytest -p no:cacheprovider -o addopts= tests` | Passed — 82 tests |
| Ruff on all modified Python files | Passed |
| `ruff check .` | Not clean — 10 existing findings in six untouched test modules; import ordering, UTC alias style, and one unused import |
| `node --check apps/api/libscope/api/dashboard_static/api.js` and `node --check apps/api/libscope/api/dashboard_static/app.js` | Passed; Node is optional for validation only |
| Integrated browser smoke test | Passed — overview, analysis and mocked job polling, comparison, adoption, all package tabs, report generation, API-key handling, and responsive width; no observed application console errors or failed API requests |
| Static asset/API integration test | Passed — FastAPI serves dashboard HTML, JavaScript modules, CSS, and SVG favicon |
| `python -m build --no-isolation --wheel --sdist` | Passed — wheel and source distribution produced |
| Package contents | Passed — both wheel and source distribution include all dashboard assets |
| `python -m libscope.cli.main --help` | Passed — CLI entry point starts without the earlier module warning |
| Docker Compose validation | Not run — Docker CLI unavailable |

No live AI provider calls were made. There is no committed automated browser-test runner; browser interactions were validated manually with the integrated Playwright browser.

### Frontend payload comparison

| Version | Files | Raw bytes | Gzip bytes |
|---|---:|---:|---:|
| Previous Vite build (`apps/dashboard/dist`) | 3 | 238,694 | 67,449 |
| Native static dashboard | 5 | 77,401 | 19,935 |

Gzip sizes are summed after compressing each static file separately. The native assets are approximately 68% smaller raw and 70% smaller gzip. The old generated `dist` and installed `node_modules` directories were ignored local artifacts and were left untouched; neither is referenced by the application, package, or Docker build.

## Remaining risks and follow-up

1. **Multi-user authentication:** The configured API key is shared. The dashboard memory-only input is suitable only for trusted operators. Add SSO or enforce identity at a trusted gateway before multi-user exposure.
2. **Distributed rate limiting:** The limiter is in-process and does not coordinate across workers/replicas. Use gateway or shared-store throttling when scaling horizontally.
3. **TLS termination:** Production must use HTTPS through a trusted reverse proxy before transmitting bearer credentials.
4. **Repository-wide lint:** Ten Ruff findings remain in untouched tests; they were not changed as unrelated cleanup.
5. **Dashboard test coverage:** Add a committed browser automation suite for selection, API-key headers, and loading/error states; current browser checks were integrated/manual.
6. **Container validation:** Run Compose configuration and image build in an environment with Docker installed.
7. **Historical depth:** The history endpoint returns bounded snapshots and the current analyzer's recent delta; richer score/adoption/vulnerability time-series analysis remains future work.

## Git safety

- Branch: `engineering/remediation-v0.1.0`
- Base/HEAD: `b8e1771025325e8ceb50d386e5b2e9ae0804ea11`
- Tag `v0.1.0` and branch `backup/pre-rebuild` were left unchanged.
- No commit or push was created.

