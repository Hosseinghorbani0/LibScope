"""
Project Health Analyzer.
Evaluates repository hygiene, documentation quality, CI/CD, tests, license, and maintainer signals.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from libscope.core.logging import get_logger
from libscope.providers.base import NormalizedMetadata, NormalizedRelease, NormalizedRepository

logger = get_logger("analyzer.health")


def normalize_health_rating(rating: str | None = None, findings: list[Any] | None = None) -> str:
    """Map analyzer and persisted finding states to a shared public vocabulary."""
    normalized = (rating or "").strip().lower()
    rating_map = {
        "excellent": "healthy",
        "healthy": "healthy",
        "needs_attention": "warning",
        "warning": "warning",
        "at_risk": "critical",
        "critical": "critical",
        "insufficient_data": "insufficient_data",
        "unknown": "unknown",
    }
    if normalized in rating_map:
        return rating_map[normalized]

    statuses = [
        str(finding.get("status") if isinstance(finding, dict) else getattr(finding, "status", "") or "").lower()
        for finding in findings or []
    ]
    if not statuses:
        return "insufficient_data"
    if any(item == "fail" for item in statuses):
        return "critical"
    if any(item in {"warning", "missing"} for item in statuses):
        return "warning"
    if all(item == "pass" for item in statuses):
        return "healthy"
    return "unknown"


@dataclass
class HealthCheckResult:
    category: str  # documentation, testing, ci, release_discipline, maintenance, license, security_policy
    check_name: str
    status: str  # pass, warning, fail, missing
    message: str
    details: dict[str, Any] | None = None


@dataclass
class ProjectHealthReport:
    package_name: str
    evaluated_at: datetime
    overall_health_rating: str  # "excellent", "healthy", "needs_attention", "at_risk", "insufficient_data"
    findings: list[HealthCheckResult] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


class HealthAnalyzer:
    """Evaluates project engineering hygiene and maintainability."""

    def analyze(
        self,
        metadata: NormalizedMetadata,
        repo: NormalizedRepository | None = None,
        releases: list[NormalizedRelease] | None = None,
        community_profile: dict[str, Any] | None = None,
    ) -> ProjectHealthReport:
        now = datetime.now(UTC)
        findings: list[HealthCheckResult] = []
        missing_info: list[str] = []
        strengths: list[str] = []
        risks: list[str] = []

        # 1. License Check
        license_str = repo.license if repo and repo.license else metadata.license
        if license_str:
            known_open_source = {"mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause", "gpl-3.0", "lgpl-3.0", "mpl-2.0", "isc"}
            clean_lic = license_str.lower().strip()
            if any(k in clean_lic for k in known_open_source):
                findings.append(
                    HealthCheckResult(
                        category="license",
                        check_name="osi_license_detected",
                        status="pass",
                        message=f"Recognized Open Source license declared: {license_str}",
                    )
                )
                strengths.append(f"Standard open source license ({license_str})")
            else:
                findings.append(
                    HealthCheckResult(
                        category="license",
                        check_name="custom_or_unclear_license",
                        status="warning",
                        message=f"License declared but may not be standard OSI identifier: {license_str}",
                    )
                )
        else:
            findings.append(
                HealthCheckResult(
                    category="license",
                    check_name="missing_license",
                    status="fail",
                    message="No software license detected. Adoption carries legal ambiguity.",
                )
            )
            risks.append("No clear license declared")

        # 2. Repository & Community Health (if repository available)
        if repo:
            if repo.is_archived:
                findings.append(
                    HealthCheckResult(
                        category="maintenance",
                        check_name="repository_archival",
                        status="fail",
                        message="Repository has been archived by the maintainers.",
                    )
                )
                risks.append("Project is officially archived")

            # Commit freshness
            if repo.last_commit_at:
                days_since_commit = (now - repo.last_commit_at).days
                if days_since_commit <= 60:
                    findings.append(
                        HealthCheckResult(
                            category="maintenance",
                            check_name="recent_commits",
                            status="pass",
                            message=f"Recent commits observed ({days_since_commit} days ago).",
                        )
                    )
                    strengths.append("Active commit history")
                elif days_since_commit > 365:
                    findings.append(
                        HealthCheckResult(
                            category="maintenance",
                            check_name="dormant_commits",
                            status="fail",
                            message=f"No commits for {days_since_commit} days (> 1 year).",
                        )
                    )
                    risks.append(f"Maintenance stagnant (last commit {days_since_commit} days ago)")
                else:
                    findings.append(
                        HealthCheckResult(
                            category="maintenance",
                            check_name="moderate_commits",
                            status="warning",
                            message=f"Last commit was {days_since_commit} days ago.",
                        )
                    )
            else:
                missing_info.append("Commit history not available via repository API")

            # Community profile (README, Code of Conduct, Contributing, Security)
            files = (community_profile or {}).get("files", {})
            has_readme = bool(files.get("readme"))
            has_contributing = bool(files.get("contributing"))
            has_code_of_conduct = bool(files.get("code_of_conduct"))
            has_security = bool(files.get("security"))

            if has_readme:
                findings.append(
                    HealthCheckResult(
                        category="documentation",
                        check_name="readme_present",
                        status="pass",
                        message="README file is present in repository.",
                    )
                )
            else:
                findings.append(
                    HealthCheckResult(
                        category="documentation",
                        check_name="missing_readme",
                        status="warning",
                        message="README file not found in repository root.",
                    )
                )

            if has_contributing:
                findings.append(
                    HealthCheckResult(
                        category="contribution_guidelines",
                        check_name="contributing_guide_present",
                        status="pass",
                        message="CONTRIBUTING guide is present.",
                    )
                )
                strengths.append("Structured contributor onboarding")
            else:
                findings.append(
                    HealthCheckResult(
                        category="contribution_guidelines",
                        check_name="missing_contributing_guide",
                        status="missing",
                        message="No CONTRIBUTING file found.",
                    )
                )

            if has_security:
                findings.append(
                    HealthCheckResult(
                        category="security_policy",
                        check_name="security_policy_present",
                        status="pass",
                        message="SECURITY.md policy published with vulnerability reporting instructions.",
                    )
                )
                strengths.append("Published security disclosure policy")
            else:
                findings.append(
                    HealthCheckResult(
                        category="security_policy",
                        check_name="missing_security_policy",
                        status="missing",
                        message="No dedicated SECURITY.md policy found.",
                    )
                )

            if has_code_of_conduct:
                findings.append(
                    HealthCheckResult(
                        category="community",
                        check_name="code_of_conduct_present",
                        status="pass",
                        message="Code of Conduct file is present.",
                    )
                )
                strengths.append("Code of Conduct published")
            else:
                findings.append(
                    HealthCheckResult(
                        category="community",
                        check_name="missing_code_of_conduct",
                        status="missing",
                        message="No Code of Conduct file found.",
                    )
                )

        else:
            missing_info.append("No associated public Git repository found for code-level health checks")

        # 3. Release discipline
        if releases:
            yanked_count = sum(1 for r in releases if r.is_yanked)
            total_releases = len(releases)
            findings.append(
                HealthCheckResult(
                    category="release_discipline",
                    check_name="release_history",
                    status="pass" if total_releases >= 3 else "warning",
                    message=f"Project has published {total_releases} releases ({yanked_count} yanked/pre-release).",
                )
            )
            if yanked_count > 0:
                findings.append(
                    HealthCheckResult(
                        category="release_discipline",
                        check_name="yanked_releases",
                        status="warning",
                        message=f"{yanked_count} releases have been yanked or marked pre-release.",
                    )
                )
        else:
            missing_info.append("Release history not available")

        # Overall rating calculation
        fails = sum(1 for f in findings if f.status == "fail")
        warnings_count = sum(1 for f in findings if f.status == "warning")
        passes = sum(1 for f in findings if f.status == "pass")

        if not repo and not releases:
            rating = "insufficient_data"
        elif fails >= 2:
            rating = "at_risk"
        elif fails == 1 or warnings_count >= 3:
            rating = "needs_attention"
        elif passes >= 4 and warnings_count <= 1:
            rating = "excellent"
        else:
            rating = "healthy"

        return ProjectHealthReport(
            package_name=metadata.name,
            evaluated_at=now,
            overall_health_rating=rating,
            findings=findings,
            missing_information=missing_info,
            strengths=strengths,
            risks=risks,
        )
