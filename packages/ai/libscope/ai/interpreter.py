"""
AI Analyst Orchestrator and Interpreter.
Coordinates deterministic evidence formatting, sanitization, and structured interpretation.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional
from libscope.core.logging import get_logger
from libscope.ai.client import AskAIClient
from libscope.ai.services.package_service import PackageAnalysisService

logger = get_logger("ai.interpreter")


@dataclass
class AIAnalysisResult:
    package_name: str
    generated_at: datetime
    provider: str
    model: str
    is_ai_generated: bool
    summary: str
    risks: str
    opportunities: str
    maintainer_recommendations: str
    competitive_position: str
    raw_response: str


class AIInterpreter:
    """Orchestrates structured intelligence synthesis."""

    def __init__(self, client: Optional[AskAIClient] = None, service: Optional[PackageAnalysisService] = None):
        self.client = client or AskAIClient()
        self.service = service or PackageAnalysisService(client=self.client)

    async def interpret(
        self,
        package_name: str,
        ecosystem: str,
        latest_version: Optional[str],
        license_str: Optional[str],
        repo_url: Optional[str],
        overall_score: Optional[float],
        confidence_level: str,
        dimension_breakdown: str,
        monthly_downloads: int,
        mirror_inclusive: bool,
        growth_trend: str,
        stars: int,
        forks: int,
        open_issues: int,
        days_since_commit: Optional[int],
        days_since_release: Optional[int],
        verified_adoptions_count: int,
        vulnerabilities_count: int,
        critical_high_count: int,
        raw_description: Optional[str],
    ) -> AIAnalysisResult:
        now = datetime.now(timezone.utc)

        pkg_output = await self.service.analyze(
            name=package_name,
            ecosystem=ecosystem,
            latest_version=latest_version,
            license_str=license_str,
            repo_url=repo_url,
            monthly_downloads=monthly_downloads,
            mirror_inclusive=mirror_inclusive,
            growth_trend=growth_trend,
            stars=stars,
            forks=forks,
            open_issues=open_issues,
            days_since_commit=days_since_commit,
            days_since_release=days_since_release,
            verified_adoptions=verified_adoptions_count,
            vulnerabilities_count=vulnerabilities_count,
            critical_high_count=critical_high_count,
            overall_score=overall_score,
            confidence_level=confidence_level,
            raw_description=raw_description,
        )

        is_ai = self.client.is_available
        provider = self.client.config.provider if is_ai else "deterministic"
        model = self.client.config.model if is_ai else "deterministic-fallback"

        return AIAnalysisResult(
            package_name=package_name,
            generated_at=now,
            provider=provider,
            model=model,
            is_ai_generated=is_ai,
            summary=pkg_output.summary,
            risks=pkg_output.risks,
            opportunities=pkg_output.opportunities,
            maintainer_recommendations=pkg_output.maintainer_recommendations,
            competitive_position=pkg_output.competitive_position,
            raw_response=json.dumps(pkg_output.model_dump(), default=str),
        )
