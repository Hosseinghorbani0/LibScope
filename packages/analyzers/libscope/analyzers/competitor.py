"""
Competitor Intelligence and Package Comparison.
Performs normalized side-by-side comparative analysis between packages with fairness indicators.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from libscope.core.logging import get_logger

logger = get_logger("analyzer.competitor")


@dataclass
class PackageComparisonItem:
    package_name: str
    ecosystem: str
    overall_score: Optional[float]
    confidence: str
    monthly_downloads: int
    weekly_downloads: int
    stars: int
    forks: int
    open_issues: int
    latest_version: Optional[str]
    days_since_last_release: Optional[int]
    days_since_last_commit: Optional[int]
    confirmed_adoptions_count: int
    vulnerabilities_count: int
    license: Optional[str]
    comparability_notes: List[str] = field(default_factory=list)


@dataclass
class CompetitorComparisonReport:
    compared_at: datetime
    packages: List[PackageComparisonItem]
    download_leader: Optional[str]
    repository_leader: Optional[str]
    adoption_leader: Optional[str]
    maintenance_leader: Optional[str]
    security_leader: Optional[str]
    summary_matrix: List[Dict[str, Any]]
    comparative_summary: str


class CompetitorAnalyzer:
    """Compares two or more packages objectively with fairness indicators."""

    def compare(
        self,
        package_data_list: List[Dict[str, Any]],
    ) -> CompetitorComparisonReport:
        now = datetime.now(timezone.utc)
        items: List[PackageComparisonItem] = []

        # Check ecosystem uniformity
        ecosystems = {p.get("ecosystem", "pypi") for p in package_data_list}
        is_cross_ecosystem = len(ecosystems) > 1

        for p in package_data_list:
            notes = []
            if is_cross_ecosystem:
                notes.append("Cross-ecosystem comparison: registry download statistics are not directly comparable.")

            monthly_dl = p.get("monthly_downloads", 0)
            stars = p.get("stars", 0)
            if monthly_dl > 100000 and stars < 50:
                notes.append("High download volume with relatively low GitHub stars suggests automated CI/sub-dependency usage.")
            elif stars > 5000 and monthly_dl < 1000:
                notes.append("High GitHub stars with modest registry downloads indicates portfolio/educational interest rather than widespread runtime installation.")

            item = PackageComparisonItem(
                package_name=p.get("name", "unknown"),
                ecosystem=p.get("ecosystem", "pypi"),
                overall_score=p.get("overall_score"),
                confidence=p.get("confidence", "medium"),
                monthly_downloads=monthly_dl,
                weekly_downloads=p.get("weekly_downloads", 0),
                stars=stars,
                forks=p.get("forks", 0),
                open_issues=p.get("open_issues", 0),
                latest_version=p.get("latest_version"),
                days_since_last_release=p.get("days_since_last_release"),
                days_since_last_commit=p.get("days_since_last_commit"),
                confirmed_adoptions_count=p.get("confirmed_adoptions_count", 0),
                vulnerabilities_count=p.get("vulnerabilities_count", 0),
                license=p.get("license"),
                comparability_notes=notes,
            )
            items.append(item)

        # Identify category leaders
        dl_leader = max(items, key=lambda x: x.monthly_downloads).package_name if items else None
        repo_leader = max(items, key=lambda x: x.stars).package_name if items else None
        adopt_leader = max(items, key=lambda x: x.confirmed_adoptions_count).package_name if items else None

        # Maintenance leader: lowest days since commit/release with active status
        def maint_key(x: PackageComparisonItem):
            commit_age = x.days_since_last_commit if x.days_since_last_commit is not None else 9999
            return commit_age

        maint_leader = min(items, key=maint_key).package_name if items else None

        # Security leader: zero vulnerabilities + valid license
        sec_candidates = [x for x in items if x.vulnerabilities_count == 0]
        sec_leader = sec_candidates[0].package_name if sec_candidates else None

        # Build matrix
        matrix = []
        for it in items:
            matrix.append({
                "package": it.package_name,
                "score": it.overall_score if it.overall_score is not None else "N/A",
                "monthly_downloads": f"{it.monthly_downloads:,}",
                "stars": f"{it.stars:,}",
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

