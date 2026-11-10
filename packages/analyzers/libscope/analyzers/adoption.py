"""
Adoption Discovery and Evidence Classification.
Discovers and classifies verified real-world adoption of a package across independent repositories.
"""
import configparser
import json
import re
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from libscope.core.logging import get_logger
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

logger = get_logger("analyzer.adoption")

# The 5 strict evidence classifications required by LibScope specification:
CLASS_CONFIRMED_DEPENDENCY = "Confirmed dependency declaration"
CLASS_CONFIRMED_USAGE = "Confirmed source-code usage"
CLASS_POSSIBLE_USAGE = "Possible usage"
CLASS_MENTION_ONLY = "Mention only"
CLASS_UNVERIFIED = "Unverified"

# Standard dependency manifest patterns
DEPENDENCY_MANIFESTS = {
    "requirements.txt",
    "requirements.in",
    "pyproject.toml",
    "setup.cfg",
    "pipfile",
    "package.json",
}
UNSUPPORTED_MANIFESTS = {"setup.py", "cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts"}
MAX_MANIFEST_SIZE = 1_000_000


def _requirement_matches(specifier: str, package_name: str) -> bool:
    line = specifier.strip()
    if not line or line.startswith(("#", "-")):
        return False
    try:
        return canonicalize_name(Requirement(line).name) == canonicalize_name(package_name)
    except InvalidRequirement:
        return False


def _is_declared_in_manifest(file_path: str, content: str, package_name: str) -> bool | None:
    """Return None when the manifest format is malformed."""
    manifest = PurePosixPath(file_path).name.lower()

    if manifest.startswith("requirements") and manifest.endswith((".txt", ".in")):
        return any(_requirement_matches(line.split(" #", 1)[0], package_name) for line in content.splitlines())

    if manifest == "pyproject.toml":
        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError:
            return None

        candidates: list[str] = []
        project = data.get("project", {})
        if isinstance(project, dict):
            candidates.extend(item for item in project.get("dependencies", []) if isinstance(item, str))
            optional = project.get("optional-dependencies", {})
            if isinstance(optional, dict):
                candidates.extend(
                    item
                    for values in optional.values()
                    if isinstance(values, list)
                    for item in values
                    if isinstance(item, str)
                )
        build_system = data.get("build-system", {})
        if isinstance(build_system, dict):
            candidates.extend(item for item in build_system.get("requires", []) if isinstance(item, str))

        tool = data.get("tool", {})
        if isinstance(tool, dict):
            poetry = tool.get("poetry", {})
            if isinstance(poetry, dict):
                dependencies = poetry.get("dependencies", {})
                if isinstance(dependencies, dict):
                    candidates.extend(dependencies)
                groups = poetry.get("group", {})
                if isinstance(groups, dict):
                    for group in groups.values():
                        if isinstance(group, dict) and isinstance(group.get("dependencies"), dict):
                            candidates.extend(group["dependencies"])
            pdm = tool.get("pdm", {})
            if isinstance(pdm, dict):
                for section in ("dependencies", "dev-dependencies"):
                    values = pdm.get(section, {})
                    if isinstance(values, dict):
                        candidates.extend(values)

        dependency_groups = data.get("dependency-groups", {})
        if isinstance(dependency_groups, dict):
            candidates.extend(
                item
                for values in dependency_groups.values()
                if isinstance(values, list)
                for item in values
                if isinstance(item, str)
            )
        return any(_requirement_matches(item, package_name) for item in candidates)

    if manifest == "setup.cfg":
        parser = configparser.ConfigParser()
        try:
            parser.read_string(content)
        except configparser.Error:
            return None
        candidates = []
        if parser.has_option("options", "install_requires"):
            candidates.extend(parser.get("options", "install_requires").splitlines())
        if parser.has_section("options.extras_require"):
            for value in parser["options.extras_require"].values():
                candidates.extend(value.splitlines())
        return any(_requirement_matches(item, package_name) for item in candidates)

    if manifest == "pipfile":
        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError:
            return None
        candidates = [
            name
            for section in ("packages", "dev-packages")
            for name in data.get(section, {})
            if isinstance(data.get(section), dict)
        ]
        return any(canonicalize_name(item) == canonicalize_name(package_name) for item in candidates)

    if manifest == "package.json":
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        candidates = [
            name
            for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
            for name in data.get(section, {})
            if isinstance(data.get(section), dict)
        ]
        return package_name.strip().lower() in candidates

    return None


@dataclass
class AdoptionEvidenceItem:
    source_repo_full_name: str
    source_repo_url: str
    file_path: str
    evidence_type: str
    raw_match: str | None
    stars: int
    confidence_score: float
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None


@dataclass
class AdoptionDiscoveryResult:
    package_name: str
    target_repo_full_name: str | None
    total_findings: int
    confirmed_dependencies_count: int
    confirmed_source_usage_count: int
    possible_usage_count: int
    mention_only_count: int
    unverified_count: int
    findings: list[AdoptionEvidenceItem] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class AdoptionAnalyzer:
    """Discovers, validates, and classifies adoption evidence."""

    def classify_evidence(
        self,
        file_path: str,
        matched_content: str,
        package_name: str,
    ) -> tuple[str, float]:
        """
        Classify raw search hit into one of the 5 canonical evidence classes:
        1. Confirmed dependency declaration (requirements.txt, pyproject.toml dependencies, setup.py install_requires)
        2. Confirmed source-code usage (import package_name, from package_name import ...)
        3. Possible usage (config file reference, dockerfile run install)
        4. Mention only (readme.md, changelog, comments, docs)
        5. Unverified (unrecognized files or ambiguous strings)
        """
        lower_path = file_path.lower()
        base_name = PurePosixPath(lower_path).name
        pkg_lower = package_name.lower()
        content_lower = matched_content.lower()
        is_requirements = base_name.startswith("requirements") and base_name.endswith((".txt", ".in"))

        # 4. Check for documentation / mention only first
        if any(lower_path.endswith(ext) for ext in [".md", ".rst", ".txt"]) and not is_requirements:
            return CLASS_MENTION_ONLY, 0.3

        if "doc" in lower_path or "example" in lower_path:
            return CLASS_MENTION_ONLY, 0.35

        if base_name in UNSUPPORTED_MANIFESTS:
            return CLASS_UNVERIFIED, 0.0

        # 1. Dependency manifest check
        if base_name in DEPENDENCY_MANIFESTS or is_requirements:
            if len(matched_content.encode("utf-8")) > MAX_MANIFEST_SIZE:
                return CLASS_UNVERIFIED, 0.0
            declared = _is_declared_in_manifest(file_path, matched_content, package_name)
            if declared:
                return CLASS_CONFIRMED_DEPENDENCY, 0.99
            return CLASS_UNVERIFIED, 0.0

        # 2. Source code usage (Python, JS, TS, etc.)
        if lower_path.endswith((".py", ".pyw")):
            import_patterns = [
                rf"^\s*import\s+{re.escape(pkg_lower)}\b",
                rf"^\s*from\s+{re.escape(pkg_lower)}(\.[a-zA-Z0-9_]+)?\s+import\b",
            ]
            for pat in import_patterns:
                if re.search(pat, content_lower, re.MULTILINE):
                    return CLASS_CONFIRMED_USAGE, 0.90
            return CLASS_POSSIBLE_USAGE, 0.60

        # Dockerfile or CI configs
        if "dockerfile" in base_name or ".github/workflows" in lower_path:
            if "pip install" in content_lower and pkg_lower in content_lower:
                return CLASS_POSSIBLE_USAGE, 0.70
            return CLASS_POSSIBLE_USAGE, 0.50

        return CLASS_UNVERIFIED, 0.20

    def process_raw_findings(
        self,
        package_name: str,
        target_repo_full_name: str | None,
        raw_items: list[dict[str, Any]],
    ) -> AdoptionDiscoveryResult:
        """
        Process, deduplicate, filter self-references, and classify raw search findings.
        """
        limitations = [
            "Discovery is based on public repository search and does not include private proprietary codebases.",
            "GitHub search API rate limits apply; results represent a verified sample rather than an exhaustive census.",
        ]

        seen_repos: set[str] = set()
        findings: list[AdoptionEvidenceItem] = []
        normalized_target = (target_repo_full_name or "").lower().strip()

        for item in raw_items:
            repo_full_name = item.get("repo_full_name", "")
            if not repo_full_name:
                continue

            # RULE: Do NOT count the package's own repository as independent adoption!
            if normalized_target and repo_full_name.lower().strip() == normalized_target:
                continue

            # Deduplicate by (repo_full_name, file_path)
            dedup_key = f"{repo_full_name}:{item.get('file_path', '')}"
            if dedup_key in seen_repos:
                continue
            seen_repos.add(dedup_key)

            file_path = item.get("file_path", "")
            raw_match = item.get("raw_match", "") or ""
            fetch_status = item.get("fetch_status", "available" if raw_match else "unavailable")
            if fetch_status != "available" or not raw_match:
                limitations.append(
                    f"Manifest content for {repo_full_name}/{file_path} could not be verified ({fetch_status})."
                )
                continue
            stars = int(item.get("stars", 0))

            evidence_type, confidence = self.classify_evidence(file_path, raw_match, package_name)

            findings.append(
                AdoptionEvidenceItem(
                    source_repo_full_name=repo_full_name,
                    source_repo_url=item.get("repo_url", f"https://github.com/{repo_full_name}"),
                    file_path=file_path,
                    evidence_type=evidence_type,
                    raw_match=raw_match[:500] if raw_match else None,
                    stars=stars,
                    confidence_score=confidence,
                )
            )

        # Sort findings: confirmed first, then by repository stars descending
        type_priority = {
            CLASS_CONFIRMED_DEPENDENCY: 1,
            CLASS_CONFIRMED_USAGE: 2,
            CLASS_POSSIBLE_USAGE: 3,
            CLASS_MENTION_ONLY: 4,
            CLASS_UNVERIFIED: 5,
        }
        findings.sort(key=lambda x: (type_priority.get(x.evidence_type, 9), -x.stars))

        # Count classifications
        c_dep = sum(1 for f in findings if f.evidence_type == CLASS_CONFIRMED_DEPENDENCY)
        c_usage = sum(1 for f in findings if f.evidence_type == CLASS_CONFIRMED_USAGE)
        c_possible = sum(1 for f in findings if f.evidence_type == CLASS_POSSIBLE_USAGE)
        c_mention = sum(1 for f in findings if f.evidence_type == CLASS_MENTION_ONLY)
        c_unverified = sum(1 for f in findings if f.evidence_type == CLASS_UNVERIFIED)

        return AdoptionDiscoveryResult(
            package_name=package_name,
            target_repo_full_name=target_repo_full_name,
            total_findings=len(findings),
            confirmed_dependencies_count=c_dep,
            confirmed_source_usage_count=c_usage,
            possible_usage_count=c_possible,
            mention_only_count=c_mention,
            unverified_count=c_unverified,
            findings=findings,
            limitations=limitations,
        )
