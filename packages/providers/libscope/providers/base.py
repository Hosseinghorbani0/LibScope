"""
Abstract provider interface and normalized data structures.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DataProvenance:
    source_name: str
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_live: bool = True
    url_accessed: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class PackageIdentity:
    name: str
    ecosystem: str
    canonical_name: str
    homepage: Optional[str] = None
    repository_url: Optional[str] = None
    provenance: Optional[DataProvenance] = None


@dataclass
class NormalizedMetadata:
    name: str
    ecosystem: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    repository_url: Optional[str] = None
    license: Optional[str] = None
    latest_version: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    project_urls: Dict[str, str] = field(default_factory=dict)
    provenance: Optional[DataProvenance] = None


@dataclass
class NormalizedRelease:
    version: str
    release_date: Optional[datetime] = None
    is_yanked: bool = False
    download_url: Optional[str] = None
    sha256: Optional[str] = None


@dataclass
class NormalizedDownloads:
    package_name: str
    ecosystem: str
    daily: int = 0
    weekly: int = 0
    monthly: int = 0
    historical: Dict[str, int] = field(default_factory=dict)  # YYYY-MM-DD -> count
    mirror_inclusive: bool = True
    is_estimated: bool = False
    provenance: Optional[DataProvenance] = None


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
    license: Optional[str] = None
    last_commit_at: Optional[datetime] = None
    last_release_at: Optional[datetime] = None
    topics: List[str] = field(default_factory=list)
    provenance: Optional[DataProvenance] = None


class BaseProvider(ABC):
    """Abstract Base Class for all ecosystem providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier, e.g. 'pypi', 'github', 'npm'."""
        pass

    @property
    @abstractmethod
    def supported_ecosystems(self) -> List[str]:
        """List of ecosystem identifiers supported by this provider."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
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
    async def fetch_releases(self, name: str) -> List[NormalizedRelease]:
        """Fetch full or recent release history."""
        pass

    @abstractmethod
    async def fetch_downloads(self, name: str) -> NormalizedDownloads:
        """Fetch download counts and breakdown when available."""
        pass

    @abstractmethod
    async def fetch_dependencies(self, name: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch declared dependencies when registry exposes them."""
        pass

