"""
Adoption Intelligence Analysis Service powered by askai-python.
"""
from typing import List, Optional
from libscope.ai.client import AskAIClient
from libscope.ai.models import AdoptionAssessmentOutput
from libscope.ai.output_validator import AIOutputValidator
from libscope.ai.prompts.adoption_prompts import ADOPTION_ANALYSIS_PROMPT
from libscope.core.logging import get_logger

logger = get_logger("ai.service.adoption")


class AdoptionAnalysisService:
    """Interprets real-world code adoption evidence and separates genuine usage from automated CI mirrors."""

    def __init__(self, client: Optional[AskAIClient] = None):
        self.client = client or AskAIClient()

    async def analyze(
        self,
        name: str,
        ecosystem: str,
        monthly_downloads: int,
        verified_adoptions: int,
        sample_adopters: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> AdoptionAssessmentOutput:
        """
        Synthesize adoption assessment using askai-python or deterministic fallback.
        """
        if not self.client.is_available:
            return self._build_deterministic_fallback(
                name=name,
                monthly_downloads=monthly_downloads,
                verified_adoptions=verified_adoptions,
            )

        adopters_fmt = "\n".join(f"- {a}" for a in (sample_adopters or ["None discovered in sample index"]))
        prompt = ADOPTION_ANALYSIS_PROMPT.format(
            name=name,
            ecosystem=ecosystem,
            monthly_downloads=monthly_downloads,
            verified_adoptions=verified_adoptions,
            adopters_sample=adopters_fmt,
            category=category or "General Library",
        )

        try:
            raw_output = await self.client.ask_async(
                prompt=prompt,
                response_model=AdoptionAssessmentOutput,
            )
            return AIOutputValidator.validate_model(raw_output, AdoptionAssessmentOutput)
        except Exception as exc:
            logger.warning(f"Adoption AI analysis failed for {name}: {exc}. Using deterministic fallback.")
            return self._build_deterministic_fallback(
                name=name,
                monthly_downloads=monthly_downloads,
                verified_adoptions=verified_adoptions,
                notice=f"AI service unavailable ({exc}). Deterministic evaluation provided.",
            )

    def _build_deterministic_fallback(
        self,
        name: str,
        monthly_downloads: int,
        verified_adoptions: int,
        notice: Optional[str] = None,
    ) -> AdoptionAssessmentOutput:
        header = f"[{notice}]\n" if notice else ""
        if verified_adoptions >= 20:
            verdict = "HIGH_GENUINE"
            dl_analysis = (
                f"Discovered {verified_adoptions} verified public manifests declaring '{name}'. "
                f"With {monthly_downloads:,} monthly downloads, the package exhibits strong indicators of organic adoption."
            )
        elif verified_adoptions >= 5:
            verdict = "MODERATE"
            dl_analysis = (
                f"Verified in {verified_adoptions} public manifests. "
                f"Substantial proportion of monthly downloads ({monthly_downloads:,}) may stem from CI pipelines and transient builds."
            )
        elif verified_adoptions > 0:
            verdict = "LOW_OR_SUBDEPENDENCY"
            dl_analysis = (
                f"Found {verified_adoptions} direct manifest citations. "
                "Download volume likely includes automated mirror activity or nested subdependency usage."
            )
        else:
            verdict = "INSUFFICIENT_EVIDENCE"
            dl_analysis = (
                f"No verified public repository manifests discovered yet for '{name}'. "
                "Download metrics cannot be independently verified without repository manifest evidence."
            )

        return AdoptionAssessmentOutput(
            genuine_adoption_verdict=verdict,
            adoption_summary=f"{header}Adoption evaluation for '{name}': classified as {verdict} based on {verified_adoptions} verified independent manifest declarations.",
            real_world_use_cases=[f"Direct dependency declarations in {verified_adoptions} external codebases."],
            download_vs_adoption_analysis=dl_analysis,
        )

