"""
Repository Health & Maintenance Analysis Service powered by askai-python.
"""

from libscope.ai.client import AskAIClient
from libscope.ai.models import HealthAssessmentOutput
from libscope.ai.output_validator import AIOutputValidator
from libscope.ai.prompts.health_prompts import HEALTH_ANALYSIS_PROMPT
from libscope.core.logging import get_logger

logger = get_logger("ai.service.health")


class HealthAnalysisService:
    """Evaluates repository engineering practices, governance, and cadence."""

    def __init__(self, client: AskAIClient | None = None):
        self.client = client or AskAIClient()

    async def analyze(
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
        Evaluate project health using askai-python or deterministic fallback.
        """
        if not self.client.is_available:
            return self._build_deterministic_fallback(
                repo_name=repo_name,
                days_since_commit=days_since_commit,
                days_since_release=days_since_release,
                has_readme=has_readme,
                has_contributing=has_contributing,
                has_security_md=has_security_md,
                has_ci=has_ci,
                is_archived=is_archived,
            )

        prompt = HEALTH_ANALYSIS_PROMPT.format(
            repo_name=repo_name,
            stars=stars,
            forks=forks,
            watchers=watchers,
            open_issues=open_issues,
            days_since_commit=days_since_commit if days_since_commit is not None else "Unknown",
            days_since_release=days_since_release if days_since_release is not None else "Unknown",
            has_readme="Yes" if has_readme else "No",
            license=license_str or "Missing",
            has_contributing="Yes" if has_contributing else "No",
            has_security_md="Yes" if has_security_md else "No",
            has_ci="Yes" if has_ci else "No",
            is_archived="ARCHIVED" if is_archived else "Active",
        )

        try:
            raw_output = await self.client.ask_async(
                prompt=prompt,
                response_model=HealthAssessmentOutput,
            )
            return AIOutputValidator.validate_model(raw_output, HealthAssessmentOutput)
        except Exception as exc:
            logger.warning(f"Health AI analysis failed for {repo_name}: {exc}. Using deterministic fallback.")
            return self._build_deterministic_fallback(
                repo_name=repo_name,
                days_since_commit=days_since_commit,
                days_since_release=days_since_release,
                has_readme=has_readme,
                has_contributing=has_contributing,
                has_security_md=has_security_md,
                has_ci=has_ci,
                is_archived=is_archived,
                notice=f"AI service unavailable ({exc}). Deterministic evaluation provided.",
            )

    def _build_deterministic_fallback(
        self,
        repo_name: str,
        days_since_commit: int | None,
        days_since_release: int | None,
        has_readme: bool,
        has_contributing: bool,
        has_security_md: bool,
        has_ci: bool,
        is_archived: bool,
        notice: str | None = None,
    ) -> HealthAssessmentOutput:
        strengths: list[str] = []
        weaknesses: list[str] = []

        if is_archived:
            return HealthAssessmentOutput(
                health_rating="AT_RISK",
                strengths=["Historical codebase preserved."],
                weaknesses=["Repository is permanently marked as archived by maintainers."],
                maintenance_cadence_verdict="ARCHIVED - No active maintenance.",
            )

        if has_readme:
            strengths.append("Project provides onboarding documentation in README.")
        else:
            weaknesses.append("Missing standard README documentation.")

        if has_ci:
            strengths.append("Configured automated continuous integration (CI) workflows.")
        else:
            weaknesses.append("No active CI build or test workflows discovered.")

        if has_security_md:
            strengths.append("Published dedicated security disclosure policy (SECURITY.md).")
        else:
            weaknesses.append("No formal SECURITY.md vulnerability reporting instructions.")

        if has_contributing:
            strengths.append("Published CONTRIBUTING guide for external developers.")
        else:
            weaknesses.append("Lacks formal CONTRIBUTING guide for contributors.")

        if days_since_commit is not None:
            if days_since_commit <= 30:
                strengths.append(f"Recent commit activity ({days_since_commit} days ago).")
                cadence = "HIGH_FREQUENCY - Active recent development."
                rating = "EXCELLENT" if len(weaknesses) == 0 else "HEALTHY"
            elif days_since_commit <= 90:
                cadence = "STEADY - Periodic maintenance updates."
                rating = "HEALTHY"
            elif days_since_commit <= 365:
                weaknesses.append(f"Infrequent commits: last commit was {days_since_commit} days ago.")
                cadence = "SLOW - Maintenance pace has slowed down."
                rating = "NEEDS_ATTENTION"
            else:
                weaknesses.append(f"Dormant: no commits in over {days_since_commit} days.")
                cadence = "DORMANT - Project may be inactive or abandoned."
                rating = "AT_RISK"
        else:
            cadence = "UNKNOWN - Commit history telemetry unavailable."
            rating = "NEEDS_ATTENTION" if weaknesses else "HEALTHY"

        if notice:
            weaknesses.append(notice)

        return HealthAssessmentOutput(
            health_rating=rating,
            strengths=strengths or ["Repository is accessible."],
            weaknesses=weaknesses or ["No major governance weaknesses identified."],
            maintenance_cadence_verdict=cadence,
        )

