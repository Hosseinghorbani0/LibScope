"""
Pydantic output schemas for structured AI services in LibScope.
"""
from pydantic import BaseModel, ConfigDict, Field


class BaseAIOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")


class PackageAnalysisOutput(BaseAIOutput):
    """Structured executive package intelligence output."""
    summary: str = Field(..., description="2-3 paragraph executive summary of the package standing.")
    risks: str = Field(..., description="Bullet points detailing observed risks.")
    opportunities: str = Field(..., description="Potential advantages or growth areas.")
    maintainer_recommendations: str = Field(..., description="Actionable recommendations for package maintainers.")
    competitive_position: str = Field(..., description="Assessment of position in ecosystem.")


class RiskAssessmentOutput(BaseAIOutput):
    """Detailed risk assessment output."""
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, or CRITICAL")
    maintenance_risks: list[str] = Field(default_factory=list)
    adoption_risks: list[str] = Field(default_factory=list)
    security_risks: list[str] = Field(default_factory=list)
    license_risks: list[str] = Field(default_factory=list)
    summary: str = Field(...)


class MaintainerRecommendationsOutput(BaseAIOutput):
    """Prioritized recommendations for project maintainers."""
    immediate_actions: list[str] = Field(default_factory=list, description="Immediate hygiene fixes (1-2 weeks)")
    medium_term_goals: list[str] = Field(default_factory=list, description="Medium term structural goals")
    community_improvements: list[str] = Field(default_factory=list, description="Contributor onboarding and policies")


class CompetitorComparisonOutput(BaseAIOutput):
    """Comparative analysis across competing packages."""
    comparative_summary: str = Field(...)
    market_leader: str = Field(...)
    recommendations_by_use_case: list[str] = Field(default_factory=list)
    key_differentiators: list[str] = Field(default_factory=list)


class AdoptionAssessmentOutput(BaseAIOutput):
    """Adoption discovery interpretation."""
    genuine_adoption_verdict: str = Field(..., description="HIGH_GENUINE, MODERATE, LOW_OR_SUBDEPENDENCY, or INSUFFICIENT_EVIDENCE")
    adoption_summary: str = Field(...)
    real_world_use_cases: list[str] = Field(default_factory=list)
    download_vs_adoption_analysis: str = Field(...)


class HealthAssessmentOutput(BaseAIOutput):
    """Project health interpretation."""
    health_rating: str = Field(..., description="EXCELLENT, HEALTHY, NEEDS_ATTENTION, or AT_RISK")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    maintenance_cadence_verdict: str = Field(...)


class SecurityAssessmentOutput(BaseAIOutput):
    """Security finding interpretation."""
    posture: str = Field(..., description="CLEAN, ELEVATED_RISK, or ACTION_REQUIRED")
    remediation_summary: str = Field(...)
    priority_fixes: list[str] = Field(default_factory=list)
    disclosure_policy_status: str = Field(...)

