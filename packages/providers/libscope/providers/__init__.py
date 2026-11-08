"""
LibScope Providers Package.
"""
from libscope.providers.base import (
    BaseProvider,
    DataProvenance,
    NormalizedDownloads,
    NormalizedMetadata,
    NormalizedRelease,
    NormalizedRepository,
    PackageIdentity,
)
from libscope.providers.github import GitHubProvider
from libscope.providers.pypi import PyPIProvider
from libscope.providers.registry import ProviderRegistry, get_provider_registry

__all__ = [
    "BaseProvider",
    "DataProvenance",
    "PackageIdentity",
    "NormalizedMetadata",
    "NormalizedRelease",
    "NormalizedDownloads",
    "NormalizedRepository",
    "PyPIProvider",
    "GitHubProvider",
    "ProviderRegistry",
    "get_provider_registry",
]

