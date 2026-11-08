"""
Unit tests for Download Analytics, moving averages, and anomaly detection.
"""
from datetime import datetime, timezone
from libscope.analyzers.downloads import DownloadsAnalyzer
from libscope.providers.base import NormalizedDownloads, NormalizedRelease


def test_downloads_analyzer_handles_missing_data():
    analyzer = DownloadsAnalyzer()
    empty_dl = NormalizedDownloads(
        package_name="test-pkg",
        ecosystem="pypi",
        daily=0,
        weekly=0,
        monthly=0,
        historical={},
    )
    res = analyzer.analyze(empty_dl)
    assert res.is_missing_data is True
    assert res.recent_trend_direction == "insufficient_data"
    assert res.moving_average_7d is None


def test_downloads_analyzer_detects_spikes_and_moving_averages():
    analyzer = DownloadsAnalyzer()

    # 20 days of baseline 1,000 downloads, then a massive 20,000 spike
    historical = {f"2026-01-{i:02d}": 1000 for i in range(1, 20)}
    historical["2026-01-20"] = 25000

    dl = NormalizedDownloads(
        package_name="spiky-pkg",
        ecosystem="pypi",
        daily=25000,
        weekly=31000,
        monthly=44000,
        historical=historical,
    )

    releases = [
        NormalizedRelease(
            version="1.2.0",
            release_date=datetime(2026, 1, 20, tzinfo=timezone.utc),
        )
    ]

    res = analyzer.analyze(dl, releases)
    assert res.is_missing_data is False
    assert res.moving_average_7d is not None
    assert len(res.anomalies) > 0
    assert any(a.anomaly_type == "spike" and a.date == "2026-01-20" for a in res.anomalies)
    assert len(res.release_impact) > 0

