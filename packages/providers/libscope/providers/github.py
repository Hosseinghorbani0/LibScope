"""
GitHub Repository and Code Host Provider implementation.
Queries GitHub REST API v3 with authentication support, rate limit tracking, and safe fallbacks.
"""
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx
from libscope.core.config import get_settings
from libscope.core.logging import get_logger
from libscope.core.security import create_safe_httpx_client
from libscope.providers.base import (
    BaseProvider,
    DataProvenance,
    NormalizedDownloads,
    NormalizedMetadata,
    NormalizedRelease,
    NormalizedRepository,
    PackageIdentity,
)

logger = get_logger("provider.github")


class GitHubProvider(BaseProvider):
    """Provider for GitHub repositories and public code search."""

    def __init__(self, token: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        settings = get_settings()
        self._token = token or settings.effective_github_token
        self._client = client
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[int] = None

    @property
    def name(self) -> str:
        return "github"

    @property
    def supported_ecosystems(self) -> List[str]:
        return ["github", "git"]

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "metadata": True,
            "releases": True,
            "downloads": False,  # GitHub does not track package registry download stats directly
            "repository": True,
            "dependencies": False,
            "code_search": True,
            "community_profile": True,
            "commit_activity": True,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = create_safe_httpx_client()
        return self._client

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def parse_owner_repo(self, query_or_url: str) -> Tuple[str, str]:
        """Extract (owner, repo) from URL or shorthand string 'owner/repo'."""
        cleaned = query_or_url.strip()
        match = re.search(r"github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)", cleaned)
        if match:
            owner, repo = match.group(1), match.group(2)
        elif "/" in cleaned and not cleaned.startswith("http"):
            parts = cleaned.split("/")
            owner, repo = parts[0], parts[1]
        else:
            raise ValueError(f"Cannot parse GitHub repository from '{query_or_url}'")

        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo

    async def _check_response(self, resp: httpx.Response, context: str) -> None:
        rem = resp.headers.get("x-ratelimit-remaining")
        reset = resp.headers.get("x-ratelimit-reset")
        if rem is not None:
            self._rate_limit_remaining = int(rem)
            if self._rate_limit_remaining < 5:
                logger.warning(f"GitHub API rate limit critical: {self._rate_limit_remaining} requests left")
        if reset is not None:
            self._rate_limit_reset = int(reset)

        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise RuntimeError(f"GitHub API rate limit exceeded while fetching {context}")
        resp.raise_for_status()

    async def resolve_identity(self, name_or_query: str) -> PackageIdentity:
        owner, repo = self.parse_owner_repo(name_or_query)
        full_name = f"{owner}/{repo}"
        repo_data = await self.fetch_repository(full_name)
        return PackageIdentity(
            name=repo,
            ecosystem="github",
            canonical_name=full_name,
            homepage=repo_data.url if repo_data else None,
            repository_url=f"https://github.com/{full_name}",
            provenance=repo_data.provenance if repo_data else None,
        )

    async def fetch_repository(self, repo_url_or_shorthand: str) -> NormalizedRepository:
        owner, repo = self.parse_owner_repo(repo_url_or_shorthand)
        full_name = f"{owner}/{repo}"
        url = f"https://api.github.com/repos/{owner}/{repo}"
        client = await self._get_client()

        resp = await client.get(url, headers=self._get_headers())
        await self._check_response(resp, full_name)
        data = resp.json()

        # Last commit date
        last_commit_at = None
        try:
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            c_resp = await client.get(commits_url, headers=self._get_headers(), params={"per_page": 1})
            if c_resp.status_code == 200 and c_resp.json():
                dt_str = c_resp.json()[0].get("commit", {}).get("committer", {}).get("date")
                if dt_str:
                    last_commit_at = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception as exc:
            logger.debug(f"Could not fetch last commit date for {full_name}: {exc}")

        # Last release date
        last_release_at = None
        try:
            rel_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            r_resp = await client.get(rel_url, headers=self._get_headers())
            if r_resp.status_code == 200:
                rel_dt_str = r_resp.json().get("published_at")
                if rel_dt_str:
                    last_release_at = datetime.fromisoformat(rel_dt_str.replace("Z", "+00:00"))
        except Exception as exc:
            logger.debug(f"Could not fetch latest release date for {full_name}: {exc}")

        license_info = data.get("license") or {}
        license_name = license_info.get("spdx_id") or license_info.get("name")

        return NormalizedRepository(
            owner=owner,
            repo_name=repo,
            full_name=full_name,
            url=data.get("html_url", f"https://github.com/{full_name}"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            closed_issues=0,  # GitHub API repo view returns open_issues (which includes PRs)
            watchers=data.get("subscribers_count", data.get("watchers_count", 0)),
            default_branch=data.get("default_branch", "main"),
            is_archived=bool(data.get("archived", False)),
            is_fork=bool(data.get("fork", False)),
            license=license_name,
            last_commit_at=last_commit_at,
            last_release_at=last_release_at,
            topics=data.get("topics", []),
            provenance=DataProvenance(
                source_name="github_api",
                url_accessed=url,
                notes=f"GitHub repository metadata. Authenticated: {bool(self._token)}",
            ),
        )

    async def fetch_community_profile(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository community profile (health files, license, readme)."""
        url = f"https://api.github.com/repos/{owner}/{repo}/community/profile"
        client = await self._get_client()
        try:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                return resp.json()
        except Exception as exc:
            logger.debug(f"Could not fetch community profile for {owner}/{repo}: {exc}")
        return {}

    async def fetch_raw_file(self, owner: str, repo: str, file_path: str, branch: str = "main") -> Optional[str]:
        """Fetch raw content of a specific file in the repository (e.g. pyproject.toml, README)."""
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        client = await self._get_client()
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        return None

    async def fetch_metadata(self, name: str) -> NormalizedMetadata:
        owner, repo = self.parse_owner_repo(name)
        repo_data = await self.fetch_repository(f"{owner}/{repo}")
        return NormalizedMetadata(
            name=repo_data.repo_name,
            ecosystem="github",
            description=None,
            homepage=repo_data.url,
            repository_url=repo_data.url,
            license=repo_data.license,
            keywords=repo_data.topics,
            provenance=repo_data.provenance,
        )

    async def fetch_releases(self, name: str) -> List[NormalizedRelease]:
        owner, repo = self.parse_owner_repo(name)
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        client = await self._get_client()

        try:
            resp = await client.get(url, headers=self._get_headers(), params={"per_page": 20})
            if resp.status_code != 200:
                return []
            data = resp.json()
            releases: List[NormalizedRelease] = []
            for item in data:
                tag = item.get("tag_name", "")
                published_at = item.get("published_at")
                rel_dt = None
                if published_at:
                    rel_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                releases.append(
                    NormalizedRelease(
                        version=tag,
                        release_date=rel_dt,
                        is_yanked=bool(item.get("prerelease", False)),
                        download_url=item.get("html_url"),
                    )
                )
            return releases
        except Exception as exc:
            logger.warning(f"Failed to fetch GitHub releases for {owner}/{repo}: {exc}")
            return []

    async def fetch_downloads(self, name: str) -> NormalizedDownloads:
        # GitHub does not track package download stats
        return NormalizedDownloads(
            package_name=name,
            ecosystem="github",
            daily=0,
            weekly=0,
            monthly=0,
            historical={},
            mirror_inclusive=False,
            is_estimated=False,
            provenance=DataProvenance(
                source_name="github_api",
                notes="Registry download metrics not supported by GitHub provider",
            ),
        )

    async def fetch_dependencies(self, name: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
        return []

    async def search_code_adoption(self, package_name: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        Search for adoption evidence of package_name in manifests across public GitHub repositories.
        Searches filenames like requirements.txt, pyproject.toml, setup.py, package.json.
        """
        if not self._token:
            logger.info("GitHub code search skipped: unauthenticated API has strict limits on search.")
            return []

        url = "https://api.github.com/search/code"
        client = await self._get_client()
        query = f'"{package_name}" filename:requirements.txt OR filename:pyproject.toml'

        try:
            resp = await client.get(
                url,
                headers=self._get_headers(),
                params={"q": query, "per_page": min(max_results, 30)},
            )
            await self._check_response(resp, "code search")
            data = resp.json()
            items = data.get("items", [])
            results = []
            for item in items:
                repo_info = item.get("repository", {})
                results.append({
                    "repo_full_name": repo_info.get("full_name"),
                    "repo_url": repo_info.get("html_url"),
                    "file_path": item.get("path"),
                    "html_url": item.get("html_url"),
                })
            return results
        except Exception as exc:
            logger.warning(f"GitHub code search failed for '{package_name}': {exc}")
            return []

