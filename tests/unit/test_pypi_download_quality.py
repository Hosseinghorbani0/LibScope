import asyncio
from datetime import date, timedelta

import httpx
from libscope.analyzers.downloads import DownloadsAnalyzer
from libscope.providers.pypi import PyPIProvider


def _run_provider(responses):
    async def run():
        async def handler(request):
            if request.url.path.endswith("/recent"):
                return httpx.Response(
                    responses.get("recent_status", 200),
                    json=responses.get("recent", {}),
                )
            assert request.url.params.get("mirrors") == "false"
            return httpx.Response(
                responses.get("overall_status", 200),
                json=responses.get("overall", {}),
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            return await PyPIProvider(client=client).fetch_downloads("Example_Package")
        finally:
            await client.aclose()

    return asyncio.run(run())


def test_pypi_downloads_are_mirror_excluded_and_track_source_coverage():
    downloads = _run_provider(
        {
            "recent": {
                "data": {"last_day": 10, "last_week": 70, "last_month": 300},
            },
            "overall": {
                "data": [
                    {"category": "with_mirrors", "date": "2026-11-20", "downloads": 9999},
                    {"category": "without_mirrors", "date": "2026-11-20", "downloads": 8},
                    {"category": "without_mirrors", "date": "2026-11-21", "downloads": 9},
                ],
            },
        }
    )

    assert (downloads.daily, downloads.weekly, downloads.monthly) == (10, 70, 300)
    assert downloads.historical == {"2026-11-20": 8, "2026-11-21": 9}
    assert downloads.mirror_inclusive is False
    assert downloads.data_status == "complete"
    assert downloads.available_periods == ["daily", "weekly", "monthly"]
    assert downloads.observed_days == 2
    assert downloads.latest_observation_date == "2026-11-21"
    assert downloads.provenance.source_name == "pypistats"


def test_pypi_uses_recent_daily_history_as_an_explicit_partial_fallback():
    today = date.today()
    rows = [
        {
            "category": "without_mirrors",
            "date": (today - timedelta(days=offset)).isoformat(),
            "downloads": 2,
        }
        for offset in range(30)
    ]
    downloads = _run_provider(
        {
            "recent_status": 503,
            "overall": {"data": rows},
        }
    )

    assert downloads.daily == 2
    assert downloads.weekly == 14
    assert downloads.monthly == 60
    assert downloads.data_status == "partial"
    assert downloads.is_estimated is True
    assert downloads.available_periods == ["daily", "weekly", "monthly"]
    assert downloads.observed_days == 30


def test_pypi_reports_only_periods_with_sufficient_fallback_coverage():
    today = date.today()
    rows = [
        {
            "category": "without_mirrors",
            "date": (today - timedelta(days=offset)).isoformat(),
            "downloads": 2,
        }
        for offset in range(5)
    ]
    downloads = _run_provider(
        {
            "recent_status": 503,
            "overall": {"data": rows},
        }
    )

    assert downloads.available_periods == ["daily"]
    assert downloads.daily == 2
    assert downloads.weekly == downloads.monthly == 0


def test_unavailable_download_sources_are_not_reported_as_verified_zero():
    downloads = _run_provider(
        {
            "recent_status": 503,
            "overall_status": 503,
        }
    )

    result = DownloadsAnalyzer().analyze(downloads)

    assert downloads.data_status == "unavailable"
    assert result.is_missing_data is True
    assert result.data_status == "unavailable"
    assert result.data_source == "pypistats"
    assert any("could not be verified" in caveat for caveat in result.caveats)


def test_partial_empty_download_sources_are_not_reported_as_verified_zero():
    downloads = _run_provider(
        {
            "recent_status": 503,
            "overall": {"data": []},
        }
    )

    result = DownloadsAnalyzer().analyze(downloads)

    assert result.data_status == "partial"
    assert result.is_missing_data is True
