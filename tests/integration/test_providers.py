"""
Integration tests for Provider adapters with mocked HTTP services.
"""
import asyncio
import json
import httpx
from libscope.providers.pypi import PyPIProvider


def test_pypi_provider_normalization():
    mock_pypi_json = {
        "info": {
            "name": "sample-pkg",
            "version": "2.4.1",
            "summary": "Sample Python Library",
            "home_page": "https://sample.org",
            "project_urls": {
                "Source": "https://github.com/sample-owner/sample-pkg.git"
            },
            "license": "Apache-2.0",
        },
        "releases": {
            "2.4.1": [
                {
                    "upload_time_iso_8601": "2026-01-15T12:00:00Z",
                    "url": "https://files.pythonhosted.org/sample.whl",
                    "digests": {"sha256": "abc123sha256"},
                }
            ]
        },
    }

    class MockAsyncClient:
        is_closed = False

        async def get(self, url, *args, **kwargs):
            url_str = str(url)
            req = httpx.Request("GET", url_str)
            if "pypi.org" in url_str:
                return httpx.Response(200, request=req, text=json.dumps(mock_pypi_json))
            elif "recent" in url_str:
                return httpx.Response(200, request=req, text=json.dumps({"data": {"last_day": 100, "last_week": 700, "last_month": 3000}}))
            elif "overall" in url_str:
                return httpx.Response(200, request=req, text=json.dumps({"data": [{"category": "without_mirrors", "date": "2026-01-01", "downloads": 50}]}))
            return httpx.Response(404, request=req, text=json.dumps({"detail": "Not found"}))

    async def _run():
        provider = PyPIProvider(client=MockAsyncClient())
        meta = await provider.fetch_metadata("sample-pkg")
        assert meta.name == "sample-pkg"
        assert meta.repository_url == "https://github.com/sample-owner/sample-pkg"
        assert meta.latest_version == "2.4.1"

        releases = await provider.fetch_releases("sample-pkg")
        assert len(releases) == 1
        assert releases[0].version == "2.4.1"

        downloads = await provider.fetch_downloads("sample-pkg")
        assert downloads.monthly == 3000
        assert downloads.daily == 100

    asyncio.run(_run())
