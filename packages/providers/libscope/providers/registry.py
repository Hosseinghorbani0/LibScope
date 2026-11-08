"""
Provider Registry for ecosystem discovery and resolution.
"""
from typing import Dict, List, Optional
from libscope.providers.base import BaseProvider
from libscope.providers.github import GitHubProvider
from libscope.providers.pypi import PyPIProvider


class ProviderRegistry:
    """Singleton registry managing active ecosystem providers."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        # Register default providers
        self.register(PyPIProvider())
        self.register(GitHubProvider())

    def register(self, provider: BaseProvider) -> None:
        self._providers[provider.name.lower()] = provider
        for eco in provider.supported_ecosystems:
            self._providers[eco.lower()] = provider

    def get(self, ecosystem_or_name: str) -> Optional[BaseProvider]:
        return self._providers.get(ecosystem_or_name.lower())

    def list_providers(self) -> List[Dict[str, any]]:
        seen = set()
        result = []
        for p in self._providers.values():
            if p.name not in seen:
                seen.add(p.name)
                result.append({
                    "name": p.name,
                    "supported_ecosystems": p.supported_ecosystems,
                    "capabilities": p.capabilities,
                })
        return result


_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry

