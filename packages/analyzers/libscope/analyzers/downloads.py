"""
Downloads and Package Trend Analytics.
Calculates moving averages, growth rates, spike detection, and release correlation.
"""
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from libscope.core.logging import get_logger
from libscope.providers.base import NormalizedDownloads, NormalizedRelease

logger = get_logger("analyzer.downloads")


@dataclass
class AnomalyDetection:
    date: str
    downloads: int
    mean: float
    std_dev: float
    anomaly_type: str  # "spike" or "drop"
    magnitude_z_score: float
    message: str


@dataclass
class DownloadAnalyticsResult:
    package_name: str
    ecosystem: str
    recorded_at: datetime
    daily_downloads: int
    weekly_downloads: int
    monthly_downloads: int
    is_missing_data: bool
    mirror_inclusive: bool
    growth_rate_pct: float | None  # e.g. weekly growth
    moving_average_7d: float | None
    moving_average_30d: float | None
    anomalies: list[AnomalyDetection] = field(default_factory=list)
    recent_trend_direction: str = "stable"  # "growing", "stable", "declining", "insufficient_data"
    release_impact: list[dict[str, Any]] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


class DownloadsAnalyzer:
    """Performs statistical analytics on package download counts."""

    def analyze(
        self,
        downloads: NormalizedDownloads,
        releases: list[NormalizedRelease] | None = None,
    ) -> DownloadAnalyticsResult:
        now = datetime.now(UTC)
        caveats = [
            "Downloads reflect automated CI/CD mirrors, bots, and repeated installations; they do not equal unique active users."
        ]
        if downloads.mirror_inclusive:
            caveats.append("Metrics may include automated mirror synchronizations.")

        is_missing = downloads.monthly == 0 and not downloads.historical
        if is_missing:
            caveats.append("No historical download records available from registry.")
            return DownloadAnalyticsResult(
                package_name=downloads.package_name,
                ecosystem=downloads.ecosystem,
                recorded_at=now,
                daily_downloads=0,
                weekly_downloads=0,
                monthly_downloads=0,
                is_missing_data=True,
                mirror_inclusive=downloads.mirror_inclusive,
                growth_rate_pct=None,
                moving_average_7d=None,
                moving_average_30d=None,
                recent_trend_direction="insufficient_data",
                caveats=caveats,
            )

        # Sort historical records by date
        sorted_dates = sorted(downloads.historical.keys())
        values = [downloads.historical[d] for d in sorted_dates]

        # Moving averages
        ma7 = None
        ma30 = None
        if len(values) >= 7:
            ma7 = round(sum(values[-7:]) / 7.0, 2)
        if len(values) >= 30:
            ma30 = round(sum(values[-30:]) / 30.0, 2)
        elif values:
            ma30 = round(sum(values) / float(len(values)), 2)

        # Growth rate (comparing latest 7 days vs previous 7 days)
        growth_rate = None
        trend = "stable"
        if len(values) >= 14:
            recent_7 = sum(values[-7:])
            prev_7 = sum(values[-14:-7])
            if prev_7 > 0:
                growth_rate = round(((recent_7 - prev_7) / float(prev_7)) * 100.0, 2)
                if growth_rate > 15.0:
                    trend = "growing"
                elif growth_rate < -15.0:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                growth_rate = 100.0 if recent_7 > 0 else 0.0
                trend = "growing" if recent_7 > 0 else "stable"
        elif downloads.weekly > 0:
            # Estimate from monthly / weekly if detailed history is brief
            weekly_equiv = downloads.monthly / 4.0
            if weekly_equiv > 0:
                est_growth = round(((downloads.weekly - weekly_equiv) / weekly_equiv) * 100.0, 2)
                growth_rate = est_growth

        # Anomaly detection (Z-score on daily observations, threshold 2.5 std devs)
        anomalies: list[AnomalyDetection] = []
        if len(values) >= 14:
            mean_val = sum(values) / float(len(values))
            variance = sum((x - mean_val) ** 2 for x in values) / float(len(values))
            std_dev = math.sqrt(variance)

            if std_dev > 0.0:
                for d, val in zip(sorted_dates, values, strict=False):
                    z = (val - mean_val) / std_dev
                    if z > 2.5:
                        anomalies.append(
                            AnomalyDetection(
                                date=d,
                                downloads=val,
                                mean=round(mean_val, 1),
                                std_dev=round(std_dev, 1),
                                anomaly_type="spike",
                                magnitude_z_score=round(z, 2),
                                message=f"Sudden download spike ({val:,} downloads, +{round(z, 1)}σ)",
                            )
                        )
                    elif z < -2.5 and val < mean_val * 0.2:
                        anomalies.append(
                            AnomalyDetection(
                                date=d,
                                downloads=val,
                                mean=round(mean_val, 1),
                                std_dev=round(std_dev, 1),
                                anomaly_type="drop",
                                magnitude_z_score=round(z, 2),
                                message=f"Sudden download drop ({val:,} downloads, {round(z, 1)}σ)",
                            )
                        )

        # Release impact analysis
        release_impact = []
        if releases and downloads.historical:
            for rel in releases[:5]:
                if rel.release_date:
                    rel_date_str = rel.release_date.strftime("%Y-%m-%d")
                    # Check downloads 3 days before and 3 days after release
                    before_vals = [downloads.historical[d] for d in sorted_dates if d < rel_date_str][-3:]
                    after_vals = [downloads.historical[d] for d in sorted_dates if d >= rel_date_str][:3]
                    if before_vals and after_vals:
                        avg_before = sum(before_vals) / float(len(before_vals))
                        avg_after = sum(after_vals) / float(len(after_vals))
                        delta_pct = round(((avg_after - avg_before) / max(1.0, avg_before)) * 100.0, 1)
                        release_impact.append({
                            "version": rel.version,
                            "release_date": rel_date_str,
                            "avg_3d_before": round(avg_before, 1),
                            "avg_3d_after": round(avg_after, 1),
                            "post_release_change_pct": delta_pct,
                        })

        return DownloadAnalyticsResult(
            package_name=downloads.package_name,
            ecosystem=downloads.ecosystem,
            recorded_at=now,
            daily_downloads=downloads.daily,
            weekly_downloads=downloads.weekly,
            monthly_downloads=downloads.monthly,
            is_missing_data=False,
            mirror_inclusive=downloads.mirror_inclusive,
            growth_rate_pct=growth_rate,
            moving_average_7d=ma7,
            moving_average_30d=ma30,
            anomalies=anomalies,
            recent_trend_direction=trend,
            release_impact=release_impact,
            caveats=caveats,
        )

