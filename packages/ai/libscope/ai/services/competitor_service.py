"""
Competitor Package Comparison Analysis Service powered by askai-python.
"""
from typing import Any

from libscope.ai.client import AskAIClient
from libscope.ai.models import CompetitorComparisonOutput
from libscope.ai.output_validator import AIOutputValidator
from libscope.ai.prompts.competitor_prompts import COMPETITOR_COMPARISON_PROMPT
from libscope.core.logging import get_logger

logger = get_logger("ai.service.competitor")


class CompetitorAnalysisService:
    """Produces multi-package comparative intelligence."""

    def __init__(self, client: AskAIClient | None = None):
        self.client = client or AskAIClient()

    async def compare(
        self,
        comparison_records: list[dict[str, Any]],
    ) -> CompetitorComparisonOutput:
        """
        Compare packages using askai-python or deterministic fallback.
        """
        if not self.client.is_available:
            return self._build_deterministic_fallback(comparison_records)

        lines: list[str] = []
        for r in comparison_records:
            name = r.get("name", "Unknown")
            score = r.get("score", "N/A")
            downloads = r.get("monthly_downloads", 0)
            stars = r.get("stars", 0)
            adoptions = r.get("verified_adoptions", 0)
            lines.append(f"Package '{name}': Score={score}/100, Downloads={downloads:,}/mo, Stars={stars:,}, Verified Adoptions={adoptions}")

        table_str = "\n".join(lines)
        prompt = COMPETITOR_COMPARISON_PROMPT.format(comparison_table=table_str)

        try:
            raw_output = await self.client.ask_async(
                prompt=prompt,
                response_model=CompetitorComparisonOutput,
            )
            return AIOutputValidator.validate_model(raw_output, CompetitorComparisonOutput)
        except Exception as exc:
            logger.warning(f"Competitor AI analysis failed: {exc}. Using deterministic fallback.")
            return self._build_deterministic_fallback(
                comparison_records,
                notice=f"AI service unavailable ({exc}). Deterministic comparison provided.",
            )

    def _build_deterministic_fallback(
        self,
        comparison_records: list[dict[str, Any]],
        notice: str | None = None,
    ) -> CompetitorComparisonOutput:
        if not comparison_records:
            return CompetitorComparisonOutput(
                comparative_summary="No packages provided for comparison.",
                market_leader="None",
                recommendations_by_use_case=[],
                key_differentiators=[],
            )

        # Sort by deterministic score or downloads
        sorted_pkgs = sorted(
            comparison_records,
            key=lambda p: (p.get("score") or 0.0, p.get("verified_adoptions") or 0, p.get("monthly_downloads") or 0),
            reverse=True,
        )
        leader = sorted_pkgs[0].get("name", "Unknown")

        summary = (
            f"Compared {len(comparison_records)} packages deterministically. "
            f"'{leader}' leads the group based on combined LibScope scores, verified adoption declarations, and activity metrics."
        )
        if notice:
            summary = f"[{notice}] {summary}"

        differentiators = [
            f"'{pkg.get('name')}': {pkg.get('monthly_downloads', 0):,} monthly downloads with {pkg.get('verified_adoptions', 0)} verified external adoptions."
            for pkg in sorted_pkgs
        ]

        recs = [
            f"Choose '{leader}' for high-maturity requirements with strong community adoption.",
        ]
        if len(sorted_pkgs) > 1:
            recs.append(f"Evaluate '{sorted_pkgs[1].get('name')}' as an alternative option depending on architectural tradeoffs.")

        return CompetitorComparisonOutput(
            comparative_summary=summary,
            market_leader=leader,
            recommendations_by_use_case=recs,
            key_differentiators=differentiators,
        )

