import { api } from "./api.js";
import { getLocale, initializeI18n, setLocale, t } from "./i18n.js";
import { parseAnalysisInput } from "./analysis-input.js";
import { readRoute, watchRoute, writeRoute } from "./routes.js";
import {
  escapeHtml,
  formatDate,
  formatNumber as number,
  evidenceTypeLabel,
  localizeComparisonNote,
  safeExternalLink,
  scoreGauge,
  statusBadge,
  statusLabel,
} from "./presentation.js";

const app = document.querySelector("#app");
const THEME_STORAGE_KEY = "libscope.theme";
const navItems = [
  ["overview", "nav.overview"],
  ["analyze", "nav.analyze"],
  ["adoption", "nav.adoption"],
  ["compare", "nav.compare"],
  ["settings", "nav.settings"],
];
const detailTabs = [
  ["overview", "tabs.score"],
  ["adoption", "tabs.adoption"],
  ["downloads", "tabs.usage"],
  ["repository", "tabs.repository"],
  ["health", "tabs.health"],
  ["security", "tabs.security"],
  ["ai", "tabs.ai"],
  ["report", "tabs.reports"],
];

function getInitialTheme() {
  try {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
  } catch (error) {
    console.warn("Unable to read the saved theme preference.", error);
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const SCORE_WEIGHTS_V1 = {
  adoption_score: 0.25,
  maintenance_score: 0.20,
  security_score: 0.15,
  documentation_score: 0.15,
  quality_score: 0.10,
  popularity_score: 0.08,
  growth_score: 0.07,
};

const state = {
  view: "overview",
  theme: getInitialTheme(),
  packages: [],
  packagesLoading: true,
  packagesError: "",
  dashboardSummary: null,
  summaryLoading: true,
  summaryError: "",
  summaryRequest: 0,
  search: "",
  packageId: null,
  detailTab: "overview",
  detail: null,
  detailLoading: false,
  detailError: "",
  detailSectionErrors: [],
  detailRequest: 0,
  adoptionPackageId: "",
  adoptionItems: [],
  adoptionStatus: null,
  adoptionLoadedFor: "",
  adoptionFilter: "all",
  adoptionLoading: false,
  adoptionError: "",
  adoptionRequest: 0,
  compareIds: [],
  comparison: null,
  comparisonLoading: false,
  comparisonError: "",
  analysisJob: null,
  analysisError: "",
  analysisSubmitting: false,
  analysisName: "",
  analysisEcosystem: "pypi",
  analysisEnableAi: false,
  analysisValidation: "",
  analysisInputSource: "",
  jobTimer: null,
  seedLoading: false,
  seedError: "",
  settingsLoading: true,
  settingsError: "",
  versionInfo: null,
  apiKeyMessage: "",
  reportLoading: false,
  reportError: "",
  reportMessage: "",
  localeError: "",
  mobileNavOpen: false,
};

function applyTheme(theme) {
  state.theme = theme;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  const themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor) themeColor.content = theme === "dark" ? "#090d16" : "#f4f7f8";
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (error) {
    console.warn("Unable to save the theme preference.", error);
  }
}

applyTheme(state.theme);

function renderShell() {
  const activeView = state.view === "package-detail" ? "overview" : state.view;
  const nav = navItems.map(([id, key]) => {
    const label = t(key);
    return `
    <button class="nav-item ${activeView === id ? "active" : ""}" type="button" data-action="navigate" data-view="${id}" ${activeView === id ? 'aria-current="page"' : ""}>
      <span class="nav-mark" aria-hidden="true">${escapeHtml(label.charAt(0))}</span><span>${escapeHtml(label)}</span>
    </button>`;
  }).join("");
  const themeAction = state.theme === "dark" ? "light" : "dark";
  const themeLabel = state.theme === "dark" ? t("theme.switchToLight") : t("theme.switchToDark");
  const themeIcon = themeAction === "light"
    ? `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"></path></svg>`
    : `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.2 15.1A8.5 8.5 0 0 1 8.9 3.8 8.5 8.5 0 1 0 20.2 15.1Z"></path></svg>`;
  const toolbarLabel = state.view === "package-detail"
    ? state.detail?.package?.name || t("common.packageIntelligence")
    : t(navItems.find(([id]) => id === state.view)?.[1] || "common.softwareIntelligence");
  app.innerHTML = `<div class="shell">
    <aside class="sidebar ${state.mobileNavOpen ? "nav-open" : ""}">
      <a class="brand" href="#/overview" aria-label="${t("brand.home")}" data-action="navigate" data-view="overview">
        <img class="brand-logo" src="/dashboard-assets/logo-${state.theme}.svg" alt="${escapeHtml(t("brand.tagline"))}">
      </a>
      <button class="mobile-nav-toggle" type="button" data-action="toggle-nav" aria-controls="primary-nav" aria-expanded="${state.mobileNavOpen}">
        <span aria-hidden="true">☰</span><span>${t("navigation.menu")}</span>
      </button>
      <nav id="primary-nav" class="primary-nav ${state.mobileNavOpen ? "is-open" : ""}" aria-label="${t("common.mainNavigation")}">${nav}</nav>
      <div class="sidebar-footer">
        <div class="demo-card">
          <div class="demo-title"><strong>${t("common.demoDataset")}</strong><span>${t("common.offlineReady")}</span></div>
          <p>${t("common.loadSamplesDescription")}</p>
          <button type="button" class="button secondary full" data-action="seed" ${state.seedLoading ? "disabled" : ""}>
            ${state.seedLoading ? t("common.loadingSamples") : t("common.loadSampleData")}
          </button>
        </div>
        <p class="version-note">LibScope v0.1.0 · Apache-2.0</p>
      </div>
    </aside>
    <main id="main-content" class="main-content">
      <header class="app-toolbar">
        <div class="toolbar-context"><span class="eyebrow">${escapeHtml(toolbarLabel)}</span></div>
        <div class="toolbar-controls">
        <label class="language-control"><span class="sr-only">${t("language.label")}</span><select id="language-select" aria-label="${t("language.label")}">
          <option value="en" ${getLocale() === "en" ? "selected" : ""}>${t("language.english")}</option>
          <option value="fa" ${getLocale() === "fa" ? "selected" : ""}>${t("language.persian")}</option>
          <option value="ar" ${getLocale() === "ar" ? "selected" : ""}>${t("language.arabic")}</option>
        </select></label>
        <button class="theme-toggle" type="button" data-action="toggle-theme" aria-label="${escapeHtml(themeLabel)}" title="${escapeHtml(themeLabel)}">
          ${themeIcon}<span class="sr-only">${themeLabel}</span>
        </button>
        </div>
      </header>
      ${state.seedError ? `<div class="notice error" role="alert">${escapeHtml(state.seedError)}</div>` : ""}
      ${state.localeError ? `<div class="notice error" role="alert">${escapeHtml(state.localeError)}</div>` : ""}
      <div id="page-view">${renderPage()}</div>
    </main>
  </div>`;
}

function renderPage() {
  switch (state.view) {
    case "analyze": return renderAnalyze();
    case "package-detail": return renderPackageDetail();
    case "adoption": return renderAdoption();
    case "compare": return renderCompare();
    case "settings": return renderSettings();
    default: return renderOverview();
  }
}

function renderOverview() {
  const packageCards = state.packagesLoading
    ? `<div class="empty-state" role="status">${t("catalog.loading")}</div>`
    : state.packagesError
      ? `<div class="empty-state"><p class="notice error" role="alert">${escapeHtml(state.packagesError)}</p><button class="button primary" data-action="reload-packages">${t("common.retry")}</button></div>`
      : renderPackageCards();
  return `<section class="page-section">
    <header class="page-heading-row">
      <div>${pageHeader(t("overview.title"), t("overview.description"))}</div>
      <div class="hero-actions">
        <button class="button primary" type="button" data-action="navigate" data-view="analyze">${t("overview.newAnalysis")}</button>
        ${state.packages.length === 0 ? `<button class="button secondary" type="button" data-action="seed" ${state.seedLoading ? "disabled" : ""}>${state.seedLoading ? t("common.loadingSamples") : t("overview.loadDemo")}</button>` : ""}
      </div>
    </header>
    ${renderDashboardSummary()}
    <section class="section-block">
      <div class="section-heading">
        <div><h2>${t("catalog.title")}</h2><p>${t("catalog.description")}</p></div>
        <label class="search-control"><span class="sr-only">${t("catalog.filterLabel")}</span><input id="package-search" type="search" placeholder="${escapeHtml(t("catalog.filterPlaceholder"))}" value="${escapeHtml(state.search)}"></label>
      </div>
      <div id="package-list">${packageCards}</div>
    </section>
  </section>`;
}

function renderDashboardSummary() {
  if (state.summaryLoading) return `<div class="empty-state" role="status">${t("summary.loading")}</div>`;
  if (state.summaryError) {
    return `<div class="notice error" role="alert">${escapeHtml(state.summaryError)} <button class="button secondary" type="button" data-action="reload-summary">${t("common.retry")}</button></div>`;
  }
  const summary = state.dashboardSummary;
  if (!summary) return "";
  const jobs = summary.recent_jobs || [];
  return `<section class="section-block" aria-labelledby="portfolio-summary-title">
    <h2 id="portfolio-summary-title" class="sr-only">${t("summary.title")}</h2>
    <div class="stat-grid four">
      <article class="stat-card"><span>${t("summary.packages")}</span><strong>${number(summary.total_packages)}</strong></article>
      <article class="stat-card"><span>${t("summary.scored")}</span><strong>${number(summary.scored_packages)}</strong></article>
      <article class="stat-card"><span>${t("summary.repositories")}</span><strong>${number(summary.linked_repositories)}</strong></article>
      <article class="stat-card"><span>${t("summary.updated")}</span><strong class="compact">${escapeHtml(summary.latest_package_update ? formatDate(summary.latest_package_update) : t("common.notRecorded"))}</strong></article>
    </div>
    <article class="panel activity-panel">
      <div class="section-heading"><div><h2>${t("summary.recentActivity")}</h2><p>${t("summary.activityDescription")}</p></div></div>
      ${jobs.length ? `<ol class="activity-list">${jobs.map((job) => `<li>
        <div class="activity-copy"><strong>${job.package_id ? `<button class="text-button" type="button" data-action="open-package" data-id="${Number(job.package_id)}"><bdi>${escapeHtml(job.package_name)}</bdi></button>` : `<bdi>${escapeHtml(job.package_name)}</bdi>`}</strong>
        <small>${escapeHtml(job.ecosystem)} · ${escapeHtml(formatDate(job.created_at))}</small></div>
        ${statusBadge(job.status)}
      </li>`).join("")}</ol>` : `<p class="empty-inline">${t("summary.noActivity")}</p>`}
    </article>
  </section>`;
}

function renderPackageCards() {
  const query = state.search.trim().toLowerCase();
  const filtered = state.packages.filter((pkg) =>
    `${pkg.name} ${pkg.description || ""}`.toLowerCase().includes(query));
  if (!filtered.length) {
    const message = state.packages.length ? t("catalog.noMatch") : t("catalog.empty");
    return `<div class="empty-state"><h3>${t("catalog.noPackages")}</h3><p>${message}</p>
      <button class="button primary" data-action="navigate" data-view="analyze">${t("common.analyzePackage")}</button>
      ${state.packages.length ? "" : `<button class="button secondary" data-action="seed" ${state.seedLoading ? "disabled" : ""}>${t("overview.loadDemo")}</button>`}
    </div>`;
  }
  return `<div class="table-wrap catalog-wrap"><table class="catalog-table">
    <thead><tr><th scope="col">${t("catalog.package")}</th><th scope="col">${t("catalog.ecosystem")}</th><th scope="col">${t("catalog.version")}</th><th scope="col">${t("catalog.license")}</th><th scope="col">${t("catalog.updated")}</th><th scope="col"><span class="sr-only">${t("catalog.details")}</span></th></tr></thead>
    <tbody>${filtered.map((pkg) => `<tr>
      <td><strong class="package-name"><bdi>${escapeHtml(pkg.name)}</bdi></strong><small class="catalog-description">${escapeHtml(pkg.description || t("catalog.noDescription"))}</small></td>
      <td>${statusBadge(pkg.ecosystem)}</td>
      <td><code dir="ltr">${escapeHtml(pkg.latest_version || t("common.unknown"))}</code></td>
      <td>${escapeHtml(pkg.license || t("common.notRecorded"))}</td>
      <td><time datetime="${escapeHtml(pkg.updated_at || "")}">${escapeHtml(formatDate(pkg.updated_at, { dateStyle: "medium" }))}</time></td>
      <td><button class="button secondary compact-button" type="button" data-action="open-package" data-id="${Number(pkg.id)}">${t("catalog.inspect")}</button></td>
    </tr>`).join("")}</tbody>
  </table></div>`;
}

function renderAnalyze() {
  const job = state.analysisJob;
  const active = job && ["queued", "running"].includes(job.status);
  const done = job && job.status === "completed";
  return `<section class="page-section narrow">
    ${pageHeader(t("analysis.title"), t("analysis.description"))}
    <form id="analysis-form" class="panel form-panel">
      <label class="field-label" for="analysis-name">${t("analysis.packageLabel")}</label>
      <input id="analysis-name" name="packageName" maxlength="255" value="${escapeHtml(state.analysisName)}" placeholder="${escapeHtml(t("analysis.packagePlaceholder"))}" autocomplete="url" aria-describedby="analysis-help analysis-feedback" aria-invalid="${Boolean(state.analysisValidation)}">
      <p id="analysis-help" class="field-help">${t("analysis.packageHelp")}</p>
      <p id="analysis-feedback" class="field-help" role="status" aria-live="polite">${state.analysisValidation ? escapeHtml(t(state.analysisValidation)) : t("analysis.inputExamples")}</p>
      <div class="form-row">
        <label class="field-label">${t("analysis.ecosystem")}
          <select name="ecosystem" aria-label="${t("analysis.ecosystem")}"><option value="pypi" ${state.analysisEcosystem === "pypi" ? "selected" : ""}>${t("analysis.pypi")}</option><option value="github" ${state.analysisEcosystem === "github" ? "selected" : ""}>${t("analysis.github")}</option></select>
        </label>
        <label class="ai-option"><input name="enableAi" type="checkbox" ${state.analysisEnableAi ? "checked" : ""}><span><strong>${t("analysis.aiOption")}</strong><small>${t("analysis.aiHelp")}</small></span></label>
      </div>
      <button class="button primary full" type="submit" ${state.analysisSubmitting || active ? "disabled" : ""}>
        ${state.analysisSubmitting ? t("analysis.starting") : active ? t("analysis.inProgress") : t("analysis.submit")}
      </button>
      ${state.analysisError ? `<p class="notice error" role="alert">${escapeHtml(state.analysisError)}</p>` : ""}
    </form>
    ${job ? renderJob(job, done) : ""}
  </section>`;
}

function renderJob(job, done) {
  const status = job.status === "completed" ? "good" : ["failed", "cancelled"].includes(job.status) ? "bad" : "info";
  const progress = Math.max(0, Math.min(100, Number(job.progress) || 0));
  return `<section class="panel job-panel" aria-live="polite">
    <div class="row-between"><div><span class="eyebrow">${escapeHtml(t("analysis.job", { id: String(job.id).slice(0, 8) }))}</span><h2>${escapeHtml(t("analysis.analyzing", { package: job.package_name, ecosystem: job.ecosystem }))}</h2></div>${statusBadge(job.status)}</div>
    <div class="progress-track" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"><span class="${status}" style="width:${progress}%"></span></div>
    <p class="field-help">${escapeHtml(job.step_message || t("analysis.waiting"))}</p>
    ${job.error_message ? `<p class="notice error">${escapeHtml(job.error_message)}</p>` : ""}
    ${done && job.package_id ? `<button class="button primary full" data-action="open-package" data-id="${Number(job.package_id)}">${t("analysis.viewReport")} →</button>` : ""}
  </section>`;
}

function pageHeader(title, description) {
  return `<header class="page-header"><h1>${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p></header>`;
}

function renderPackageDetail() {
  if (state.detailLoading) return `<div class="empty-state" role="status">${t("detail.loading")}</div>`;
  if (state.detailError || !state.detail) {
    return `<section class="empty-state"><h2>${t("detail.loadFailed")}</h2><p class="notice error" role="alert">${escapeHtml(state.detailError || t("detail.unavailable"))}</p>
      <div class="button-row"><button class="button primary" data-action="retry-detail">${t("common.retry")}</button><button class="button secondary" data-action="navigate" data-view="overview">${t("common.backToCatalog")}</button></div></section>`;
  }
  const pkg = state.detail.package;
  const score = pkg.latest_score || {};
  const repo = pkg.repository;
  const ai = pkg.latest_ai_analysis;
  const content = {
    overview: renderScoreBreakdown(score, state.detail.scoreHistory),
    adoption: renderDetailAdoption(pkg),
    downloads: renderHistory(pkg),
    repository: renderRepository(repo),
    health: renderHealth(state.detail.health),
    security: renderSecurity(pkg, state.detail.security, state.detail.securityStatus),
    ai: renderAI(ai),
    report: renderReports(pkg),
  }[state.detailTab];
  const sectionsWithErrors = {
    overview: ["scoreHistory"],
    adoption: ["adoption", "adoptionStatus"],
    downloads: ["history", "analytics"],
    repository: ["releases"],
    health: ["health"],
    security: ["security", "securityStatus"],
  };
  const activeSectionErrors = state.detailSectionErrors.filter((item) =>
    (sectionsWithErrors[state.detailTab] || []).includes(item.key));
  const sectionWarning = activeSectionErrors.length
    ? `<div class="notice warning" role="status"><strong>${t("detail.partialData")}</strong><ul>${activeSectionErrors.map((item) => `<li>${escapeHtml(item.message)}</li>`).join("")}</ul></div>`
    : "";
  const tabs = detailTabs.map(([id, label]) => {
    const text = id === "adoption"
      ? t("tabs.adoptionCount", { count: number(state.detail.adoption.length) })
      : id === "security"
        ? t("tabs.securityCount", { count: number(state.detail.security.length) })
        : t(label);
    return `<button id="tab-${id}" type="button" role="tab" class="tab-button ${state.detailTab === id ? "active" : ""}" data-action="detail-tab" data-tab="${id}" aria-controls="panel-${id}" aria-selected="${state.detailTab === id}" tabindex="${state.detailTab === id ? "0" : "-1"}">${escapeHtml(text)}</button>`;
  }).join("");
  return `<section class="page-section">
    <button class="back-link" type="button" data-action="navigate" data-view="overview">← ${t("common.backToCatalog")}</button>
    <header class="package-header panel">
      <div class="package-heading"><div class="tag-row"><span class="badge info">${escapeHtml(statusLabel(pkg.ecosystem))}</span><span class="badge muted"><bdi dir="ltr">v${escapeHtml(pkg.latest_version || t("common.unknown"))}</bdi></span><span class="badge ${pkg.license ? "good" : "warn"}">${escapeHtml(pkg.license || t("repository.licenseNotRecorded"))}</span></div>
        <h1><bdi>${escapeHtml(pkg.name)}</bdi></h1><p>${escapeHtml(pkg.description || t("common.noPackageDescription"))}</p>
        <div class="external-links">${pkg.repository_url ? safeExternalLink(pkg.repository_url, t("detail.repository")) : ""}${pkg.homepage ? safeExternalLink(pkg.homepage, t("detail.homepage")) : ""}</div>
        <p class="package-freshness">${escapeHtml(t("detail.packageRecordUpdated", { date: formatDate(pkg.updated_at) }))}</p>
      </div>
      <div class="score-summary">${scoreGauge(score.overall_score, score.confidence_level || "unknown")}<div><strong>${t("score.title")}</strong><p>${escapeHtml(score.explanation || (score.calculated_at ? t("score.explanationMissing") : t("score.unavailable")))}</p></div></div>
    </header>
    <div class="tab-strip" role="tablist" aria-label="${t("common.packageSections")}">${tabs}</div>
    <div id="panel-${state.detailTab}" class="tab-content" role="tabpanel" aria-labelledby="tab-${state.detailTab}" tabindex="0">${sectionWarning}${content || ""}</div>
  </section>`;
}

function renderScoreBreakdown(score, scoreHistory) {
  let breakdown = {};
  if (score.breakdown) {
    try {
      const parsed = JSON.parse(score.breakdown);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) breakdown = parsed;
    } catch {
      return `<div class="empty-state">${t("score.detailsUnavailable")}</div>${renderScoreHistory(scoreHistory)}`;
    }
  }
  let entries = Object.entries(breakdown);
  if (!entries.length) {
    entries = [
      ["popularity_score", t("score.dimensionPopularity")],
      ["growth_score", t("score.dimensionGrowth")],
      ["adoption_score", t("score.dimensionAdoption")],
      ["maintenance_score", t("score.dimensionMaintenance")],
      ["documentation_score", t("score.dimensionDocumentation")],
      ["quality_score", t("score.dimensionQuality")],
      ["security_score", t("score.dimensionSecurity")],
    ]
      .filter(([key]) => score[key] !== null && score[key] !== undefined)
      .map(([key, name]) => [key, {
        name,
        score: score[key],
        weight: score.version === "v1.0.0" ? SCORE_WEIGHTS_V1[key] : null,
        explanation: t("score.noStoredDimensionExplanation"),
      }]);
  }
  if (!entries.length) return `<div class="empty-state">${t("score.noDimensions")}</div>${renderScoreHistory(scoreHistory)}`;
  const updatedAt = score.calculated_at
    ? t("score.calculated", { date: formatDate(score.calculated_at), version: score.version || t("common.unknown") })
    : t("score.timestampMissing");
  return `<div class="stack">
    <article class="panel score-methodology">
      <div class="row-between"><h2>${t("score.howToRead")}</h2>${statusBadge(score.confidence_level || "unknown")}</div>
      <p>${escapeHtml(score.explanation || t("score.noExplanation"))}</p>
      <small>${escapeHtml(updatedAt)}</small>
      <p class="field-help">${t("score.normalization")}</p>
    </article>
    <div class="dimension-grid">${entries.map(([key, dimension]) => {
    const value = dimension.score;
    const known = value !== null && value !== undefined && Number.isFinite(Number(value));
    const amount = known ? Math.max(0, Math.min(100, Number(value))) : 0;
    const hasWeight = dimension.weight !== null && dimension.weight !== undefined &&
      Number.isFinite(Number(dimension.weight));
    const weight = hasWeight ? t("score.weight", { percent: number(Number(dimension.weight) * 100) }) : t("score.weightMissing");
    const inputs = dimension.inputs && typeof dimension.inputs === "object"
      ? Object.entries(dimension.inputs).map(([name, input]) => `<div><dt>${escapeHtml(name.replaceAll("_", " "))}</dt><dd><bdi>${escapeHtml(input ?? t("score.inputMissing"))}</bdi></dd></div>`).join("")
      : "";
    return `<article class="panel dimension-card"><div class="row-between"><strong>${escapeHtml(dimension.name || key)}</strong><span class="accent-blue">${known ? `${number(value, 1)} ${t("score.outOf100")}` : t("common.na")}</span></div>
      ${known ? `<div class="progress-track" role="progressbar" aria-label="${escapeHtml(t("score.dimensionProgress", { dimension: dimension.name || key }))}" aria-valuenow="${amount}" aria-valuemin="0" aria-valuemax="100"><span class="info" style="width:${amount}%"></span></div>` : `<p class="field-help">${t("score.dimensionUnavailable")}</p>`}
      <div class="dimension-meta"><span>${weight}</span>${statusBadge(dimension.confidence || "unknown")}</div>
      <p>${escapeHtml(dimension.explanation || t("score.noDimensionExplanation"))}</p>
      ${inputs ? `<details><summary>${t("score.inputs")}</summary><dl class="details-list">${inputs}</dl></details>` : ""}</article>`;
  }).join("")}</div>
  </div>${renderScoreHistory(scoreHistory)}`;
}

function renderScoreHistory(points) {
  const valid = (Array.isArray(points) ? points : []).filter((point) =>
    point.overall_score !== null && point.overall_score !== undefined &&
    Number.isFinite(Number(point.overall_score)));
  if (valid.length < 2) {
    return `<article class="panel"><h2>${t("score.historyTitle")}</h2><p>${escapeHtml(t("score.historyInsufficient", { count: number(valid.length) }))}</p></article>`;
  }
  const width = 720;
  const height = 220;
  const padding = { top: 18, right: 20, bottom: 36, left: 62 };
  const x = (index) => padding.left + index * (width - padding.left - padding.right) / (valid.length - 1);
  const y = (value) => height - padding.bottom - Number(value) / 100 * (height - padding.top - padding.bottom);
  const polyline = valid.map((point, index) => `${x(index)},${y(point.overall_score)}`).join(" ");
  const first = escapeHtml(formatDate(valid[0].calculated_at, { dateStyle: "medium" }));
  const last = escapeHtml(formatDate(valid[valid.length - 1].calculated_at, { dateStyle: "medium" }));
  const ticks = [0, 50, 100].map((value) => `<line x1="${padding.left}" y1="${y(value)}" x2="${width - padding.right}" y2="${y(value)}" class="chart-grid"/><text x="${padding.left - 8}" y="${y(value) + 4}" text-anchor="end" class="chart-label">${number(value)}</text>`).join("");
  const markers = valid.map((point, index) => `<circle cx="${x(index)}" cy="${y(point.overall_score)}" r="4" class="chart-point"><title>${escapeHtml(t("score.historyPoint", { score: number(point.overall_score, 1), date: formatDate(point.calculated_at), confidence: statusLabel(point.confidence_level) }))}</title></circle>`).join("");
  return `<article class="panel"><div class="section-heading"><div><h2>${t("score.historyTitle")}</h2><p>${t("score.historyDescription")}</p></div><span class="badge muted">${t("score.historyCount", { count: number(valid.length) })}</span></div>
    <div class="chart-wrap"><svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="score-history-title score-history-description">
      <title id="score-history-title">${t("score.historyTitle")}</title>
      <desc id="score-history-description">${escapeHtml(t("score.historyChartDescription", { count: number(valid.length), first, last }))}</desc>${ticks}
      <polyline points="${polyline}" class="chart-line"/>${markers}
      <text x="${padding.left}" y="${height - 8}" class="chart-label">${first}</text><text x="${width - padding.right}" y="${height - 8}" text-anchor="end" class="chart-label">${last}</text>
    </svg></div>
  </article>`;
}

function renderDetailAdoption(pkg) {
  const status = state.detail.adoptionStatus;
  return `<div class="stack">
    <article class="panel"><h2>${t("adoption.externalTitle")}</h2><p>${escapeHtml(t("adoption.externalDescription", { package: pkg.name }))}</p>
      <p class="status-line">${t("adoption.status")}: ${statusBadge(status?.status || "not_checked")}</p>
      ${renderAdoptionSummary(state.detail.adoption)}
      ${(status?.caveats || []).map((item) => `<p class="caveat">${escapeHtml(item)}</p>`).join("")}</article>
    ${renderEvidenceTable(state.detail.adoption, t("adoption.noChecked"), t("adoption.noResult"))}
  </div>`;
}

function renderAdoptionSummary(items) {
  const categories = [
    ["Confirmed dependency declaration", "adoption.confirmedDependencies"],
    ["Confirmed source-code usage", "adoption.confirmedSource"],
    ["Possible usage", "adoption.possible"],
    ["Mention only", "adoption.mentions"],
    ["Unverified", "adoption.unverified"],
  ];
  const counts = new Map(items.map((item) => [item.evidence_type, 0]));
  for (const item of items) counts.set(item.evidence_type, (counts.get(item.evidence_type) || 0) + 1);
  const status = state.detail?.adoptionStatus?.status || state.adoptionStatus?.status;
  const countAvailable = ["checked", "partial"].includes(status);
  return `<div class="evidence-summary">${categories
    .map(([type, key]) => `<div><span>${t(key)}</span><strong>${countAvailable ? number(counts.get(type) || 0) : t("common.na")}</strong></div>`)
    .join("")}</div>`;
}

function renderEvidenceTable(items, emptyChecked, emptyUnknown) {
  if (!items.length) {
    const status = state.detail?.adoptionStatus?.status || state.adoptionStatus?.status;
    const message = status === "checked" ? emptyChecked : emptyUnknown;
    return `<div class="empty-state">${escapeHtml(message)}</div>`;
  }
  return `<div class="table-wrap" tabindex="0" role="region" aria-label="${t("adoption.evidenceTable")}"><table><thead><tr><th>${t("adoption.repository")}</th><th>${t("adoption.classification")}</th><th>${t("adoption.manifest")}</th><th>${t("adoption.evidence")}</th><th>${t("adoption.stars")}</th><th>${t("adoption.confidence")}</th></tr></thead>
    <tbody>${items.map((item) => `<tr>
      <td><bdi>${safeExternalLink(item.source_repo_url, item.source_repo_full_name)}</bdi></td>
      <td>${escapeHtml(evidenceTypeLabel(item.evidence_type))}</td>
      <td><code dir="ltr">${escapeHtml(item.file_path)}</code></td>
      <td>${item.raw_match ? `<details><summary>${t("adoption.viewMatch")}</summary><code dir="ltr">${escapeHtml(item.raw_match)}</code></details>` : t("adoption.rawMatchMissing")}<small class="catalog-description">${escapeHtml(t("adoption.firstRecorded", { date: formatDate(item.discovered_at, { dateStyle: "medium" }) }))}</small></td>
      <td>${number(item.stars)}</td><td>${item.confidence_score == null ? t("common.na") : `${number(Number(item.confidence_score) * 100)}%`}</td>
    </tr>`).join("")}</tbody></table></div>`;
}

function renderHistory(pkg) {
  const history = state.detail.history || {};
  const snapshots = state.detail.analytics || [];
  const latest = snapshots.length ? snapshots[snapshots.length - 1] : null;
  const growth = latest?.growth_rate;
  const average = pkg.total_downloads_30d == null ? null : Math.round(pkg.total_downloads_30d / 30);
  const points = history.historical_chart_points || [];
  return `<div class="stack">
    <div class="stat-grid three">
      <article class="stat-card"><span>${t("history.downloads30d")}</span><strong>${number(pkg.total_downloads_30d)}</strong><small>${t("history.mirrors")}</small></article>
      <article class="stat-card"><span>${t("history.growth")}</span><strong>${growth == null ? t("common.na") : `${number(growth, 2)}%`}</strong><small>${t("history.latestSnapshot")}</small></article>
      <article class="stat-card"><span>${t("history.average")}</span><strong>${average == null ? t("common.na") : number(average)}</strong><small>${t("history.averageDefinition")}</small></article>
    </div>
    <article class="panel"><div class="section-heading"><div><h2>${t("history.title")}</h2><p>${escapeHtml(history.summary || t("history.noSnapshotsSummary"))}</p></div><span class="badge muted">${t("history.records", { count: number(history.total_snapshots_recorded) })}</span></div>
      ${renderHistoryChart(points)}
      ${history.deltas?.length ? renderHistoryDeltas(history.deltas) : `<p class="field-help">${t("history.minimumSnapshots")}</p>`}
    </article>
  </div>`;
}

function renderHistoryChart(points) {
  const valid = points.filter((point) => point.downloads !== null && point.downloads !== undefined &&
    point.downloads !== "" && Number.isFinite(Number(point.downloads)));
  if (!valid.length) return `<div class="empty-chart">${t("history.noHistory")}</div>`;
  const width = 720;
  const height = 220;
  const padding = { top: 18, right: 20, bottom: 36, left: 62 };
  const values = valid.map((point) => Number(point.downloads));
  const maximum = Math.max(1, ...values);
  const min = Math.min(0, ...values);
  const span = Math.max(1, maximum - min);
  const x = (index) => padding.left + index * (width - padding.left - padding.right) / Math.max(1, valid.length - 1);
  const y = (value) => height - padding.bottom - (value - min) * (height - padding.top - padding.bottom) / span;
  const polyline = valid.map((point, index) => `${x(index)},${y(Number(point.downloads))}`).join(" ");
  const tickValues = [0, 0.5, 1].map((fraction) => min + span * fraction);
  const ticks = tickValues.map((value) => {
    const position = y(value);
    return `<line x1="${padding.left}" y1="${position}" x2="${width - padding.right}" y2="${position}" class="chart-grid"/><text x="${padding.left - 8}" y="${position + 4}" text-anchor="end" class="chart-label">${escapeHtml(number(value))}</text>`;
  }).join("");
  const markers = valid.map((point, index) => `<circle cx="${x(index)}" cy="${y(Number(point.downloads))}" r="4" class="chart-point"><title>${escapeHtml(point.date)}: ${escapeHtml(number(point.downloads))} ${t("history.downloadsUnit")}</title></circle>`).join("");
  const first = escapeHtml(valid[0].date || "");
  const last = escapeHtml(valid[valid.length - 1].date || "");
  const minimum = number(Math.min(...values));
  const maximumLabel = number(maximum);
  return `<div class="chart-wrap"><svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="history-chart-title history-chart-description">
    <title id="history-chart-title">${t("history.chartDownloadsTitle")}</title>
    <desc id="history-chart-description">${escapeHtml(t("history.observations", { count: number(valid.length), first, last, minimum, maximum: maximumLabel }))}</desc>${ticks}
    <polyline points="${polyline}" class="chart-line"/>${markers}
    <text x="${padding.left}" y="${height - 8}" class="chart-label">${first}</text><text x="${width - padding.right}" y="${height - 8}" text-anchor="end" class="chart-label">${last}</text>
  </svg><p class="chart-caption">${escapeHtml(t("history.caption", { count: number(valid.length), first, last, minimum, maximum: maximumLabel }))}</p></div>`;
}

function renderHistoryDeltas(deltas) {
  return `<div class="delta-list">${deltas.map((delta) => `<div><span>${t("history.delta")}</span><strong>${number(delta.downloads_delta)} ${t("history.downloadsUnit")} (${delta.downloads_delta_pct == null ? t("common.na") : `${number(delta.downloads_delta_pct, 2)}%`}), ${number(delta.stars_delta)} ${t("repository.stars")}, ${number(delta.forks_delta)} ${t("repository.forks")}</strong>
    <small>${escapeHtml(formatDate(delta.previous_date))} → ${escapeHtml(formatDate(delta.current_date))}</small></div>`).join("")}</div>`;
}

function renderRepository(repo) {
  if (!repo) return `<div class="empty-state">${t("repository.noLink")}</div>`;
  return `<div class="stack">
    <article class="panel"><h2>${safeExternalLink(repo.url, repo.full_name)}</h2><div class="stat-grid four">
      <div class="stat-card"><span>${t("repository.stars")}</span><strong>${number(repo.stars)}</strong></div>
      <div class="stat-card"><span>${t("repository.forks")}</span><strong>${number(repo.forks)}</strong></div>
      <div class="stat-card"><span>${t("repository.openIssues")}</span><strong>${number(repo.open_issues)}</strong></div>
      <div class="stat-card"><span>${t("repository.defaultBranch")}</span><strong class="compact"><bdi dir="ltr">${escapeHtml(repo.default_branch || t("common.na"))}</bdi></strong></div>
    </div>
    <dl class="details-list"><div><dt>${t("repository.watchers")}</dt><dd>${number(repo.watchers)}</dd></div><div><dt>${t("repository.closedIssues")}</dt><dd>${number(repo.closed_issues)}</dd></div><div><dt>${t("repository.license")}</dt><dd>${escapeHtml(repo.license || t("repository.licenseNotRecorded"))}</dd></div><div><dt>${t("repository.archived")}</dt><dd>${repo.is_archived ? t("common.yes") : t("common.no")}</dd></div><div><dt>${t("repository.fork")}</dt><dd>${repo.is_fork ? t("common.yes") : t("common.no")}</dd></div><div><dt>${t("repository.lastCommit")}</dt><dd>${escapeHtml(repo.last_commit_at ? formatDate(repo.last_commit_at) : t("common.unknown"))}</dd></div><div><dt>${t("repository.lastRelease")}</dt><dd>${escapeHtml(repo.last_release_at ? formatDate(repo.last_release_at) : t("common.unknown"))}</dd></div></dl></article>
    ${renderReleaseHistory(state.detail.releases)}
  </div>`;
}

function renderReleaseHistory(releases) {
  if (!releases.length) return `<article class="panel"><div class="row-between"><h2>${t("release.title")}</h2>${statusBadge("no records")}</div><p>${t("release.noRecords")}</p></article>`;
  return `<article class="panel"><div class="section-heading"><div><h2>${t("release.title")}</h2><p>${t("release.description")}</p></div><span class="badge muted">${t("release.records", { count: number(releases.length) })}</span></div>
    <ol class="release-list">${releases.map((release) => `<li>
      <div class="release-marker" aria-hidden="true"></div>
      <div class="release-content"><div class="row-between"><strong><bdi>${escapeHtml(release.version)}</bdi></strong>${release.is_yanked ? statusBadge("yanked") : statusBadge("available")}</div>
        <time datetime="${escapeHtml(release.release_date || "")}">${escapeHtml(release.release_date ? formatDate(release.release_date) : t("release.dateMissing"))}</time>
      </div>
    </li>`).join("")}</ol>
  </article>`;
}

function renderHealth(items) {
  if (!items.length) return `<div class="notice info"><strong>${t("health.noFindings")}</strong><p>${t("health.missingNotPass")}</p></div>`;
  const counts = items.reduce((result, finding) => {
    result[finding.status] = (result[finding.status] || 0) + 1;
    return result;
  }, {});
  return `<div class="stack">
    <article class="panel"><div class="row-between"><h2>${t("health.title")}</h2><span class="badge muted">${number(items.length)} ${t("health.checks")}</span></div>
      <div class="health-summary">${Object.entries(counts).map(([status, count]) => `<span>${statusBadge(status)} <strong>${number(count)}</strong></span>`).join("")}</div>
      <p class="field-help">${t("health.recordedFindings")}</p>
    </article>
    ${items.map((finding) => `<article class="panel finding">
    <div class="row-between"><strong>${escapeHtml(finding.check_name)}</strong>${statusBadge(finding.status)}</div>
    <p>${escapeHtml(finding.message)}</p>${finding.details ? `<details><summary>${t("common.details")}</summary><p>${escapeHtml(finding.details)}</p></details>` : ""}
    <small>${escapeHtml(finding.category)} · ${escapeHtml(formatDate(finding.detected_at))}</small>
  </article>`).join("")}
  </div>`;
}

function renderSecurity(pkg, findings, status) {
  const caveats = status?.caveats || [];
  const findingsMayBeStale = !["checked", "partial"].includes(status?.status);
  const coverageLabel = status?.status === "checked" ? t("security.verified") :
    status?.status === "partial" ? t("security.partial") : t("security.stored");
  const severityCounts = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((severity) => ({
    severity,
    count: findings.filter((item) => String(item.severity).toUpperCase() === severity).length,
  }));
  const distribution = `<div class="security-summary" aria-label="${escapeHtml(t("security.counts", { status: coverageLabel }))}">
    ${severityCounts.map(({ severity, count }) => `<div class="severity-count ${severity.toLowerCase()}"><span>${escapeHtml(t(`security.${severity.toLowerCase()}`))}</span><strong>${number(count)}</strong></div>`).join("")}
  </div>`;
  let result;
  if (findings.length) {
    result = `<div class="stack">${findings.map((item) => `<article class="panel finding security-finding">
      <div class="row-between"><strong>${escapeHtml(item.identifier)}</strong>${statusBadge(item.severity)}</div>
      <h3>${escapeHtml(item.title || t("security.identifier"))}</h3><p>${escapeHtml(item.details || t("security.detailsMissing"))}</p>
      <dl class="details-list"><div><dt>${t("security.affectedRange")}</dt><dd><bdi dir="ltr">${escapeHtml(item.affected_range || t("common.unknown"))}</bdi></dd></div><div><dt>${t("security.fixedIn")}</dt><dd><bdi dir="ltr">${escapeHtml(item.fixed_in || t("common.unknown"))}</bdi></dd></div><div><dt>${t("security.source")}</dt><dd>${escapeHtml(item.source)}</dd></div></dl>
      ${item.remediation ? `<p class="accent-green">${escapeHtml(t("security.triage", { remediation: item.remediation }))}</p>` : ""}
        ${item.reference_url ? `<p>${safeExternalLink(item.reference_url, t("security.reference"))}</p>` : ""}
    </article>`).join("")}</div>`;
  } else if (status?.status === "checked") {
    result = `<div class="notice success"><strong>${t("security.clean")}</strong><p>${escapeHtml(t("security.cleanNote", { package: pkg.name }))}</p></div>`;
  } else {
    result = `<div class="notice warning"><strong>${t("security.notClean")}</strong><p>${escapeHtml(t("security.notCleanNote", { status: statusLabel(status?.status || "not checked") }))}</p></div>`;
  }
  return `<div class="stack"><article class="panel"><div class="row-between"><h2>${t("security.title")}</h2>${statusBadge(status?.status || "not_checked")}</div>
    ${distribution}
    ${findingsMayBeStale && findings.length ? `<p class="notice warning">${t("security.findingsMayBeStale")}</p>` : ""}
    ${status?.checked_at ? `<p class="field-help">${escapeHtml(t("security.checked", { date: formatDate(status.checked_at) }))}</p>` : ""}${caveats.map((item) => `<p class="caveat">${escapeHtml(item)}</p>`).join("")}</article>${result}</div>`;
}

function renderAI(ai) {
  if (!ai) return `<div class="empty-state">${t("ai.noAnalysis")}</div>`;
  const sections = [
    [t("ai.summary"), ai.summary],
    [t("ai.risks"), ai.risks],
    [t("ai.opportunities"), ai.opportunities],
    [t("ai.recommendations"), ai.maintainer_recommendations],
    [t("ai.competitive"), ai.competitive_position],
  ].filter(([, text]) => text);
  return `<article class="panel stack"><div class="row-between"><h2>${t("ai.title")}</h2><span class="badge info">${escapeHtml(ai.model)}</span></div><p class="field-help">${escapeHtml(t("ai.generated", { date: formatDate(ai.generated_at), provider: ai.provider }))}</p>
    <div class="ai-grid">${sections.map(([title, text]) => `<section class="ai-section"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(text)}</p></section>`).join("")}</div></article>`;
}

function renderReports(pkg) {
  return `<article class="panel form-panel">
    <h2>${t("report.title")}</h2><p>${escapeHtml(t("report.description", { package: pkg.name }))}</p>
    <label class="field-label" for="report-format">${t("report.format")}</label><select id="report-format"><option value="html">${t("report.html")}</option><option value="markdown">${t("report.markdown")}</option><option value="json">${t("report.json")}</option></select>
    <button class="button primary" type="button" data-action="generate-report" ${state.reportLoading ? "disabled" : ""}>${state.reportLoading ? t("report.generating") : t("report.generate")}</button>
    ${state.reportError ? `<p class="notice error" role="alert">${escapeHtml(state.reportError)}</p>` : ""}
    ${state.reportMessage ? `<p class="notice success" role="status">${escapeHtml(state.reportMessage)}</p>` : ""}
  </article>`;
}

function renderAdoption() {
  const options = state.packages.map((pkg) => `<option value="${Number(pkg.id)}" ${String(pkg.id) === String(state.adoptionPackageId) ? "selected" : ""}>${escapeHtml(pkg.name)} (${escapeHtml(pkg.ecosystem)})</option>`).join("");
  const filtered = state.adoptionItems.filter((item) => state.adoptionFilter === "all" ||
    String(item.evidence_type).toLowerCase().includes(state.adoptionFilter));
  return `<section class="page-section">
    ${pageHeader(t("adoption.pageTitle"), t("adoption.pageDescription"))}
    ${!state.packages.length && !state.packagesLoading ? `<div class="empty-state">${t("adoption.emptyPackages")}</div>` : ""}
    <div class="filter-row">
      <label class="field-label">${t("adoption.package")}<select id="adoption-package">${options}</select></label>
      <label class="field-label">${t("adoption.filterLabel")}<select id="adoption-filter">
        <option value="all" ${state.adoptionFilter === "all" ? "selected" : ""}>${t("adoption.allClassifications")}</option>
        <option value="dependency" ${state.adoptionFilter === "dependency" ? "selected" : ""}>${t("adoption.confirmedDeclaration")}</option>
        <option value="source-code" ${state.adoptionFilter === "source-code" ? "selected" : ""}>${t("adoption.confirmedCode")}</option>
        <option value="possible" ${state.adoptionFilter === "possible" ? "selected" : ""}>${t("adoption.possibleUsage")}</option>
        <option value="mention" ${state.adoptionFilter === "mention" ? "selected" : ""}>${t("adoption.mentionOnly")}</option>
      </select></label>
    </div>
    ${state.packagesError ? `<p class="notice error" role="alert">${escapeHtml(state.packagesError)}</p>` : ""}
    ${state.adoptionError ? `<div class="notice error" role="alert">${escapeHtml(state.adoptionError)} <button class="button secondary" type="button" data-action="retry-adoption">${t("common.retry")}</button></div>` : ""}
    ${state.adoptionItems.length ? `<article class="panel"><div class="row-between"><h2>${t("adoption.evidenceClassification")}</h2><span class="badge muted">${t("adoption.records", { count: number(state.adoptionItems.length) })}</span></div>${renderAdoptionSummary(state.adoptionItems)}</article>` : ""}
    ${state.adoptionLoading ? `<div class="empty-state" role="status">${t("error.loadAdoption")}</div>` :
      filtered.length === 0 && state.adoptionItems.length > 0
        ? `<div class="empty-state">${t("adoption.noRecordsForFilter")}</div>`
        : renderEvidenceTable(filtered,
          t("adoption.noRecordsChecked"),
          t("adoption.discoveryIncomplete"))}
    ${state.adoptionStatus ? `<article class="panel"><div class="row-between"><h2>${t("adoption.discoveryStatus")}</h2>${statusBadge(state.adoptionStatus.status)}</div>
      ${(state.adoptionStatus.caveats || []).map((item) => `<p class="caveat">${escapeHtml(item)}</p>`).join("")}</article>` : ""}
  </section>`;
}

function renderCompare() {
  const selected = new Set(state.compareIds.map(Number));
  const choices = state.packages.map((pkg) => `<label class="choice ${selected.has(Number(pkg.id)) ? "selected" : ""}">
    <input type="checkbox" name="compare-package" value="${Number(pkg.id)}" ${selected.has(Number(pkg.id)) ? "checked" : ""}>
    <span><bdi>${escapeHtml(pkg.name)}</bdi></span><small>${escapeHtml(statusLabel(pkg.ecosystem))}</small></label>`).join("");
  return `<section class="page-section">
    ${pageHeader(t("compare.title"), t("compare.description"))}
    ${state.packagesLoading ? `<div class="empty-state" role="status">${t("analysis.loadingPackages")}</div>` : ""}
    ${!state.packagesLoading && state.packages.length < 2 ? `<div class="empty-state">${t("compare.minimumTwo")}</div>` : ""}
    <form id="compare-form" class="panel stack">
      <fieldset class="choice-fieldset"><legend>${t("compare.select")}</legend><div class="choice-grid">${choices}</div></fieldset>
      <button class="button primary" type="submit" ${state.comparisonLoading || state.compareIds.length < 2 ? "disabled" : ""}>${state.comparisonLoading ? t("compare.running") : t("compare.submit")}</button>
    </form>
    ${state.comparisonError ? `<p class="notice error" role="alert">${escapeHtml(state.comparisonError)}</p>` : ""}
    ${state.comparison ? renderComparison(state.comparison) : ""}
  </section>`;
}

function renderComparison(result) {
  const metrics = [
    [t("compare.metric.score"), (pkg) => pkg.overall_score == null ? t("common.na") : `${number(pkg.overall_score, 1)} / 100`],
    [t("compare.metric.confidence"), (pkg) => statusLabel(pkg.confidence)],
    [t("compare.metric.monthly"), (pkg) => number(pkg.monthly_downloads)],
    [t("compare.metric.stars"), (pkg) => number(pkg.stars)],
    [t("compare.metric.forks"), (pkg) => number(pkg.forks)],
    [t("compare.metric.openIssues"), (pkg) => number(pkg.open_issues)],
    [t("compare.metric.version"), (pkg) => pkg.latest_version || t("common.unknown")],
    [t("compare.metric.releaseAge"), (pkg) => pkg.last_release_age_days == null ? t("compare.unknownDays") : `${number(pkg.last_release_age_days)} ${t("common.days")}`],
    [t("compare.metric.adoptions"), (pkg) => number(pkg.verified_adoptions)],
    [t("compare.metric.vulnerabilities"), (pkg) => number(pkg.vulnerabilities_count)],
    [t("compare.metric.license"), (pkg) => pkg.license || t("repository.unspecified")],
  ];
  return `<div class="stack comparison-result">
    <article class="notice info"><strong>${t("compare.summary")}</strong><p>${escapeHtml(t("compare.summaryCount", { count: number(result.packages.length) }))}</p></article>
    <div class="table-wrap" tabindex="0" role="region" aria-label="${t("compare.table")}"><table class="comparison-table"><thead><tr><th>${t("common.metric")}</th>${result.packages.map((pkg) => `<th><bdi>${escapeHtml(pkg.package_name)}</bdi><small>${escapeHtml(statusLabel(pkg.ecosystem))}</small></th>`).join("")}</tr></thead>
    <tbody>${metrics.map(([label, getter]) => `<tr><th>${escapeHtml(label)}</th>${result.packages.map((pkg) => `<td>${escapeHtml(getter(pkg))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
    ${result.packages.some((pkg) => pkg.comparability_notes?.length) ? `<div class="panel"><h2>${t("compare.comparability")}</h2>${result.packages.map((pkg) => pkg.comparability_notes?.length ? `<p><strong><bdi>${escapeHtml(pkg.package_name)}</bdi>:</strong> ${pkg.comparability_notes.map((note) => `<span>${escapeHtml(localizeComparisonNote(note))}</span>`).join(" ")}</p>` : "").join("")}</div>` : ""}
    <p class="field-help">${escapeHtml(t("compare.comparedAt", { date: formatDate(result.compared_at) }))}</p>
  </div>`;
}

function renderSettings() {
  const info = state.versionInfo;
  return `<section class="page-section narrow">
    ${pageHeader(t("settings.title"), t("settings.description"))}
    ${state.settingsError ? `<div class="notice error" role="alert">${escapeHtml(state.settingsError)} <button class="button secondary" type="button" data-action="retry-settings">${t("common.retry")}</button></div>` : ""}
    <article class="panel stack">
      <div><h2>${t("settings.apiAccess")}</h2><p>${t("settings.apiKeyHelp")}</p></div>
      <form id="api-key-form" class="key-form">
        <label class="sr-only" for="api-key-input">${t("settings.apiKeyLabel")}</label><input id="api-key-input" type="password" autocomplete="off" spellcheck="false" placeholder="${api.hasApiKey() ? t("settings.replaceKeyPlaceholder") : t("settings.apiKeyPlaceholder")}">
        <button class="button primary" type="submit">${t("settings.useKey")}</button>${api.hasApiKey() ? `<button class="button secondary" type="button" data-action="clear-key">${t("settings.clearKey")}</button>` : ""}
      </form>
      <p class="field-help" role="status">${escapeHtml(state.apiKeyMessage || (api.hasApiKey() ? t("settings.apiKeyActive") : t("settings.apiKeyAbsent")))}</p>
    </article>
    <article class="panel stack">
      <h2>${t("settings.providers")}</h2>
      <div class="provider-row"><div><strong>${t("settings.pypi")}</strong><small>${t("settings.pypiHelp")}</small></div>${statusBadge("active")}</div>
      <div class="provider-row"><div><strong>${t("settings.github")}</strong><small>${info?.github_token_configured ? t("settings.authenticated") : t("settings.unauthenticated")}</small></div>${statusBadge(info?.github_token_configured ? "authenticated" : "anonymous")}</div>
      <div class="provider-row"><div><strong>${t("settings.osv")}</strong><small>${t("settings.osvHelp")}</small></div>${statusBadge("active")}</div>
    </article>
    <article class="panel stack">
      <h2>${t("settings.ai")}</h2><p>${t("settings.aiHelp")}</p>
      <dl class="details-list"><div><dt>${t("settings.provider")}</dt><dd><bdi>${escapeHtml(info?.ai_provider || (state.settingsLoading ? t("settings.loading") : t("settings.unknown")))}</bdi></dd></div>
      <div><dt>${t("settings.credentials")}</dt><dd>${info?.ai_configured ? t("settings.configured") : state.settingsLoading ? t("settings.loading") : t("settings.deterministic")}</dd></div></dl>
    </article>
    <article class="panel stack">
      <h2>${t("settings.security")}</h2><p>${t("settings.securityHelp")}</p>
      <p class="field-help">${t("settings.sharedKey")}</p>
    </article>
    <article class="panel row-between"><div><h2>${t("settings.database")}</h2><p>${t("settings.loadDemo")}</p></div><button class="button secondary" data-action="seed" ${state.seedLoading ? "disabled" : ""}>${state.seedLoading ? t("settings.seeding") : t("common.loadSampleData")}</button></article>
  </section>`;
}

function render() {
  renderShell();
}

function showPageOnly() {
  const container = app.querySelector("#page-view");
  if (container) {
    container.innerHTML = renderPage();
  }
}

async function loadDashboardSummary() {
  const requestId = ++state.summaryRequest;
  state.summaryLoading = true;
  state.summaryError = "";
  if (state.view === "overview") render();
  try {
    const summary = await api.getDashboardSummary();
    if (!summary || !Array.isArray(summary.recent_jobs)) {
      throw new Error(t("error.dashboardSummary"));
    }
    if (requestId !== state.summaryRequest) return;
    state.dashboardSummary = summary;
  } catch (error) {
    if (requestId === state.summaryRequest) state.summaryError = error.message || t("error.dashboardSummary");
  } finally {
    if (requestId === state.summaryRequest) {
      state.summaryLoading = false;
      if (state.view === "overview") render();
    }
  }
}

function navigate(view, { syncUrl = true } = {}) {
  state.view = view;
  state.mobileNavOpen = false;
  if (view === "overview") state.packageId = null;
  if (syncUrl) writeRoute(view, null, null);
  if (view === "settings" && !state.versionInfo && !state.settingsLoading) loadSettings();
  render();
  if (view === "adoption" && state.packages.length &&
      (!state.adoptionPackageId || state.adoptionError || state.adoptionLoadedFor !== state.adoptionPackageId)) {
    state.adoptionPackageId = state.adoptionPackageId || String(state.packages[0].id);
    loadAdoption(state.adoptionPackageId);
  }
}

async function loadPackages() {
  state.packagesLoading = true;
  state.packagesError = "";
  render();
  try {
    state.packages = await api.listPackages();
    if (!Array.isArray(state.packages)) throw new Error(t("error.packageList"));
    if (state.packages.length && !state.compareIds.length) {
      state.compareIds = state.packages.slice(0, 3).map((pkg) => Number(pkg.id));
    }
    if (!state.adoptionPackageId && state.packages.length) state.adoptionPackageId = String(state.packages[0].id);
  } catch (error) {
    state.packagesError = error.message || t("error.loadPackages");
  } finally {
    state.packagesLoading = false;
    render();
    if (state.view === "adoption" && state.adoptionPackageId && !state.adoptionItems.length) {
      loadAdoption(state.adoptionPackageId);
    }
  }
}

async function loadSettings() {
  state.settingsLoading = true;
  state.settingsError = "";
  showPageOnly();
  try {
    state.versionInfo = await api.getVersion();
  } catch (error) {
    state.settingsError = error.message || t("error.serviceSettings");
  } finally {
    state.settingsLoading = false;
    if (state.view === "settings") showPageOnly();
  }
}

async function loadAdoption(packageId) {
  if (!packageId) return;
  const requestId = ++state.adoptionRequest;
  state.adoptionLoading = true;
  state.adoptionError = "";
  state.adoptionItems = [];
  state.adoptionStatus = null;
  if (state.view === "adoption") showPageOnly();
  try {
    const [items, status] = await Promise.all([
      api.getPackageAdoption(packageId),
      api.getPackageAdoptionStatus(packageId),
    ]);
    if (requestId !== state.adoptionRequest) return;
    if (!Array.isArray(items)) throw new Error(t("error.adoption"));
    state.adoptionItems = items;
    state.adoptionStatus = status;
    state.adoptionLoadedFor = String(packageId);
  } catch (error) {
    if (requestId === state.adoptionRequest) state.adoptionError = error.message || t("error.loadAdoption");
  } finally {
    if (requestId === state.adoptionRequest) {
      state.adoptionLoading = false;
      if (state.view === "adoption") showPageOnly();
    }
  }
}

async function loadDetail(packageId, { tab = "overview", syncUrl = true } = {}) {
  const requestId = ++state.detailRequest;
  state.packageId = Number(packageId);
  state.detail = null;
  state.detailLoading = true;
  state.detailError = "";
  state.detailSectionErrors = [];
  state.detailTab = detailTabs.some(([id]) => id === tab) ? tab : "overview";
  state.reportError = "";
  state.reportLoading = false;
  state.view = "package-detail";
  if (syncUrl) writeRoute("package-detail", state.packageId, state.detailTab);
  render();
  try {
    const id = state.packageId;
    const pkg = await api.getPackage(id);
    if (!pkg || typeof pkg !== "object" || Array.isArray(pkg)) {
      throw new Error(t("error.detail"));
    }
    const isRecord = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
    const requests = [
      ["adoption", api.getPackageAdoption(id), Array.isArray, []],
      ["adoptionStatus", api.getPackageAdoptionStatus(id), isRecord, null],
      ["health", api.getPackageHealth(id), Array.isArray, []],
      ["security", api.getPackageSecurity(id), Array.isArray, []],
      ["securityStatus", api.getPackageSecurityStatus(id), isRecord, null],
      ["history", api.getPackageHistory(id), isRecord, {}],
      ["analytics", api.getPackageAnalytics(id), Array.isArray, []],
      ["releases", api.getPackageReleases(id), Array.isArray, []],
      ["scoreHistory", api.getPackageScoreHistory(id), Array.isArray, []],
    ];
    const settled = await Promise.allSettled(requests.map(([, request]) => request));
    if (requestId !== state.detailRequest) return;
    const detailData = {};
    for (const [index, [key, , isValid, fallback]] of requests.entries()) {
      const result = settled[index];
      if (result.status === "fulfilled" && isValid(result.value)) {
        detailData[key] = result.value;
      } else {
        detailData[key] = fallback;
        const error = result.status === "rejected" ? result.reason : null;
        state.detailSectionErrors.push({ key, message: error?.message || t("error.detailSection") });
      }
    }
    state.detail = { package: pkg, ...detailData };
  } catch (error) {
    if (requestId === state.detailRequest) state.detailError = error.message || t("error.loadDetail");
  } finally {
    if (requestId === state.detailRequest) {
      state.detailLoading = false;
      if (state.view === "package-detail") showPageOnly();
    }
  }
}

async function seedDemo() {
  state.seedLoading = true;
  state.seedError = "";
  render();
  try {
    await api.seedDemo();
    await loadPackages();
    await loadDashboardSummary();
    state.seedError = "";
  } catch (error) {
    state.seedError = error.message || t("error.seed");
  } finally {
    state.seedLoading = false;
    render();
  }
}

async function submitAnalysis(form) {
  if (state.analysisSubmitting) return;
  const formData = new FormData(form);
  const input = String(formData.get("packageName") || "");
  const result = parseAnalysisInput(input, String(formData.get("ecosystem") || "pypi"));
  state.analysisName = input;
  if (!result.valid) {
    state.analysisValidation = result.reason;
    state.analysisError = "";
    showPageOnly();
    app.querySelector("#analysis-name")?.focus();
    return;
  }
  state.analysisValidation = "";
  state.analysisEcosystem = result.ecosystem;
  state.analysisEnableAi = formData.has("enableAi");
  state.analysisSubmitting = true;
  state.analysisError = "";
  state.analysisJob = null;
  render();
  try {
    const job = await api.triggerAnalysis(result.identifier, result.ecosystem, state.analysisEnableAi);
    state.analysisJob = job;
    if (["queued", "running"].includes(job.status)) pollJob(job.id);
    if (job.status === "completed") {
      loadPackages();
      loadDashboardSummary();
    }
  } catch (error) {
    state.analysisError = error.message || t("error.submitAnalysis");
  } finally {
    state.analysisSubmitting = false;
    if (state.view === "analyze") showPageOnly();
  }
}

function pollJob(jobId) {
  if (state.jobTimer) clearTimeout(state.jobTimer);
  const poll = async () => {
    if (!state.analysisJob || state.analysisJob.id !== jobId || !["queued", "running"].includes(state.analysisJob.status)) return;
    try {
      const updated = await api.getJob(jobId);
      if (!state.analysisJob || state.analysisJob.id !== jobId) return;
      state.analysisJob = updated;
      state.analysisError = "";
      if (updated.status === "completed") {
        loadPackages();
        loadDashboardSummary();
      }
      if (state.view === "analyze") showPageOnly();
      if (["queued", "running"].includes(updated.status)) state.jobTimer = setTimeout(poll, 1200);
    } catch (error) {
      state.analysisError = error.message || t("error.pollJob");
      if (state.view === "analyze") showPageOnly();
      state.jobTimer = setTimeout(poll, 3000);
    }
  };
  state.jobTimer = setTimeout(poll, 1000);
}

async function submitComparison(form) {
  const packageIds = Array.from(new FormData(form).getAll("compare-package")).map(Number);
  state.compareIds = packageIds;
  if (packageIds.length < 2 || state.comparisonLoading) return;
  state.comparisonLoading = true;
  state.comparisonError = "";
  showPageOnly();
  try {
    state.comparison = await api.comparePackages(packageIds);
  } catch (error) {
    state.comparisonError = error.message || t("error.compare");
  } finally {
    state.comparisonLoading = false;
    if (state.view === "compare") showPageOnly();
  }
}

async function generateReport() {
  if (!state.detail || state.reportLoading) return;
  const format = app.querySelector("#report-format")?.value || "html";
  state.reportLoading = true;
  state.reportError = "";
  state.reportMessage = "";
  showPageOnly();
  let htmlWindow = null;
  if (format === "html") htmlWindow = window.open("about:blank", "_blank");
  try {
    const result = await api.generateReport(state.packageId, format);
    if (format === "html") {
      if (htmlWindow && result.id) {
        htmlWindow.opener = null;
        htmlWindow.location.href = `/api/v1/reports/${encodeURIComponent(result.id)}`;
        state.reportMessage = t("report.htmlMessage");
      } else {
        htmlWindow?.close();
        throw new Error(t("report.blocked"));
      }
    } else {
      const extension = format === "json" ? "json" : "md";
      const mime = format === "json" ? "application/json" : "text/markdown";
      const url = URL.createObjectURL(new Blob([result.content], { type: `${mime};charset=utf-8` }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `libscope-${state.detail.package.name}.${extension}`;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      state.reportMessage = t("report.downloadMessage", { format: t(format === "json" ? "report.json" : "report.markdown") });
    }
  } catch (error) {
    htmlWindow?.close();
    state.reportError = error.message || t("error.report");
  } finally {
    state.reportLoading = false;
    if (state.view === "package-detail") showPageOnly();
  }
}

app.addEventListener("click", (event) => {
  const target = event.target.closest("[data-action]");
  if (!target || target.disabled) return;
  if (target.tagName === "A") event.preventDefault();
  const action = target.dataset.action;
  if (action === "navigate") navigate(target.dataset.view);
  if (action === "toggle-nav") {
    state.mobileNavOpen = !state.mobileNavOpen;
    render();
  }
  if (action === "open-package") {
    if (state.view === "analyze" && state.analysisJob?.status === "completed" &&
        state.analysisJob.package_id === Number(target.dataset.id)) {
      loadPackages();
    }
    loadDetail(target.dataset.id);
  }
  if (action === "detail-tab") {
    state.detailTab = target.dataset.tab;
    writeRoute("package-detail", state.packageId, state.detailTab);
    showPageOnly();
  }
  if (action === "seed") seedDemo();
  if (action === "reload-packages") loadPackages();
  if (action === "reload-summary") loadDashboardSummary();
  if (action === "retry-detail") loadDetail(state.packageId);
  if (action === "retry-adoption") loadAdoption(state.adoptionPackageId);
  if (action === "retry-settings") loadSettings();
  if (action === "generate-report") generateReport();
  if (action === "clear-key") {
    api.clearApiKey();
    state.apiKeyMessage = t("settings.keyCleared");
    showPageOnly();
  }
  if (action === "toggle-theme") {
    applyTheme(state.theme === "dark" ? "light" : "dark");
    render();
  }
});

app.addEventListener("input", (event) => {
  if (event.target.id === "analysis-name") {
    state.analysisName = event.target.value;
    const result = parseAnalysisInput(event.target.value, state.analysisEcosystem);
    state.analysisValidation = result.valid ? "" : result.reason;
    if (result.valid) state.analysisEcosystem = result.ecosystem;
    const feedback = app.querySelector("#analysis-feedback");
    const ecosystem = app.querySelector('select[name="ecosystem"]');
    event.target.setAttribute("aria-invalid", String(!result.valid && event.target.value.trim() !== ""));
    if (feedback) {
      feedback.textContent = result.valid
        ? t("analysis.normalized", { identifier: result.identifier, ecosystem: t(`analysis.${result.ecosystem}`) })
        : event.target.value.trim() ? t(result.reason) : t("analysis.inputExamples");
    }
    if (ecosystem && result.valid) ecosystem.value = result.ecosystem;
    return;
  }
  if (event.target.id !== "package-search") return;
  state.search = event.target.value;
  const list = app.querySelector("#package-list");
  if (list) {
    list.innerHTML = state.packagesLoading ? `<div class="empty-state">${t("catalog.loading")}</div>` : renderPackageCards();
  }
});

app.addEventListener("change", async (event) => {
  if (event.target.id === "language-select") {
    try {
      await setLocale(event.target.value);
      state.localeError = "";
      render();
    } catch (error) {
      console.error("Unable to change the dashboard language.", error);
      state.localeError = t("settings.languageError");
      render();
    }
    return;
  }
  if (event.target.name === "ecosystem") {
    state.analysisEcosystem = event.target.value === "github" ? "github" : "pypi";
    const input = app.querySelector("#analysis-name");
    const feedback = app.querySelector("#analysis-feedback");
    const result = parseAnalysisInput(input?.value || "", state.analysisEcosystem);
    state.analysisValidation = result.valid ? "" : result.reason;
    if (result.valid) state.analysisEcosystem = result.ecosystem;
    event.target.value = state.analysisEcosystem;
    input?.setAttribute("aria-invalid", String(!result.valid && Boolean(input.value.trim())));
    if (feedback) {
      feedback.textContent = result.valid
        ? t("analysis.normalized", { identifier: result.identifier, ecosystem: t(`analysis.${result.ecosystem}`) })
        : input?.value.trim() ? t(result.reason) : t("analysis.inputExamples");
    }
    return;
  }
  if (event.target.id === "adoption-package") {
    state.adoptionPackageId = event.target.value;
    loadAdoption(state.adoptionPackageId);
  }
  if (event.target.id === "adoption-filter") {
    state.adoptionFilter = event.target.value;
    showPageOnly();
  }
  if (event.target.name === "compare-package") {
    const checked = Array.from(app.querySelectorAll('input[name="compare-package"]:checked')).map((input) => input.value);
    if (checked.length > 10) {
      event.target.checked = false;
      state.comparisonError = t("compare.maxError");
      state.compareIds = checked.slice(0, 10).map(Number);
    } else {
      state.comparisonError = "";
      state.compareIds = checked.map(Number);
    }
    state.comparison = null;
    showPageOnly();
  }
});

app.addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.target.id === "analysis-form") submitAnalysis(event.target);
  if (event.target.id === "compare-form") submitComparison(event.target);
  if (event.target.id === "api-key-form") {
    const input = app.querySelector("#api-key-input");
    if (!input?.value.trim()) {
      state.apiKeyMessage = t("settings.enterKey");
    } else {
      api.setApiKey(input.value);
      state.apiKeyMessage = t("settings.apiKeyOnly");
    }
    showPageOnly();
  }
});

app.addEventListener("keydown", (event) => {
  const tab = event.target.closest('[role="tab"]');
  if (!tab || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  const tabs = Array.from(app.querySelectorAll('[role="tab"]'));
  const current = tabs.indexOf(tab);
  const direction = getLocale() === "en" ? 1 : -1;
  const next = event.key === "Home" ? 0
    : event.key === "End" ? tabs.length - 1
      : (current + (event.key === "ArrowRight" ? direction : -direction) + tabs.length) % tabs.length;
  event.preventDefault();
  tabs[next].focus();
  tabs[next].click();
});

async function startApplication() {
  try {
    await initializeI18n();
  } catch (error) {
    console.error("Unable to initialize dashboard translations.", error);
    app.replaceChildren();
    const message = document.createElement("div");
    message.className = "empty-state";
    message.setAttribute("role", "alert");
    message.textContent = `Unable to load dashboard language resources: ${error.message}`;
    app.append(message);
    return;
  }
  const route = readRoute();
  state.view = route.view;
  state.packageId = route.packageId || null;
  state.detailTab = route.detailTab || "overview";
  render();
  loadPackages();
  loadDashboardSummary();
  if (state.view === "settings") loadSettings();
  if (state.view === "package-detail" && state.packageId) {
    loadDetail(state.packageId, { tab: state.detailTab, syncUrl: false });
  }
}

watchRoute(() => {
  const route = readRoute();
  if (route.view === "package-detail" && route.packageId) {
    loadDetail(route.packageId, { tab: route.detailTab, syncUrl: false });
  } else {
    navigate(route.view, { syncUrl: false });
  }
});

startApplication();
