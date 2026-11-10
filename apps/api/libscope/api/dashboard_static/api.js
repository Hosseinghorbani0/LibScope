import { t } from "./i18n.js";

const API_BASE = "/api/v1";
const REQUEST_TIMEOUT_MS = 15000;
let apiKey = null;

function getErrorMessage(status, headers) {
  const key = status === 401 ? "error.unauthorized"
    : status === 403 ? "error.forbidden"
      : status === 404 ? "error.notFound"
        : status === 400 || status === 422 ? "error.invalidRequest"
          : status === 429 ? "error.rateLimited"
            : status >= 500 ? "error.server"
              : null;
  const message = key ? t(key) : t("error.http", { status });
  if (status !== 429) return message;
  const retryAfter = Number(headers.get("retry-after"));
  return Number.isFinite(retryAfter) && retryAfter > 0
    ? `${message}${t("error.retryAfter", { seconds: retryAfter })}`
    : message;
}

async function request(path, { method = "GET", body, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  const headers = new Headers({ Accept: "application/json" });
  if (body !== undefined) headers.set("Content-Type", "application/json");
  if (apiKey) headers.set("Authorization", `Bearer ${apiKey}`);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    let response;
    try {
      response = await fetch(path, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
        credentials: "same-origin",
      });
    } catch (error) {
      if (controller.signal.aborted) throw new Error(t("error.timeout"));
      if (error instanceof TypeError) {
        throw new Error(t("error.network"));
      }
      throw error;
    }

    const contentType = response.headers.get("content-type") || "";
    let payload;
    try {
      payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();
    } catch (error) {
      if (controller.signal.aborted) throw new Error(t("error.timeout"));
      if (contentType.includes("application/json")) throw new Error(t("error.invalidJson"));
      throw error;
    }

    if (!response.ok) throw new Error(getErrorMessage(response.status, response.headers));
    if (contentType.includes("application/json") && payload === null) {
      throw new Error(t("error.emptyJson"));
    }
    return payload;
  } catch (error) {
    if (controller.signal.aborted) throw new Error(t("error.timeout"));
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function packagePath(id, suffix = "") {
  return `${API_BASE}/packages/${encodeURIComponent(id)}${suffix}`;
}

export const api = {
  setApiKey(value) {
    apiKey = value.trim() || null;
  },
  clearApiKey() {
    apiKey = null;
  },
  hasApiKey() {
    return apiKey !== null;
  },
  getVersion() {
    return request(`${API_BASE}/version`);
  },
  getDashboardSummary(recentLimit = 5) {
    return request(`${API_BASE}/dashboard/summary?recent_limit=${encodeURIComponent(recentLimit)}`);
  },
  listPackages() {
    return request(`${API_BASE}/packages?limit=100`);
  },
  getPackage(id) {
    return request(packagePath(id));
  },
  getPackageScoreHistory(id, limit = 100) {
    return request(`${packagePath(id, "/score-history")}?limit=${encodeURIComponent(limit)}`);
  },
  getPackageAnalytics(id, limit = 100, offset = 0) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    return request(`${packagePath(id, "/analytics")}?${params}`);
  },
  getPackageHistory(id, limit = 100) {
    return request(`${packagePath(id, "/history")}?limit=${encodeURIComponent(limit)}`);
  },
  getPackageReleases(id, limit = 50, offset = 0) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    return request(`${packagePath(id, "/releases")}?${params}`);
  },
  getPackageHealth(id) {
    return request(packagePath(id, "/health"));
  },
  getPackageAdoption(id) {
    return request(packagePath(id, "/adoption"));
  },
  getPackageAdoptionStatus(id) {
    return request(packagePath(id, "/adoption/status"));
  },
  getPackageSecurity(id) {
    return request(packagePath(id, "/security"));
  },
  getPackageSecurityStatus(id) {
    return request(packagePath(id, "/security/status"));
  },
  triggerAnalysis(packageName, ecosystem, enableAi) {
    return request(`${API_BASE}/analyze`, {
      method: "POST",
      body: { package_name: packageName, ecosystem, enable_ai: enableAi },
    });
  },
  getJob(jobId) {
    return request(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`);
  },
  comparePackages(packageIds) {
    return request(`${API_BASE}/compare`, {
      method: "POST",
      body: { package_ids: packageIds },
    });
  },
  generateReport(packageId, format) {
    return request(`${API_BASE}/reports/generate`, {
      method: "POST",
      body: { package_id: packageId, format },
    });
  },
  seedDemo() {
    return request(`${API_BASE}/demo/seed`, { method: "POST" });
  },
};

