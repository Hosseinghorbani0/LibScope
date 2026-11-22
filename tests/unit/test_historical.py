from datetime import UTC, datetime, timedelta

from libscope.analyzers.historical import HistoricalAnalyzer


def test_historical_analysis_does_not_infer_zero_download_delta_from_missing_data():
    now = datetime.now(UTC)
    result = HistoricalAnalyzer().analyze_snapshots(
        "example",
        [
            {"recorded_at": now - timedelta(days=1), "downloads_count": 120},
            {"recorded_at": now, "downloads_count": None},
        ],
    )

    assert result.deltas == []
    assert result.historical_chart_points[-1]["downloads"] is None
    assert "lacks verified download data" in result.summary
