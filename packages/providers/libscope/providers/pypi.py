"""
PyPI Package Provider implementation.
Queries PyPI JSON API and pypistats API.
"""
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx
from libscope.core.logging import get_logger
from libscope.core.security import create_safe_httpx_client
from libscope.providers.base import (
    BaseProvider,
    DataProvenance,
    NormalizedDownloads,
    NormalizedMetadata,
    NormalizedRelease,
    PackageIdentity,
)

logger = get_logger("provider.pypi")


class PyPIProvider(BaseProvider):
    """Ecosystem provider for Python Package Index (PyPI)."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    @property
    def name(self) -> str:
        return "pypi"

    @property
    def supported_ecosystems(self) -> list[str]:
        return ["pypi", "python"]

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "metadata": True,
            "releases": True,
            "downloads": True,
            "dependencies": True,
            "repository_url_extraction": True,
            "repository_direct_metrics": False,  # PyPI does not host git repos
            "issue_tracking": False,             # Handled by repository provider
            "code_search": False,                # Handled by code host provider
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = create_safe_httpx_client()
        return self._client

    def _extract_github_url(self, info: dict[str, Any]) -> str | None:
        """Extract GitHub repository URL from project_urls or home_page."""
        urls: list[str] = []
        if info.get("home_page"):
            urls.append(info["home_page"])

        project_urls = info.get("project_urls") or {}
        for _key, val in project_urls.items():
            if val:
                urls.append(val)

        github_pattern = re.compile(r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/.*)?")
        for candidate in urls:
            match = github_pattern.match(candidate.strip())
            if match:
                owner, repo = match.group(1), match.group(2)
                # Strip trailing .git
                if repo.endswith(".git"):
                    repo = repo[:-4]
                return f"https://github.com/{owner}/{repo}"

        return None

    async def resolve_identity(self, name_or_query: str) -> PackageIdentity:
        name = name_or_query.strip().lower()
        metadata = await self.fetch_metadata(name)
        return PackageIdentity(
            name=name,
            ecosystem="pypi",
            canonical_name=metadata.name,
            homepage=metadata.homepage,
            repository_url=metadata.repository_url,
            provenance=metadata.provenance,
        )

    async def fetch_metadata(self, name: str) -> NormalizedMetadata:
        clean_name = name.strip().lower()
        url = f"https://pypi.org/pypi/{clean_name}/json"
        client = await self._get_client()

        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                raise ValueError(f"Package '{clean_name}' not found on PyPI")
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError(f"Package '{clean_name}' not found on PyPI") from exc
            logger.error(f"PyPI API HTTP error for {clean_name}: {exc}")
            raise RuntimeError(f"PyPI API error: {exc.response.status_code}") from exc
        except Exception as exc:
            logger.error(f"Failed to query PyPI for {clean_name}: {exc}")
            raise

        info = data.get("info", {})
        repo_url = self._extract_github_url(info)

        return NormalizedMetadata(
            name=info.get("name", clean_name),
            ecosystem="pypi",
            description=info.get("summary"),
            homepage=info.get("home_page"),
            repository_url=repo_url,
            license=info.get("license"),
            latest_version=info.get("version"),
            author=info.get("author") or info.get("author_email"),
            keywords=info.get("keywords", "").split(",") if isinstance(info.get("keywords"), str) else [],
            project_urls=info.get("project_urls") or {},
            provenance=DataProvenance(
                source_name="pypi_registry",
                url_accessed=url,
                notes="Collected from PyPI JSON API endpoint",
            ),
        )

    async def fetch_releases(self, name: str) -> list[NormalizedRelease]:
        clean_name = name.strip().lower()
        url = f"https://pypi.org/pypi/{clean_name}/json"
        client = await self._get_client()

        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning(f"Could not fetch releases from PyPI for {clean_name}: {exc}")
            return []

        raw_releases = data.get("releases", {})
        results: list[NormalizedRelease] = []

        for ver, dists in raw_releases.items():
            release_date = None
            is_yanked = False
            download_url = None
            sha256 = None

            if dists and isinstance(dists, list):
                # Pick the latest or wheel/sdist distribution
                dist = dists[0]
                upload_time = dist.get("upload_time_iso_8601") or dist.get("upload_time")
                if upload_time:
                    try:
                        # Normalize ISO timestamp
                        release_date = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                    except Exception:
                        pass
                is_yanked = bool(dist.get("yanked", False))
                download_url = dist.get("url")
                digests = dist.get("digests") or {}
                sha256 = digests.get("sha256")

            results.append(
                NormalizedRelease(
                    version=ver,
                    release_date=release_date,
                    is_yanked=is_yanked,
                    download_url=download_url,
                    sha256=sha256,
                )
            )

        # Sort chronologically if dates exist, newest first
        results.sort(
            key=lambda r: r.release_date or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        return results

    async def fetch_downloads(self, name: str) -> NormalizedDownloads:
        """Fetch mirror-excluded download metrics and track source completeness."""
        clean_name = name.strip().lower()
        client = await self._get_client()
        encoded_name = quote(clean_name, safe="")
        recent_url = f"https://pypistats.org/api/packages/{encoded_name}/recent"
        overall_url = f"https://pypistats.org/api/packages/{encoded_name}/overall"
        recent_counts: dict[str, int] = {}
        recent_available = False
        historical: dict[str, int] = {}
        historical_available = False
        is_estimated = False

        try:
            resp = await client.get(recent_url)
            if resp.status_code == 200:
                payload = resp.json()
                data = payload.get("data") if isinstance(payload, dict) else None
                if isinstance(data, dict):
                    for period, key in (
                        ("daily", "last_day"),
                        ("weekly", "last_week"),
                        ("monthly", "last_month"),
                    ):
                        count = data.get(key)
                        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
                            recent_counts[period] = count
                    recent_available = len(recent_counts) == 3
                if not recent_available:
                    logger.warning("PyPI Stats recent response was incomplete for %s", clean_name)
            else:
                logger.warning(
                    "PyPI Stats recent endpoint returned HTTP %s for %s",
                    resp.status_code,
                    clean_name,
                )
        except Exception as exc:
            logger.warning(f"Failed to fetch recent pypistats for {clean_name}: {exc}")

        try:
            resp = await client.get(overall_url, params={"mirrors": "false"})
            if resp.status_code == 200:
                payload = resp.json()
                rows = payload.get("data") if isinstance(payload, dict) else None
                if isinstance(rows, list):
                    historical_available = True
                    for row in rows:
                        if not isinstance(row, dict):
                            historical_available = False
                            continue
                        if row.get("category") != "without_mirrors":
                            continue
                        raw_date = row.get("date")
                        count = row.get("downloads")
                        try:
                            parsed_date = date.fromisoformat(raw_date)
                        except (TypeError, ValueError):
                            historical_available = False
                            continue
                        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                            historical_available = False
                            continue
                        historical[parsed_date.isoformat()] = (
                            historical.get(parsed_date.isoformat(), 0) + count
                        )
                else:
                    logger.warning("PyPI Stats overall response was invalid for %s", clean_name)
            else:
                logger.warning(
                    "PyPI Stats overall endpoint returned HTTP %s for %s",
                    resp.status_code,
                    clean_name,
                )
        except Exception as exc:
            logger.warning(f"Could not fetch historical pypistats for {clean_name}: {exc}")

        latest_date = max(historical, default=None)
        if historical and not recent_available:
            latest = date.fromisoformat(latest_date)
            for period, days in (("daily", 1), ("weekly", 7), ("monthly", 30)):
                if period in recent_counts:
                    continue
                start = latest - timedelta(days=days - 1)
                window = {
                    day: count
                    for day, count in historical.items()
                    if start <= date.fromisoformat(day) <= latest
                }
                minimum_observations = max(1, int(days * 0.9))
                if len(window) >= minimum_observations:
                    recent_counts[period] = sum(window.values())
                    is_estimated = True

        data_status = (
            "complete"
            if recent_available and historical_available
            else "partial"
            if recent_counts or historical_available or historical
            else "unavailable"
        )
        provenance_notes = (
            "PyPI Stats excludes known mirrors. Recent aggregate and daily historical "
            "series are fetched independently; figures are downloads, not unique users."
        )
        if not recent_available:
            provenance_notes += " Recent aggregate endpoint was incomplete or unavailable."
        if not historical_available:
            provenance_notes += " Historical endpoint was incomplete or unavailable."

        return NormalizedDownloads(
            package_name=clean_name,
            ecosystem="pypi",
            daily=recent_counts.get("daily", 0),
            weekly=recent_counts.get("weekly", 0),
            monthly=recent_counts.get("monthly", 0),
            historical=historical,
            mirror_inclusive=False,
            is_estimated=is_estimated,
            data_status=data_status,
            available_periods=[
                period for period in ("daily", "weekly", "monthly") if period in recent_counts
            ],
            observed_days=len(historical),
            latest_observation_date=latest_date,
            provenance=DataProvenance(
                source_name="pypistats",
                url_accessed=recent_url,
                notes=provenance_notes,
            ),
        )

    async def fetch_dependencies(self, name: str, version: str | None = None) -> list[dict[str, Any]]:
        clean_name = name.strip().lower()
        url = f"https://pypi.org/pypi/{clean_name}/json"
        client = await self._get_client()

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            requires_dist = data.get("info", {}).get("requires_dist") or []
            return [{"requirement": req} for req in requires_dist]
        except Exception as exc:
            logger.warning(f"Failed to fetch dependencies for {clean_name}: {exc}")
            return []

