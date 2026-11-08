"""
Abstract provider interface and normalized data structures.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class DataProvenance:
    source_name: str
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_live: bool = True
    url_accessed: str | None = None
    notes: str | None = None


@dataclass
class PackageIdentity:
    name: str
    ecosystem: str
    canonical_name: str
    homepage: str | None = None
    repository_url: str | None = None
    provenance: DataProvenance | None = None


@dataclass
class NormalizedMetadata:
    name: str
    ecosystem: str
    description: str | None = None
    homepage: str | None = None
    repository_url: str | None = None
    license: str | None = None
    latest_version: str | None = None
    author: str | None = None
    keywords: list[str] = field(default_factory=list)
    project_urls: dict[str, str] = field(default_factory=dict)
    provenance: DataProvenance | None = None


@dataclass
class NormalizedRelease:
    version: str
    release_date: datetime | None = None
    is_yanked: bool = False
    download_url: str | None = None
    sha256: str | None = None


@dataclass
class NormalizedDownloads:
    package_name: str
    ecosystem: str
    daily: int = 0
    weekly: int = 0
    monthly: int = 0
    historical: dict[str, int] = field(default_factory=dict)  # YYYY-MM-DD -> count
    mirror_inclusive: bool = True
    is_estimated: bool = False
    provenance: DataProvenance | None = None


@dataclass
class NormalizedRepository:
    owner: str
    repo_name: str
    full_name: str
    url: str
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    watchers: int = 0
    default_branch: str = "main"
    is_archived: bool = False
    is_fork: bool = False
    license: str | None = None
    last_commit_at: datetime | None = None
    last_release_at: datetime | None = None
    topics: list[str] = field(default_factory=list)
    provenance: DataProvenance | None = None


class BaseProvider(ABC):
    """Abstract Base Class for all ecosystem providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier, e.g. 'pypi', 'github', 'npm'."""
        pass

    @property
    @abstractmethod
    def supported_ecosystems(self) -> list[str]:
        """List of ecosystem identifiers supported by this provider."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> dict[str, bool]:
        """
        Explicit mapping of supported vs unsupported capabilities.
        Must report false for registry-unsupported features.
        """
        pass

    @abstractmethod
    async def resolve_identity(self, name_or_query: str) -> PackageIdentity:
        """Resolve package query to canonical identity and associated repo."""
        pass

    @abstractmethod
    async def fetch_metadata(self, name: str) -> NormalizedMetadata:
        """Fetch package metadata from ecosystem registry."""
        pass

    @abstractmethod
    async def fetch_releases(self, name: str) -> list[NormalizedRelease]:
        """Fetch full or recent release history."""
        pass

    @abstractmethod
    async def fetch_downloads(self, name: str) -> NormalizedDownloads:
        """Fetch download counts and breakdown when available."""
        pass

    @abstractmethod
    async def fetch_dependencies(self, name: str, version: str | None = None) -> list[dict[str, Any]]:
        """Fetch declared dependencies when registry exposes them."""
        pass

