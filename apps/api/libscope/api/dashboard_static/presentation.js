import { getIntlLocale, hasTranslation, t } from "./i18n.js";

export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

export function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) {
    return t("common.na");
  }
  return Number(value).toLocaleString(getIntlLocale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function safeExternalLink(value, label) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") return escapeHtml(label);
    return `<a href="${escapeHtml(url.href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
  } catch {
    return escapeHtml(label);
  }
}

export function formatDate(value, options = { dateStyle: "medium" }) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? t("common.unknown") : parsed.toLocaleString(getIntlLocale(), options);
}

export function statusLabel(status) {
  const normalized = String(status || "unknown").toLowerCase().replaceAll(" ", "_");
  const translationKey = `status.${normalized}`;
  return hasTranslation(translationKey) ? t(translationKey) : t("status.unknown");
}

export function statusBadge(status) {
  const normalized = String(status || "unknown").toLowerCase();
  const tone = ["pass", "checked", "completed", "active", "authenticated"].includes(normalized)
    ? "good"
    : ["warning", "partial", "queued", "running"].includes(normalized)
      ? "warn"
      : ["failed", "fail", "cancelled", "critical", "high"].includes(normalized)
        ? "bad"
        : "muted";
  return `<span class="badge ${tone}">${escapeHtml(statusLabel(normalized))}</span>`;
}

export function evidenceTypeLabel(value) {
  const key = {
    "Confirmed dependency declaration": "adoption.confirmedDeclaration",
    "Confirmed source-code usage": "adoption.confirmedCode",
    "Possible usage": "adoption.possibleUsage",
    "Mention only": "adoption.mentionOnly",
    Unverified: "adoption.unverified",
  }[String(value || "")];
  return key ? t(key) : t("status.unknown");
}

export function localizeComparisonNote(value) {
  const key = {
    "Cross-ecosystem comparison: registry download statistics are not directly comparable.":
      "compare.note.crossEcosystem",
    "High download volume with relatively low GitHub stars suggests automated CI/sub-dependency usage.":
      "compare.note.highDownloads",
    "High GitHub stars with modest registry downloads indicates portfolio/educational interest rather than widespread runtime installation.":
      "compare.note.highStars",
  }[String(value || "")];
  return key ? t(key) : String(value || "");
}

export function scoreGauge(score, confidence = "medium", size = 112) {
  const missing = score === null || score === undefined || !Number.isFinite(Number(score));
  const value = missing ? 0 : Math.min(100, Math.max(0, Number(score)));
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const color = missing ? "var(--subtle)" : value >= 85 ? "var(--positive)" : value >= 65 ? "var(--warning)" : "var(--danger)";
  const offset = circumference - value / 100 * circumference;
  return `<div class="score-wrap">
    <svg class="score-gauge" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="${escapeHtml(missing ? t("score.unavailable") : `${t("score.title")}: ${formatNumber(value, 1)} / 100`)}">
      <circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="none" stroke="var(--border)" stroke-width="8"/>
      ${missing ? "" : `<circle cx="${size / 2}" cy="${size / 2}" r="${radius}" fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>`}
    </svg>
    <span class="score-value" style="color:${color}">${missing ? escapeHtml(t("common.na")) : formatNumber(value, 1)}<small>${t("score.outOf100")}</small></span>
    <span class="badge ${confidence === "high" ? "good" : confidence === "low" ? "bad" : "warn"}">${escapeHtml(t("score.confidence", { confidence: statusLabel(confidence) }))}</span>
  </div>`;
}
