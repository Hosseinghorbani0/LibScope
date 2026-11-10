const VIEWS = new Set(["overview", "analyze", "adoption", "compare", "settings"]);
const DETAIL_TABS = new Set([
  "overview",
  "adoption",
  "downloads",
  "repository",
  "health",
  "security",
  "ai",
  "report",
]);
let lastSeenUrl = null;

export function readRoute(hash = window.location.hash) {
  const parts = hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (parts[0] === "packages" && /^\d+$/.test(parts[1] || "")) {
    return {
      view: "package-detail",
      packageId: Number(parts[1]),
      detailTab: DETAIL_TABS.has(parts[2]) ? parts[2] : "overview",
    };
  }
  return { view: VIEWS.has(parts[0]) ? parts[0] : "overview" };
}

export function writeRoute(view, packageId, detailTab, { replace = false } = {}) {
  const path = view === "package-detail" && Number.isInteger(Number(packageId)) && Number(packageId) > 0
    ? `#/packages/${Number(packageId)}/${DETAIL_TABS.has(detailTab) ? detailTab : "overview"}`
    : `#/${VIEWS.has(view) ? view : "overview"}`;
  if (window.location.hash === path) return;
  const method = replace ? "replaceState" : "pushState";
  window.history[method](null, "", path);
  lastSeenUrl = window.location.href;
}

export function watchRoute(listener) {
  lastSeenUrl ??= window.location.href;
  const handleRouteChange = () => {
    if (window.location.href === lastSeenUrl) return;
    lastSeenUrl = window.location.href;
    listener();
  };
  window.addEventListener("popstate", handleRouteChange);
  window.addEventListener("hashchange", handleRouteChange);
}
