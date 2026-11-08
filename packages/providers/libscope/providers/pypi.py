"""
PyPI Package Provider implementation.
Queries PyPI JSON API and pypistats API.
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
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

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    @property
    def name(self) -> str:
        return "pypi"

    @property
    def supported_ecosystems(self) -> List[str]:
        return ["pypi", "python"]

    @property
    def capabilities(self) -> Dict[str, bool]:
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

    def _extract_github_url(self, info: Dict[str, Any]) -> Optional[str]:
        """Extract GitHub repository URL from project_urls or home_page."""
        urls: List[str] = []
        if info.get("home_page"):
            urls.append(info["home_page"])

        project_urls = info.get("project_urls") or {}
        for key, val in project_urls.items():
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

    async def fetch_releases(self, name: str) -> List[NormalizedRelease]:
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
        results: List[NormalizedRelease] = []

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
            key=lambda r: r.release_date or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return results

    async def fetch_downloads(self, name: str) -> NormalizedDownloads:
        """Fetch download counts from pypistats.org."""
        clean_name = name.strip().lower()
        client = await self._get_client()

        daily, weekly, monthly = 0, 0, 0
        historical: Dict[str, int] = {}
        provenance_notes = "pypistats recent API"

        # 1. Recent downloads
        try:
            recent_url = f"https://pypistats.org/api/packages/{clean_name}/recent"
            resp = await client.get(recent_url)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                daily = data.get("last_day", 0)
                weekly = data.get("last_week", 0)
                monthly = data.get("last_month", 0)
        except Exception as exc:
            logger.warning(f"Failed to fetch recent pypistats for {clean_name}: {exc}")

        # 2. Historical overall downloads (last 30-180 days daily breakdown)
        try:
            overall_url = f"https://pypistats.org/api/packages/{clean_name}/overall"
            resp = await client.get(overall_url)
            if resp.status_code == 200:
                rows = resp.json().get("data", [])
                for row in rows:
                    if row.get("category") == "without_mirrors":
                        dt = row.get("date")
                        cnt = row.get("downloads", 0)
                        if dt:
                            historical[dt] = historical.get(dt, 0) + cnt
                if historical:
                    provenance_notes += "; overall daily historical (without mirrors)"
        except Exception as exc:
            logger.debug(f"Could not fetch historical pypistats for {clean_name}: {exc}")

        return NormalizedDownloads(
            package_name=clean_name,
            ecosystem="pypi",
            daily=daily,
            weekly=weekly,
            monthly=monthly,
            historical=historical,
            mirror_inclusive=False if historical else True,
            is_estimated=False,
            provenance=DataProvenance(
                source_name="pypistats",
                url_accessed=f"https://pypistats.org/api/packages/{clean_name}/recent",
                notes=provenance_notes,
            ),
        )

    async def fetch_dependencies(self, name: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
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

