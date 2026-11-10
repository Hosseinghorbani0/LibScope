import assert from "node:assert/strict";
import test from "node:test";

import { parseAnalysisInput } from "../../apps/api/libscope/api/dashboard_static/analysis-input.js";

test("accepts a PyPI project identifier", () => {
  assert.deepEqual(parseAnalysisInput(" requests "), {
    valid: true,
    identifier: "requests",
    ecosystem: "pypi",
    source: "identifier",
  });
});

test("normalizes a direct PyPI project URL", () => {
  assert.deepEqual(parseAnalysisInput("https://pypi.org/project/Requests/"), {
    valid: true,
    identifier: "Requests",
    ecosystem: "pypi",
    source: "pypi-url",
  });
});

test("normalizes a direct GitHub repository URL", () => {
  assert.deepEqual(parseAnalysisInput("https://github.com/psf/requests.git"), {
    valid: true,
    identifier: "psf/requests",
    ecosystem: "github",
    source: "github-url",
  });
});

test("treats owner/repository identifiers as GitHub regardless of the select value", () => {
  assert.deepEqual(parseAnalysisInput("psf/requests", "pypi"), {
    valid: true,
    identifier: "psf/requests",
    ecosystem: "github",
    source: "identifier",
  });
});

test("rejects unsupported hosts and malformed URLs", () => {
  assert.equal(parseAnalysisInput("https://example.com/requests").reason, "analysis.validation.unsupportedHost");
  assert.equal(parseAnalysisInput("https://pypi.org/project/requests/json").reason, "analysis.validation.invalidPyPiUrl");
  assert.equal(parseAnalysisInput("https://github.com/psf").reason, "analysis.validation.invalidGitHubUrl");
  assert.equal(parseAnalysisInput("github.com/psf/requests?tab=readme").reason, "analysis.validation.invalidUrl");
  assert.equal(parseAnalysisInput("https://github.com//psf/requests").reason, "analysis.validation.invalidUrl");
  assert.equal(parseAnalysisInput("https://github.com/psf%2Fteam/requests").reason, "analysis.validation.invalidIdentifier");
  assert.equal(parseAnalysisInput("https://github.com.evil.test/psf/requests").reason, "analysis.validation.unsupportedHost");
});

test("requires a repository identifier for the GitHub ecosystem", () => {
  assert.equal(parseAnalysisInput("requests", "github").reason, "analysis.validation.repositoryRequired");
});
