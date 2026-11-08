"""
Maintainer Recommendations Service powered by askai-python.
"""
from typing import List, Optional
from libscope.ai.client import AskAIClient
from libscope.ai.models import MaintainerRecommendationsOutput
from libscope.ai.output_validator import AIOutputValidator
from libscope.ai.prompts.recommendations_prompts import RECOMMENDATIONS_PROMPT
from libscope.core.logging import get_logger

logger = get_logger("ai.service.recommendations")


class MaintainerRecommendationsService:
    """Produces prioritized, actionable guidance for project maintainers."""

    def __init__(self, client: Optional[AskAIClient] = None):
        self.client = client or AskAIClient()

    async def generate_recommendations(
        self,
        name: str,
        score: Optional[float],
        confidence: str,
        health_score: Optional[float] = None,
        maintenance_score: Optional[float] = None,
        security_score: Optional[float] = None,
        adoption_score: Optional[float] = None,
        hygiene_gaps: Optional[List[str]] = None,
        days_since_commit: Optional[int] = None,
        days_since_release: Optional[int] = None,
        vulnerabilities_count: int = 0,
    ) -> MaintainerRecommendationsOutput:
        """
        Generate prioritized recommendations using askai-python or deterministic fallback.
        """
        if not self.client.is_available:
            return self._build_deterministic_fallback(
                name=name,
                vulnerabilities_count=vulnerabilities_count,
                hygiene_gaps=hygiene_gaps or [],
                days_since_release=days_since_release,
            )

        gaps_str = ", ".join(hygiene_gaps) if hygiene_gaps else "None detected"
        prompt = RECOMMENDATIONS_PROMPT.format(
            name=name,
            score=score if score is not None else "N/A",
            confidence=confidence,
            health_score=health_score if health_score is not None else "N/A",
            maintenance_score=maintenance_score if maintenance_score is not None else "N/A",
            security_score=security_score if security_score is not None else "N/A",
            adoption_score=adoption_score if adoption_score is not None else "N/A",
            hygiene_gaps=gaps_str,
            days_since_commit=days_since_commit if days_since_commit is not None else "Unknown",
            days_since_release=days_since_release if days_since_release is not None else "Unknown",
            vulnerabilities_count=vulnerabilities_count,
        )

        try:
            raw_output = await self.client.ask_async(
                prompt=prompt,
                response_model=MaintainerRecommendationsOutput,
            )
            return AIOutputValidator.validate_model(raw_output, MaintainerRecommendationsOutput)
        except Exception as exc:
            logger.warning(f"Recommendations AI generation failed for {name}: {exc}. Using deterministic fallback.")
            return self._build_deterministic_fallback(
                name=name,
                vulnerabilities_count=vulnerabilities_count,
                hygiene_gaps=hygiene_gaps or [],
                days_since_release=days_since_release,
                notice=f"AI service unavailable ({exc}). Deterministic recommendations provided.",
            )

    def _build_deterministic_fallback(
        self,
        name: str,
        vulnerabilities_count: int,
        hygiene_gaps: List[str],
        days_since_release: Optional[int],
        notice: Optional[str] = None,
    ) -> MaintainerRecommendationsOutput:
        immediate: List[str] = []
        medium: List[str] = []
        community: List[str] = []

        if notice:
            immediate.append(f"[{notice}]")

        if vulnerabilities_count > 0:
            immediate.append(f"Audit and patch {vulnerabilities_count} open security vulnerabilities in dependencies.")

        for gap in hygiene_gaps:
            if "SECURITY.md" in gap:
                immediate.append("Add a SECURITY.md vulnerability reporting policy.")
            elif "LICENSE" in gap:
                immediate.append("Add an OSI-approved LICENSE file to clarify downstream usage rights.")
            elif "CONTRIBUTING" in gap:
                community.append("Create a CONTRIBUTING.md guide with setup steps for new contributors.")
            elif "CI" in gap:
                medium.append("Configure automated CI test workflows (e.g. GitHub Actions).")

        if days_since_release is not None and days_since_release > 180:
            immediate.append(f"Publish a fresh release (last release was {days_since_release} days ago).")

        if not immediate:
            immediate.append("Review issue backlog and close stale bug reports.")

        if not medium:
            medium.append("Automate changelog generation and semantic versioning releases.")
            medium.append("Establish integration benchmarks and regression test suites.")

        if not community:
            community.append("Add issue templates for bug reports and feature requests.")
            community.append("Document architectural design principles in documentation.")

        return MaintainerRecommendationsOutput(
            immediate_actions=immediate,
            medium_term_goals=medium,
            community_improvements=community,
        )

