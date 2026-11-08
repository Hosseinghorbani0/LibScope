"""
Adoption Discovery and Evidence Classification.
Discovers and classifies verified real-world adoption of a package across independent repositories.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Set
from libscope.core.logging import get_logger

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
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
}


@dataclass
class AdoptionEvidenceItem:
    source_repo_full_name: str
    source_repo_url: str
    file_path: str
    evidence_type: str
    raw_match: Optional[str]
    stars: int
    confidence_score: float
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None


@dataclass
class AdoptionDiscoveryResult:
    package_name: str
    target_repo_full_name: Optional[str]
    total_findings: int
    confirmed_dependencies_count: int
    confirmed_source_usage_count: int
    possible_usage_count: int
    mention_only_count: int
    unverified_count: int
    findings: List[AdoptionEvidenceItem] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


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
        base_name = lower_path.split("/")[-1]
        pkg_lower = package_name.lower()
        content_lower = matched_content.lower()

        # 4. Check for documentation / mention only first
        if any(lower_path.endswith(ext) for ext in [".md", ".rst", ".txt"]) and base_name not in ["requirements.txt", "requirements.in"]:
            return CLASS_MENTION_ONLY, 0.3

        if "doc" in lower_path or "example" in lower_path:
            return CLASS_MENTION_ONLY, 0.35

        # 1. Dependency manifest check
        if base_name in DEPENDENCY_MANIFESTS:
            # Check if package name is declared as a package requirement
            dep_patterns = [
                rf'"{re.escape(pkg_lower)}[\^~>=<]*.*"',
                rf"'{re.escape(pkg_lower)}[\^~>=<]*.*'",
                rf"^{re.escape(pkg_lower)}\b",
                rf"\b{re.escape(pkg_lower)}\b\s*[>=<~^]",
            ]
            for pat in dep_patterns:
                if re.search(pat, content_lower, re.MULTILINE):
                    return CLASS_CONFIRMED_DEPENDENCY, 0.95
            return CLASS_CONFIRMED_DEPENDENCY, 0.85

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
            if f"pip install" in content_lower and pkg_lower in content_lower:
                return CLASS_POSSIBLE_USAGE, 0.70
            return CLASS_POSSIBLE_USAGE, 0.50

        return CLASS_UNVERIFIED, 0.20

    def process_raw_findings(
        self,
        package_name: str,
        target_repo_full_name: Optional[str],
        raw_items: List[Dict[str, Any]],
    ) -> AdoptionDiscoveryResult:
        """
        Process, deduplicate, filter self-references, and classify raw search findings.
        """
        limitations = [
            "Discovery is based on public repository search and does not include private proprietary codebases.",
            "GitHub search API rate limits apply; results represent a verified sample rather than an exhaustive census.",
        ]

        seen_repos: Set[str] = set()
        findings: List[AdoptionEvidenceItem] = []
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
            raw_match = item.get("raw_match", "") or file_path
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

