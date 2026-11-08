"""
Historical Intelligence Analyzer.
Analyzes snapshot deltas across days, weeks, and months, tracking adoption growth and metric changes.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from libscope.core.logging import get_logger

logger = get_logger("analyzer.historical")


@dataclass
class SnapshotDelta:
    period: str  # "since_previous", "7_days", "30_days"
    previous_date: datetime
    current_date: datetime
    downloads_delta: int
    downloads_delta_pct: float | None
    stars_delta: int
    forks_delta: int
    score_delta: float | None
    new_adoptions_count: int
    new_vulnerabilities_count: int


@dataclass
class HistoricalAnalysisResult:
    package_name: str
    analyzed_at: datetime
    total_snapshots_recorded: int
    deltas: list[SnapshotDelta] = field(default_factory=list)
    historical_chart_points: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""


class HistoricalAnalyzer:
    """Computes trends and metric drift across stored historical snapshots."""

    def analyze_snapshots(
        self,
        package_name: str,
        snapshots: list[dict[str, Any]],
        scores: list[dict[str, Any]] | None = None,
    ) -> HistoricalAnalysisResult:
        now = datetime.now(UTC)
        if not snapshots:
            return HistoricalAnalysisResult(
                package_name=package_name,
                analyzed_at=now,
                total_snapshots_recorded=0,
                summary="No previous historical snapshots found. This is the baseline collection.",
            )

        # Sort snapshots chronologically
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("recorded_at", datetime.min))
        chart_points = []
        for s in sorted_snaps:
            chart_points.append({
                "date": s.get("recorded_at").strftime("%Y-%m-%d") if isinstance(s.get("recorded_at"), datetime) else str(s.get("recorded_at")),
                "downloads": s.get("downloads_count", 0),
                "stars": s.get("stars_count", 0),
                "forks": s.get("forks_count", 0),
            })

        deltas: list[SnapshotDelta] = []
        if len(sorted_snaps) >= 2:
            latest = sorted_snaps[-1]
            prev = sorted_snaps[-2]

            prev_dl = prev.get("downloads_count", 0)
            curr_dl = latest.get("downloads_count", 0)
            dl_delta = curr_dl - prev_dl
            dl_delta_pct = round((dl_delta / max(1, prev_dl)) * 100.0, 2) if prev_dl > 0 else None

            stars_delta = (latest.get("stars_count") or 0) - (prev.get("stars_count") or 0)
            forks_delta = (latest.get("forks_count") or 0) - (prev.get("forks_count") or 0)

            deltas.append(
                SnapshotDelta(
                    period="since_previous",
                    previous_date=prev.get("recorded_at", now),
                    current_date=latest.get("recorded_at", now),
                    downloads_delta=dl_delta,
                    downloads_delta_pct=dl_delta_pct,
                    stars_delta=stars_delta,
                    forks_delta=forks_delta,
                    score_delta=None,
                    new_adoptions_count=0,
                    new_vulnerabilities_count=0,
                )
            )

        summary = f"Recorded {len(sorted_snaps)} snapshots over time for {package_name}."
        if deltas:
            d = deltas[0]
            summary += f" Recent delta: {d.downloads_delta:+d} downloads, {d.stars_delta:+d} stars."

        return HistoricalAnalysisResult(
            package_name=package_name,
            analyzed_at=now,
            total_snapshots_recorded=len(sorted_snaps),
            deltas=deltas,
            historical_chart_points=chart_points,
            summary=summary,
        )

