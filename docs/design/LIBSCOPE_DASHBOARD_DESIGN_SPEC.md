# LibScope Dashboard Design Specification

## Status

Approved implementation baseline for the dashboard redesign. The specification preserves the existing uncommitted work and defines data-trust constraints before any product changes. It does not authorize a database schema migration; if one becomes necessary, its compatibility plan must be reviewed separately.

## Product intent

LibScope is an open-source software intelligence platform: **Beyond Downloads.** The dashboard should help developers assess adoption, security, maintenance, package health, and evidence quality without overstating what the collected data proves.

The interface will remain a framework-free, same-origin application served by FastAPI. It will use semantic HTML, modular JavaScript, CSS, browser APIs, native Fetch, and lightweight SVG. End users will not need Node.js or a frontend installation.

### Product principles

1. Evidence before decoration: show source, measurement period, freshness, coverage, and caveats alongside important metrics.
2. Missing is not zero: distinguish unavailable, not checked, partial, failed, stale, and verified-empty results.
3. Explain scores: expose the dimension, score, confidence, weight, inputs, and methodology where available.
4. Preserve established workflows: analysis, polling, comparison, adoption discovery, package detail, reports, settings, API-key handling, and demo data remain available.
5. Progressive disclosure: make the executive summary scannable while preserving access to evidence and methodology.
6. Accessible by default: keyboard-operable controls, visible focus, contrast, reduced motion, meaningful headings, and text alternatives for charts.
7. Internationalization is architectural: translated labels are keyed data, not conditional strings scattered through UI logic.
8. No unsupported history: a current finding or current score must not be presented as a time series.

## Information architecture

### Global shell

- Original LibScope symbol and wordmark.
- Primary destinations: Overview, Package catalog, Analyze, Adoption, Compare.
- Persistent language and theme controls in the application header.
- Breadcrumbs and package context on detail screens.
- Responsive navigation that remains keyboard accessible at mobile widths.
- Service/database freshness and collection status only when the backend can provide a meaningful timestamp and status.

### Overview

1. **Portfolio summary:** exact package/repository totals and clearly defined coverage counts.
2. **Attention queue:** packages with confirmed security findings, failed/incomplete checks, or latest health checks requiring attention; each item links to its evidence.
3. **Recent analysis activity:** recent persisted jobs, with terminal status and timestamps.
4. **Package portfolio:** searchable, filterable, sortable, paginated catalog with score, confidence, ecosystem, latest version, and freshness where known.
5. **Portfolio distributions and trends:** only computed from actual records and accompanied by denominators, definitions, and an unavailable state when coverage is insufficient.

Do not use hard-coded provider counts or model labels as measured portfolio statistics. A displayed total must not be derived from the first page of a paginated catalog.

### Package intelligence

The package detail experience opens with an executive summary containing identity, repository links, score and confidence, score coverage, key verified findings, and last collection timestamps. Sections are:

1. Overview and score methodology.
2. Adoption evidence.
3. Security findings and scan status.
4. Health and maintenance checks.
5. Usage and historical snapshots.
6. Repository activity and release history.
7. Optional AI interpretation, explicitly separated from deterministic evidence.
8. HTML, Markdown, and JSON report exports.

Each section must distinguish observed evidence from inference. A score dimension with no evidence remains unavailable, not zero.

### Other workflows

- **Analyze:** preserve PyPI/GitHub selection, optional AI interpretation, job progress, errors, retries, and direct navigation to completed package intelligence.
- **Adoption:** filter by evidence type and package; expose repository, manifest, raw match where safe, confidence, discovery time, status, and caveats. Possible usage and documentation mentions are never labeled confirmed dependencies.
- **Security:** show status and check time before findings; group verified findings by severity and include identifiers, affected/fixed versions, source, and references. Incomplete or failed checks cannot be called clean.
- **Compare:** retain 2–10 package selection, side-by-side measurements, confidence, comparability notes, and explicit unavailable values. Use visual comparisons only for metrics with comparable definitions and coverage.
- **Reports:** preserve HTML, Markdown, and JSON; include provenance, coverage, limitations, score explanation, and the matching brand. Provide localized labels for supported locales.
- **Settings:** preserve memory-only bearer-key behavior and provider information; add language and theme preferences. Never persist the API key.

## Data contracts and provenance

| Information | Existing source | Current limitation | Redesign behavior |
|---|---|---|---|
| Package identity and current metadata | Package detail/list API | List is paginated, with a maximum of 100 per request | Add a bounded aggregate response for exact portfolio counts; paginate the catalog |
| Repository signals | Repository model/detail API | Missing repository values are not equivalent to zero | Show source and unknown values distinctly |
| Score and dimensions | Score records and scoring engine | Score rows are historical, but no score-series endpoint is exposed | Expose stored score history and render only recorded points |
| Score methodology | Scoring engine weights and dimension breakdown | UI shows dimensions but not a full methodology/data-coverage explanation | Present actual weights, inputs, explanations, confidence, and model version |
| Download usage | Metric snapshots/history API | Snapshots are collected during analyses; they are not guaranteed daily observations | Label period and collection dates; do not imply continuous coverage |
| Releases | Release API/model | Dashboard does not currently request release records | Render stored release dates and yanked state; do not invent release-frequency data |
| Adoption | Evidence records plus latest search status/caveats | Records are inserted on first discovery; absence from later scans is not persisted | Show evidence and first-discovered timestamps; do not infer adoption churn or a complete dependency graph |
| Security | Current findings and latest snapshot status/caveats | Successful scans replace findings; failed scans retain older findings | Treat findings as current only with a confirming latest status; label retained findings stale/unconfirmed after a failed scan |
| Health | Findings replaced by the latest analysis | No separate health-history series | Summarize the latest finding set and status; do not show historical health trends |
| Analysis activity | Persisted analysis jobs | No dashboard activity/summary endpoint | Expose a bounded recent-job view from existing rows |
| Comparison | Compare API and stored package/repository/score records | Last-release and last-commit ages are currently emitted as unknown | Populate ages from recorded timestamps; preserve comparability notes |
| AI interpretation | Latest stored AI analysis | Optional and generated from collected evidence | Label provider/model/time and keep distinct from deterministic scoring |

### Minimal backend additions

The first backend iteration should avoid schema changes:

- Add a bounded dashboard summary endpoint using aggregates over existing package, score, finding, snapshot, and job rows.
- Derive the latest health status from the latest persisted health finding set; return explicit coverage and unknown counts.
- Derive security distribution only for packages whose latest check is confirmed; expose partial/failed/not-checked counts separately.
- Include a bounded recent-job list and a freshness timestamp.
- Extend package history with stored score points, reusing existing `Score` rows.
- Correct comparison release/commit ages from existing repository timestamps.
- Use the existing releases route from the dashboard.

Security scan history, health history, adoption removals, and historical dependency graphs are not currently reliable persisted series. They remain explicitly unavailable. If product requirements later justify storing them, propose an additive schema change and a migration/backfill strategy before implementation. `Base.metadata.create_all()` does not migrate existing tables.

## Visual identity

Create an original SVG identity based on a precise package/dependency graph viewed through an analytical aperture. The symbol must work independently at small sizes; the lockup combines it with the LibScope wordmark and “Beyond Downloads.” Avoid generic magnifying-glass-only or copied company marks.

Deliver:

- Primary horizontal lockup for light backgrounds.
- Inverse lockup for dark backgrounds.
- Single-color mark/lockup.
- Compact app icon.
- SVG favicon.

Use the same assets in the dashboard and HTML report. Document asset variants and usage for contributors.

## Visual system and interaction

- Establish semantic color tokens for light and dark themes, surfaces, borders, text, focus, and status.
- Keep severity/status meaning consistent and do not rely on color alone.
- Use restrained typography, compact but readable information density, consistent spacing, and clear table/chart hierarchy.
- Use CSS logical properties and direction-aware layouts; isolate technical identifiers and URLs with `bdi` or explicit LTR direction in RTL pages.
- Persist locale/theme preferences only. Default to English and respect system color preference until a user selects a theme.
- Prefer native SVG for charts. Every chart includes units, period, labeled axes, a textual summary, and an empty/incomplete state.
- Avoid decorative-only charts, click-like non-controls, and unnecessary motion.

## Internationalization

- Locale dictionaries live in separate structured files (`en`, `fa`, `ar`) with stable keys and English fallback.
- All user-facing content, including navigation, validation, error/loading/empty states, tables, dialogs, tooltips, and reports, goes through the translation layer.
- Set document `lang` and `dir` for the selected locale: English LTR; Persian and Arabic RTL.
- Use `Intl.NumberFormat` and `Intl.DateTimeFormat` with the active locale.
- Keep package names, code, identifiers, and URLs readable using direction isolation.
- Verify Persian typography and alignment in actual browser output; translating strings without RTL layout is insufficient.

## Technical architecture

- FastAPI continues to serve the dashboard and static assets from the Python distribution.
- Keep API transport, localization, state, rendering, and event delegation in small native JavaScript modules.
- Use same-origin API requests and preserve the API key in module memory only.
- Avoid new frontend runtime dependencies and mandatory build tools.
- Any new static files must be included in both wheel and source distribution.

## Delivery order and acceptance gates

1. **Specification:** inventory current capabilities, data provenance, constraints, and testable acceptance criteria. Gate: no unsupported metric is planned as available.
2. **Brand:** SVG variants and integration. Gate: readable at favicon/app-icon size and valid in reports.
3. **Design system:** responsive tokens, light/dark controls, accessible primitives, logical layout. Gate: keyboard/focus, reduced motion, and viewport checks.
4. **English redesign:** all existing workflows and richer overview/package views. Gate: every legacy interaction remains reachable and error/empty states are explicit.
5. **Persian:** complete translation and RTL/bidi pass. Gate: no untranslated visible strings and no direction/layout regressions.
6. **Arabic:** same architecture, RTL behavior, and translation coverage. Gate: no untranslated visible strings.
7. **Data improvements:** implement only justified additive API behavior based on existing records; disclose unpersisted history rather than fabricating it. Gate: API tests verify counts, coverage, statuses, and response bounds.
8. **Quality and documentation:** browser workflows, accessibility, locales, themes, packaging, payload-size comparison, API/report docs, and project-state updates. Gate: all feasible automated checks pass; unavailable infrastructure is explicitly reported.

## Definition of done

- Existing dashboard capabilities are preserved.
- The product has a coherent LibScope identity and light/dark themes.
- English, Persian RTL, and Arabic RTL work across all visible dashboard states.
- Overview and intelligence screens expose trustworthy, explainable information with provenance and clear data gaps.
- Charts use real data and have accessible textual equivalents.
- No React, Vite, TypeScript, charting framework, or frontend runtime dependency is introduced.
- FastAPI-served assets are present in wheel and sdist; no frontend install is required for end users.
- Critical workflows, error states, keyboard access, responsive layouts, and package distributions are tested.
- No commit, push, release, or Git-history rewrite occurs without explicit authorization.
