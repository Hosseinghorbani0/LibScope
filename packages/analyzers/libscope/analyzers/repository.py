"""
Repository Intelligence Analyzer.
Analyzes commit cadence, release frequency, issues responsiveness, and repository health.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime

from libscope.core.logging import get_logger
from libscope.providers.base import NormalizedRelease, NormalizedRepository

logger = get_logger("analyzer.repository")


@dataclass
class RepositoryIntelligenceResult:
    owner: str
    repo_name: str
    full_name: str
    url: str
    stars: int
    forks: int
    watchers: int
    open_issues: int
    is_archived: bool
    is_fork: bool
    license_spdx: str | None
    days_since_last_commit: int | None
    days_since_last_release: int | None
    release_cadence_days_avg: float | None
    activity_status: str  # "very_active", "active", "stale", "dormant", "archived"
    insights: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class RepositoryAnalyzer:
    """Analyzes public repository metrics and maintainer activity."""

    def analyze(
        self,
        repo: NormalizedRepository,
        releases: list[NormalizedRelease] | None = None,
    ) -> RepositoryIntelligenceResult:
        now = datetime.now(UTC)
        insights: list[str] = []
        warnings: list[str] = []

        # 1. Archival status
        if repo.is_archived:
            warnings.append("Repository is explicitly marked ARCHIVED by its owners. Maintenance has stopped.")
            activity_status = "archived"
        else:
            activity_status = "active"

        # 2. Commit cadence
        days_since_commit = None
        if repo.last_commit_at:
            delta = now - repo.last_commit_at
            days_since_commit = max(0, delta.days)
            if days_since_commit > 365:
                warnings.append(f"No commits in over a year ({days_since_commit} days). Project appears dormant.")
                if not repo.is_archived:
                    activity_status = "dormant"
            elif days_since_commit > 180:
                warnings.append(f"Last commit was {days_since_commit} days ago. Maintenance pace is slow.")
                if not repo.is_archived:
                    activity_status = "stale"
            elif days_since_commit <= 30:
                insights.append(f"Active commit activity within the past month ({days_since_commit} days ago).")
                if not repo.is_archived:
                    activity_status = "very_active"

        # 3. Release cadence
        days_since_release = None
        cadence_avg = None
        if releases and len(releases) >= 2:
            dates = [r.release_date for r in releases if r.release_date]
            dates.sort(reverse=True)
            if dates:
                days_since_release = max(0, (now - dates[0]).days)
            if len(dates) >= 2:
                intervals = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
                intervals = [d for d in intervals if d >= 0]
                if intervals:
                    cadence_avg = round(sum(intervals) / float(len(intervals)), 1)
                    insights.append(f"Average release interval: ~{cadence_avg} days across {len(intervals) + 1} releases.")
        elif repo.last_release_at:
            days_since_release = max(0, (now - repo.last_release_at).days)

        if days_since_release is not None and days_since_release > 365:
            warnings.append(f"Last release was over a year ago ({days_since_release} days ago).")

        # 4. Community metrics & popularity
        if repo.stars >= 1000:
            insights.append(f"High GitHub visibility with {repo.stars:,} stars and {repo.forks:,} forks.")
        elif repo.stars < 10:
            insights.append("Emerging or niche repository with fewer than 10 GitHub stars.")

        # Distinguish stars from adoption
        insights.append("Note: GitHub stars represent bookmarking/interest, not verified production deployment.")

        if repo.is_fork:
            warnings.append("This repository is a fork of another project.")

        return RepositoryIntelligenceResult(
            owner=repo.owner,
            repo_name=repo.repo_name,
            full_name=repo.full_name,
            url=repo.url,
            stars=repo.stars,
            forks=repo.forks,
            watchers=repo.watchers,
            open_issues=repo.open_issues,
            is_archived=repo.is_archived,
            is_fork=repo.is_fork,
            license_spdx=repo.license,
            days_since_last_commit=days_since_commit,
            days_since_last_release=days_since_release,
            release_cadence_days_avg=cadence_avg,
            activity_status=activity_status,
            insights=insights,
            warnings=warnings,
        )

