const IDENTIFIER_SEGMENT = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const MAX_IDENTIFIER_LENGTH = 255;
const HOST_LIKE_PREFIX = /^(?:www\.)?(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?:\/|$)/;

function invalid(reason) {
  return { valid: false, reason };
}

function valid(identifier, ecosystem, source) {
  return { valid: true, identifier, ecosystem, source };
}

function validateIdentifier(identifier, ecosystem, source) {
  if (identifier.length > MAX_IDENTIFIER_LENGTH) return invalid("analysis.validation.tooLong");
  const segments = identifier.split("/");
  if (segments.length > 2 || segments.some((segment) => !IDENTIFIER_SEGMENT.test(segment))) {
    return invalid("analysis.validation.invalidIdentifier");
  }
  if (segments.length === 2) {
    return valid(identifier, "github", source);
  }
  if (ecosystem !== "pypi") return invalid("analysis.validation.repositoryRequired");
  return valid(identifier, "pypi", source);
}

function decodePathSegment(segment) {
  try {
    return decodeURIComponent(segment);
  } catch {
    return null;
  }
}

function parseUrl(input) {
  if (!/^[A-Za-z][A-Za-z\d+.-]*:\/\//.test(input) &&
      !/^(?:www\.)?(?:pypi\.org|github\.com)(?:\/|$)/i.test(input)) {
    if (HOST_LIKE_PREFIX.test(input)) return invalid("analysis.validation.unsupportedHost");
    return null;
  }

  let url;
  try {
    url = new URL(input.includes("://") ? input : `https://${input}`);
  } catch {
    return invalid("analysis.validation.invalidUrl");
  }
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.port) {
    return invalid("analysis.validation.invalidUrl");
  }
  if (url.search || url.hash) return invalid("analysis.validation.invalidUrl");

  const host = url.hostname.toLowerCase();
  const rawParts = url.pathname.split("/").slice(1);
  if (rawParts.at(-1) === "") rawParts.pop();
  if (rawParts.some((part) => !part)) return invalid("analysis.validation.invalidUrl");
  const parts = rawParts.map(decodePathSegment);
  if (parts.some((part) => part === null)) return invalid("analysis.validation.invalidUrl");

  if (["pypi.org", "www.pypi.org"].includes(host)) {
    if (parts.length !== 2 || parts[0].toLowerCase() !== "project") {
      return invalid("analysis.validation.invalidPyPiUrl");
    }
    return validateIdentifier(parts[1], "pypi", "pypi-url");
  }
  if (["github.com", "www.github.com"].includes(host)) {
    if (parts.length !== 2) return invalid("analysis.validation.invalidGitHubUrl");
    const repository = parts[1].endsWith(".git") ? parts[1].slice(0, -4) : parts[1];
    return validateIdentifier(`${parts[0]}/${repository}`, "github", "github-url");
  }
  return invalid("analysis.validation.unsupportedHost");
}

export function parseAnalysisInput(value, selectedEcosystem = "pypi") {
  const input = String(value ?? "").trim();
  if (!input) return invalid("analysis.validation.required");

  const parsedUrl = parseUrl(input);
  if (parsedUrl) return parsedUrl;
  return validateIdentifier(input, selectedEcosystem === "github" ? "github" : "pypi", "identifier");
}
