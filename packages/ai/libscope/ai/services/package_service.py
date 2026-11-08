"""
Package Intelligence Analysis Service powered by askai-python.
"""
from libscope.ai.client import AskAIClient
from libscope.ai.models import PackageAnalysisOutput
from libscope.ai.output_validator import AIOutputValidator
from libscope.ai.prompts.package_prompts import PACKAGE_ANALYSIS_PROMPT
from libscope.ai.security import sanitize_untrusted_text
from libscope.core.logging import get_logger

logger = get_logger("ai.service.package")


class PackageAnalysisService:
    """Orchestrates comprehensive package intelligence synthesis."""

    def __init__(self, client: AskAIClient | None = None):
        self.client = client or AskAIClient()

    async def analyze(
        self,
        name: str,
        ecosystem: str,
        latest_version: str | None,
        license_str: str | None,
        repo_url: str | None,
        monthly_downloads: int,
        mirror_inclusive: bool,
        growth_trend: str,
        stars: int,
        forks: int,
        open_issues: int,
        days_since_commit: int | None,
        days_since_release: int | None,
        verified_adoptions: int,
        vulnerabilities_count: int,
        critical_high_count: int,
        overall_score: float | None,
        confidence_level: str,
        raw_description: str | None,
    ) -> PackageAnalysisOutput:
        """
        Generate structured package analysis using askai-python or deterministic fallback.
        """
        if not self.client.is_available:
            return self._build_deterministic_fallback(name, overall_score, confidence_level, verified_adoptions, vulnerabilities_count)

        sanitized_desc = sanitize_untrusted_text(raw_description, max_length=1500)
        prompt = PACKAGE_ANALYSIS_PROMPT.format(
            name=name,
            ecosystem=ecosystem,
            latest_version=latest_version or "Unknown",
            license=license_str or "Unspecified",
            repo_url=repo_url or "None",
            monthly_downloads=monthly_downloads,
            mirror_note="includes automated CI mirrors" if mirror_inclusive else "mirror-exclusive",
            growth_trend=growth_trend,
            stars=stars,
            forks=forks,
            open_issues=open_issues,
            days_since_commit=days_since_commit if days_since_commit is not None else "Unknown",
            days_since_release=days_since_release if days_since_release is not None else "Unknown",
            verified_adoptions=verified_adoptions,
            vulnerabilities_count=vulnerabilities_count,
            critical_high_count=critical_high_count,
            overall_score=overall_score if overall_score is not None else "N/A",
            confidence_level=confidence_level,
            sanitized_description=sanitized_desc,
        )

        try:
            raw_output = await self.client.ask_async(
                prompt=prompt,
                response_model=PackageAnalysisOutput,
            )
            return AIOutputValidator.validate_model(raw_output, PackageAnalysisOutput)
        except Exception as exc:
            logger.warning(f"askai-python analysis for {name} failed: {exc}. Falling back to deterministic synthesis.")
            return self._build_deterministic_fallback(name, overall_score, confidence_level, verified_adoptions, vulnerabilities_count, notice=f"AI provider unavailable ({exc}). Deterministic synthesis provided.")

    def _build_deterministic_fallback(
        self,
        name: str,
        score: float | None,
        confidence: str,
        verified_adoptions: int,
        vulnerabilities: int,
        notice: str | None = None,
    ) -> PackageAnalysisOutput:
        header = f"[{notice}]\n" if notice else "[Deterministic Intelligence Report - AI Engine Offline]\n"
        score_str = f"{score}/100" if score is not None else "Insufficient Data"

        summary = (
            f"{header}Package '{name}' has been evaluated deterministically by LibScope with an overall quality score of {score_str} "
            f"({confidence} confidence). Verified independent adoption was discovered in {verified_adoptions} public repository manifests. "
            f"There are currently {vulnerabilities} reported security findings in the OSV database."
        )

        risks = (
            f"• Verified in {verified_adoptions} external project manifests.\n"
            f"• Security advisories count: {vulnerabilities}.\n"
            "• Monitor downstream patch releases and upstream breaking changes."
        )

        opportunities = (
            "• Expand test automation and CI pipeline reporting.\n"
            "• Establish verified community guidelines and published disclosure policy."
        )

        recs = (
            "• Regularly update dependencies to resolve potential advisories.\n"
            "• Maintain predictable semantic release versioning."
        )

        pos = f"Active package within its ecosystem evaluated with {score_str} LibScope score."

        return PackageAnalysisOutput(
            summary=summary,
            risks=risks,
            opportunities=opportunities,
            maintainer_recommendations=recs,
            competitive_position=pos,
        )

