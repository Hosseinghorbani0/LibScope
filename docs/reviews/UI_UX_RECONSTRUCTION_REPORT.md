# LibScope UI/UX Reconstruction Report

## Mission baseline

- Audited branch: `engineering/remediation-v0.1.0`
- Audited base: `b8e1771025325e8ceb50d386e5b2e9ae0804ea11`
- `origin/main`, `main`, `v0.1.0`, and the remediation branch point at the same base commit. The current worktree already contains extensive, unrelated-to-this-mission uncommitted remediation and native-dashboard changes. Those changes are preserved; no history operation was performed.
- Runtime: FastAPI served the dashboard from `/` and `/dashboard-assets/`; the real-browser audit used an isolated temporary SQLite database seeded with the existing demo dataset.
- Existing architecture documents: `PROJECT_STATE.md`, `docs/reviews/ENGINEERING_REMEDIATION_REPORT.md`, and `docs/design/LIBSCOPE_DASHBOARD_DESIGN_SPEC.md`.

## Existing frontend and API map

| Workflow | Dashboard surface | API contract |
|---|---|---|
| Portfolio summary and activity | Overview in `apps/api/libscope/api/dashboard_static/app.js` | `GET /api/v1/dashboard/summary`, `GET /api/v1/packages` |
| Package search and detail | Catalog and eight detail tabs | `GET /api/v1/packages`, `GET /api/v1/packages/{id}` |
| Package analysis and polling | Analyze form and job panel | `POST /api/v1/analyze`, `GET /api/v1/jobs/{id}` |
| Adoption | Global discovery and package evidence | `GET /api/v1/packages/{id}/adoption` and `/adoption/status` |
| Comparison | Multi-package selection and matrix | `POST /api/v1/compare` |
| Usage and score history | Native SVG charts and recorded deltas | `GET /api/v1/packages/{id}/history`, `/analytics`, `/score-history` |
| Repository, health, security, and releases | Package detail tabs | `GET /api/v1/packages/{id}/health`, `/security`, `/security/status`, and `/releases` |
| AI interpretation | Package detail tab | Package detail response's `latest_ai_analysis` |
| Reports | HTML, Markdown, and JSON export | `POST /api/v1/reports/generate`, then `GET /api/v1/reports/{id}` for HTML |
| Settings and authentication | Provider status and memory-only API key | `GET /api/v1/version`; bearer header on protected write operations |
| Demo data | Sidebar action and empty-catalog action | `POST /api/v1/demo/seed` |

The static application is native HTML/CSS/ES modules. `api.js` owns Fetch and the in-memory API key, `i18n.js` loads locale dictionaries, and `app.js` currently combines application state, all screen rendering, and event handling. The package and report APIs are served by the same FastAPI application. The analysis endpoint accepts canonical package/repository identifiers, not URLs; no identity-search or candidate-resolution endpoint exists.

## Baseline browser and contract findings

The application loaded and the overview, all five primary destinations, and all eight package tabs were reachable in the real browser. The demo catalog contained three seeded packages. No page-level JavaScript exception was observed during this baseline pass. Testing an API-protected operation without entering the local test key produced an expected `401`.

Measured viewport widths: 320, 360, 375, 390, 430, 768, 1024, 1440, and 1600 CSS pixels. The document did not exceed the viewport width in the sampled overview/analyze states. However, the mobile primary-nav content is 655px wide and depends on a horizontal scroll region; the chart CSS has a 440px minimum width inside a clipped wrapper, which can hide chart content. The demo controls are hidden on mobile.

| Priority | Finding and evidence | Consequence |
|---|---|---|
| P0 | The analysis input at `app.js` lines 319–341 has a restrictive identifier-only `pattern`. In-browser, `https://pypi.org/project/requests/` failed `checkValidity()` with “Please match the requested format.” No URL parsing or canonicalization occurs before `POST /api/v1/analyze`. | Required direct PyPI and GitHub URLs cannot be submitted; browser-generated validation is not localized or actionable. |
| P0 | Many rendered labels remain English literals in `app.js` (for example catalog, analysis, comparison, report, settings, health, security, and repository views). `i18n.js` lines 83–89 silently falls back to English or the raw key, while lines 101–120 attempt to translate by matching rendered text nodes to English dictionary values. | Localization is incomplete and fragile; dynamic content, compound text nodes, attributes, and newly added screens can bypass the heuristic. Missing keys are not surfaced as errors. |
| P0 | `main.py` lines 250–257 maps a missing metrics snapshot to `total_downloads_30d=0`; `main.py` lines 481–485 similarly maps absent snapshots/repositories to numeric zero in comparisons. The response schema requires numeric values (`schemas.py` lines 156 and 232). | The UI cannot distinguish “no observation” from a verified zero and can present fabricated certainty. |
| P1 | The root renderer in `app.js` combines all views, state transitions, transport orchestration, event handlers, and localization; e.g. render functions span lines 176–790 and data/event logic spans lines 803–1188. | Changes to one screen risk unrelated workflows; the one-file structure impedes regression coverage and maintainability. |
| P1 | Comparison choices and requests use package names (`app.js` lines 718–735 and 1011–1024), while the API can compare package IDs (`schemas.py` lines 221–224). | Same-name packages across ecosystems can be conflated or returned as the wrong comparison set. |
| P1 | At `styles.css` lines 257–258 charts have a 440px minimum width while `.chart-wrap` clips overflow; at lines 316–324 the mobile nav is a horizontally scrolling strip and the sidebar footer is hidden. | Chart content and demo actions are difficult or impossible to reach on small screens; mobile navigation discoverability is weak. |
| P1 | Detail loading uses a single `Promise.all` for package, score history, downloads, adoption, health, security, and releases (`app.js` around lines 901–935). Any one ancillary endpoint failure rejects the entire detail page. | Partial outages hide otherwise usable package intelligence instead of identifying the unavailable section. |
| P1 | `api.js` returns raw backend `detail` strings for HTTP errors rather than mapping known statuses into localized UI messages. | Authentication, rate-limit, and service errors can appear in English and lack recovery guidance. |
| P2 | Package catalog loading requests only the first 100 records (`api.js` around line 56), even though the backend supports offset pagination. | Larger catalogs cannot be searched or inspected completely. |
| P2 | Detail evidence includes literal English labels and raw internal status/classification strings (e.g. adoption evidence types and some health/security labels in `app.js`). | A page may have a translated heading while its evidence table remains partially untranslated. |
| P2 | The current tab role sets roving `tabindex`, but no arrow-key tab navigation handler is present (`app.js` around lines 379–387 and 1070–1188). | The detail tablist does not implement expected keyboard interaction. |
| P2 | Routes are held only in JavaScript state; `navigate()` does not update the URL and startup ignores a route fragment (`app.js` around lines 825–835 and 1167–1188). | Refresh and browser back/forward do not restore the selected page or package. |

The three locale dictionaries currently contain 382 matching keys and have matching placeholders. Key parity alone does not establish UI coverage: static English strings are only translated when their entire text node exactly matches a dictionary value. Persian and English remain the priority locales; the existing Arabic dictionary will be retained and kept structurally in sync where practical.

## Prioritized implementation plan

### P0 — Acceptance blockers

1. Replace text-node translation heuristics with explicit, centralized translation keys for all static interface strings, form validation, statuses, error states, chart descriptions, and accessibility labels. Add a development/test check that fails for missing keys/placeholders; retain API-sourced names, identifiers, and evidence text as source content with bidi isolation.
2. Add a pure input parser/normalizer for package names, PyPI project URLs, GitHub repository URLs, and `owner/repository` identifiers. Validate exact allowed hosts and URL structure, select the matching ecosystem deterministically, give localized feedback, preserve the entered value on errors, and submit only the canonical identifier accepted by the existing API. Do not invent candidate search or ambiguity resolution; document that capability as requiring a backend API if needed.
3. Make unavailable metrics nullable through the existing API response contracts where their absence is currently coerced to zero. Update score/download/comparison rendering and tests so unknown, not checked, and verified zero remain distinct.

### P1 — Product reliability and usability

4. Establish and apply a compact design system: light/dark semantic tokens, typography/spacing/radius/elevation scales, consistent controls and status semantics, visible focus, contrast-aware colors, and reduced-motion behavior.
5. Rebuild the responsive application shell and navigation for keyboard/touch use; provide mobile access to all navigation and demo actions. Make tables and charts operable without clipping on 320px screens.
6. Split renderers, input parsing, and route/state handling into focused native ES modules. Use package IDs for comparisons and add URL-backed navigation with refresh/back/forward restoration.
7. Isolate independent package-detail requests so a failed ancillary endpoint yields a localized partial/unavailable section, not a failed whole page. Localize known API status errors and provide clear retry guidance.
8. Add complete catalog pagination using the backend's existing `limit`/`offset` parameters.

### P2 — Verification and polish

9. Exercise every navigation route, detail tab, form, report format, authentication path, locale, theme, chart, and supported input class in the browser; record console and failed-request results.
10. Add automated regression checks for URL normalization, locale key/placeholder coverage, API payload identity, and critical UI flows where the existing test environment supports them without adding end-user frontend dependencies.
11. Update `PROJECT_STATE.md`, user/deployment documentation, and this report with final behavior, accepted limitations, and measured validation. Keep the worktree uncommitted and preserve all pre-existing changes.

## Acceptance limitations identified before implementation

- URL parsing can reliably recognize the supported PyPI/GitHub URL forms and canonical identifiers locally. Searching registries for an arbitrary human-entered name or resolving multiple candidates is not supported by the existing API and will not be simulated.
- The current persistence model does not provide complete historical health, security, or adoption series. The interface must state those limits rather than draw synthetic trends.
- Browser automation packages are not declared in the project. Prefer dependency-free parser/contract tests and integrated-browser verification unless an existing installed browser test runner is found.

## Final implementation and validation log

Pending implementation and post-change validation.

