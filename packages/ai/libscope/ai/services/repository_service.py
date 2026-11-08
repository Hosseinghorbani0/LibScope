"""
Repository Intelligence Analysis Service powered by askai-python.
"""

from libscope.ai.client import AskAIClient
from libscope.ai.models import HealthAssessmentOutput
from libscope.ai.services.health_service import HealthAnalysisService
from libscope.core.logging import get_logger

logger = get_logger("ai.service.repository")


class RepositoryAnalysisService:
    """Provides repository-level software intelligence and analysis."""

    def __init__(self, client: AskAIClient | None = None):
        self.client = client or AskAIClient()
        self._health_service = HealthAnalysisService(client=self.client)

    async def analyze_repo(
        self,
        repo_name: str,
        stars: int,
        forks: int,
        watchers: int,
        open_issues: int,
        days_since_commit: int | None,
        days_since_release: int | None,
        has_readme: bool,
        license_str: str | None,
        has_contributing: bool,
        has_security_md: bool,
        has_ci: bool,
        is_archived: bool = False,
    ) -> HealthAssessmentOutput:
        """
        Delegates to health analysis service to synthesize repository evaluation.
        """
        return await self._health_service.analyze(
            repo_name=repo_name,
            stars=stars,
            forks=forks,
            watchers=watchers,
            open_issues=open_issues,
            days_since_commit=days_since_commit,
            days_since_release=days_since_release,
            has_readme=has_readme,
            license_str=license_str,
            has_contributing=has_contributing,
            has_security_md=has_security_md,
            has_ci=has_ci,
            is_archived=is_archived,
        )

