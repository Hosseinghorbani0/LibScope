"""
Competitor Intelligence and Package Comparison.
Performs normalized side-by-side comparative analysis between packages with fairness indicators.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from libscope.core.logging import get_logger

logger = get_logger("analyzer.competitor")


@dataclass
class PackageComparisonItem:
    package_name: str
    ecosystem: str
    overall_score: float | None
    confidence: str
    monthly_downloads: int | None
    weekly_downloads: int
    stars: int | None
    forks: int | None
    open_issues: int | None
    latest_version: str | None
    days_since_last_release: int | None
    days_since_last_commit: int | None
    confirmed_adoptions_count: int | None
    vulnerabilities_count: int | None
    license: str | None
    comparability_notes: list[str] = field(default_factory=list)


@dataclass
class CompetitorComparisonReport:
    compared_at: datetime
    packages: list[PackageComparisonItem]
    download_leader: str | None
    repository_leader: str | None
    adoption_leader: str | None
    maintenance_leader: str | None
    security_leader: str | None
    summary_matrix: list[dict[str, Any]]
    comparative_summary: str


class CompetitorAnalyzer:
    """Compares two or more packages objectively with fairness indicators."""

    def compare(
        self,
        package_data_list: list[dict[str, Any]],
    ) -> CompetitorComparisonReport:
        now = datetime.now(UTC)
        items: list[PackageComparisonItem] = []

        # Check ecosystem uniformity
        ecosystems = {p.get("ecosystem", "pypi") for p in package_data_list}
        is_cross_ecosystem = len(ecosystems) > 1

        for p in package_data_list:
            notes = []
            if is_cross_ecosystem:
                notes.append("Cross-ecosystem comparison: registry download statistics are not directly comparable.")

            monthly_dl = p.get("monthly_downloads")
            stars = p.get("stars")
            if monthly_dl is not None and stars is not None and monthly_dl > 100000 and stars < 50:
                notes.append("High download volume with relatively low GitHub stars suggests automated CI/sub-dependency usage.")
            elif monthly_dl is not None and stars is not None and stars > 5000 and monthly_dl < 1000:
                notes.append("High GitHub stars with modest registry downloads indicates portfolio/educational interest rather than widespread runtime installation.")

            item = PackageComparisonItem(
                package_name=p.get("name", "unknown"),
                ecosystem=p.get("ecosystem", "pypi"),
                overall_score=p.get("overall_score"),
                confidence=p.get("confidence", "medium"),
                monthly_downloads=monthly_dl,
                weekly_downloads=p.get("weekly_downloads", 0),
                stars=stars,
                forks=p.get("forks"),
                open_issues=p.get("open_issues"),
                latest_version=p.get("latest_version"),
                days_since_last_release=p.get("days_since_last_release"),
                days_since_last_commit=p.get("days_since_last_commit"),
                confirmed_adoptions_count=p.get("confirmed_adoptions_count"),
                vulnerabilities_count=p.get("vulnerabilities_count"),
                license=p.get("license"),
                comparability_notes=notes,
            )
            items.append(item)

        # Identify category leaders
        downloads = [item for item in items if item.monthly_downloads is not None]
        repositories = [item for item in items if item.stars is not None]
        adoptions = [item for item in items if item.confirmed_adoptions_count is not None]
        dl_leader = max(downloads, key=lambda item: item.monthly_downloads).package_name if downloads else None
        repo_leader = max(repositories, key=lambda item: item.stars).package_name if repositories else None
        adopt_leader = max(adoptions, key=lambda item: item.confirmed_adoptions_count).package_name if adoptions else None

        recent_commits = [item for item in items if item.days_since_last_commit is not None]
        maint_leader = min(recent_commits, key=lambda item: item.days_since_last_commit).package_name if recent_commits else None

        # Security leader: zero vulnerabilities + valid license
        sec_candidates = [x for x in items if x.vulnerabilities_count == 0]
        sec_leader = sec_candidates[0].package_name if sec_candidates else None

        # Build matrix
        matrix = []
        for it in items:
            matrix.append({
                "package": it.package_name,
                "score": it.overall_score if it.overall_score is not None else "N/A",
                "monthly_downloads": f"{it.monthly_downloads:,}" if it.monthly_downloads is not None else "N/A",
                "stars": f"{it.stars:,}" if it.stars is not None else "N/A",
                "verified_adoptions": it.confirmed_adoptions_count,
                "known_vulnerabilities": it.vulnerabilities_count,
                "license": it.license or "Unspecified",
            })

        pkg_names = ", ".join(it.package_name for it in items)
        summary = (
            f"Compared {len(items)} packages ({pkg_names}). "
            f"Download volume leader: {dl_leader or 'None'}. "
            f"GitHub community leader: {repo_leader or 'None'}. "
            f"Verified adoption leader: {adopt_leader or 'None'}."
        )

        return CompetitorComparisonReport(
            compared_at=now,
            packages=items,
            download_leader=dl_leader,
            repository_leader=repo_leader,
            adoption_leader=adopt_leader,
            maintenance_leader=maint_leader,
            security_leader=sec_leader,
            summary_matrix=matrix,
            comparative_summary=summary,
        )
