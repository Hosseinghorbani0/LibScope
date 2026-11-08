"""
Evidence-Based Scoring Engine.
Calculates transparent, explainable scores across multi-dimensional quality and adoption indicators.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from typing import Any, Dict, List, Optional
from libscope.core.logging import get_logger

logger = get_logger("scoring.engine")

SCORING_MODEL_VERSION = "v1.0.0"


@dataclass
class DimensionScore:
    name: str
    score: Optional[float]  # 0 to 100, None if insufficient data
    weight: float
    confidence: str  # high, medium, low, none
    explanation: str
    inputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreResult:
    package_name: str
    version: str
    calculated_at: datetime
    overall_score: Optional[float]  # 0 to 100, or None if insufficient evidence
    confidence_level: str           # "high", "medium", "low"
    is_insufficient_data: bool
    dimensions: Dict[str, DimensionScore] = field(default_factory=dict)
    explanation: str = ""
    breakdown_json: str = ""


class ScoringEngine:
    """
    Transparent, explainable scoring engine.
    Weights:
      - Adoption: 0.25 (Key differentiator: verified independent code adoption)
      - Maintenance: 0.20 (Commit frequency, release discipline, responsiveness)
      - Security Posture: 0.15 (Zero known vulnerabilities, security policy)
      - Documentation: 0.15 (README, setup guide, examples)
      - Engineering Quality: 0.10 (CI/CD, tests, license)
      - Popularity: 0.08 (Downloads, stars)
      - Growth: 0.07 (Trajectory, moving average delta)
    """

    WEIGHTS = {
        "adoption": 0.25,
        "maintenance": 0.20,
        "security": 0.15,
        "documentation": 0.15,
        "quality": 0.10,
        "popularity": 0.08,
        "growth": 0.07,
    }

    def _calc_popularity(self, monthly_downloads: int, stars: int) -> DimensionScore:
        inputs = {"monthly_downloads": monthly_downloads, "stars": stars}
        if monthly_downloads == 0 and stars == 0:
            return DimensionScore(
                name="popularity",
                score=None,
                weight=self.WEIGHTS["popularity"],
                confidence="none",
                explanation="No download or star metrics recorded.",
                inputs=inputs,
            )

        # Logarithmic scaling: 1k dl -> 30, 100k dl -> 70, 1M+ dl -> 90+
        dl_score = 0.0
        if monthly_downloads > 0:
            dl_score = min(100.0, math.log10(monthly_downloads) * 15.0)

        star_score = 0.0
        if stars > 0:
            star_score = min(100.0, math.log10(stars) * 25.0)

        combined = round(0.6 * dl_score + 0.4 * star_score, 1)
        conf = "high" if monthly_downloads > 0 and stars > 0 else "medium"
        return DimensionScore(
            name="popularity",
            score=min(100.0, combined),
            weight=self.WEIGHTS["popularity"],
            confidence=conf,
            explanation=f"Scaled from {monthly_downloads:,} monthly downloads and {stars:,} GitHub stars.",
            inputs=inputs,
        )

    def _calc_growth(self, growth_rate_pct: Optional[float], recent_trend: str) -> DimensionScore:
        inputs = {"growth_rate_pct": growth_rate_pct, "recent_trend": recent_trend}
        if growth_rate_pct is None:
            return DimensionScore(
                name="growth",
                score=None,
                weight=self.WEIGHTS["growth"],
                confidence="low",
                explanation="Insufficient historical snapshots to compute exact growth rate.",
                inputs=inputs,
            )

        # Bound score between 10 and 100
        score = 60.0 + (growth_rate_pct * 0.5)
        score = max(10.0, min(100.0, score))

        return DimensionScore(
            name="growth",
            score=round(score, 1),
            weight=self.WEIGHTS["growth"],
            confidence="medium",
            explanation=f"Based on recent growth rate of {growth_rate_pct:+.1f}% ({recent_trend}).",
            inputs=inputs,
        )

    def _calc_adoption(self, confirmed_adoptions: int, possible_usages: int) -> DimensionScore:
        inputs = {"confirmed_adoptions": confirmed_adoptions, "possible_usages": possible_usages}
        # Strong weighting on verified independent adoption
        if confirmed_adoptions == 0 and possible_usages == 0:
            return DimensionScore(
                name="adoption",
                score=None,
                weight=self.WEIGHTS["adoption"],
                confidence="none",
                explanation="No verified independent external adoption found in public manifests.",
                inputs=inputs,
            )

        base = 40.0 + min(50.0, confirmed_adoptions * 3.5) + min(10.0, possible_usages * 1.0)
        score = min(100.0, base)
        conf = "high" if confirmed_adoptions >= 3 else "medium"

        return DimensionScore(
            name="adoption",
            score=round(score, 1),
            weight=self.WEIGHTS["adoption"],
            confidence=conf,
            explanation=f"Verified in {confirmed_adoptions} independent public project dependency declarations.",
            inputs=inputs,
        )

    def _calc_maintenance(
        self,
        days_since_commit: Optional[int],
        days_since_release: Optional[int],
        is_archived: bool,
    ) -> DimensionScore:
        inputs = {
            "days_since_commit": days_since_commit,
            "days_since_release": days_since_release,
            "is_archived": is_archived,
        }
        if is_archived:
            return DimensionScore(
                name="maintenance",
                score=0.0,
                weight=self.WEIGHTS["maintenance"],
                confidence="high",
                explanation="Repository is explicitly ARCHIVED. No active maintenance.",
                inputs=inputs,
            )

        if days_since_commit is None:
            return DimensionScore(
                name="maintenance",
                score=None,
                weight=self.WEIGHTS["maintenance"],
                confidence="none",
                explanation="Commit timeline unavailable.",
                inputs=inputs,
            )

        # Score based on freshness
        if days_since_commit <= 14:
            score = 95.0
            desc = f"Very active; last commit {days_since_commit} days ago."
        elif days_since_commit <= 45:
            score = 85.0
            desc = f"Active maintenance; last commit {days_since_commit} days ago."
        elif days_since_commit <= 180:
            score = 65.0
            desc = f"Moderate maintenance; last commit {days_since_commit} days ago."
        elif days_since_commit <= 365:
            score = 40.0
            desc = f"Slow maintenance pace; last commit {days_since_commit} days ago."
        else:
            score = 15.0
            desc = f"Stale or dormant; no commits in {days_since_commit} days."

        if days_since_release and days_since_release > 365:
            score = max(5.0, score - 15.0)
            desc += f" Last release was {days_since_release} days ago."

        return DimensionScore(
            name="maintenance",
            score=round(score, 1),
            weight=self.WEIGHTS["maintenance"],
            confidence="high",
            explanation=desc,
            inputs=inputs,
        )

    def _calc_documentation(self, has_readme: bool, has_docs_site: bool, description: Optional[str]) -> DimensionScore:
        inputs = {"has_readme": has_readme, "has_docs_site": has_docs_site, "has_desc": bool(description)}
        score = 20.0
        if description and len(description) > 10:
            score += 15.0
        if has_readme:
            score += 45.0
        if has_docs_site:
            score += 20.0

        return DimensionScore(
            name="documentation",
            score=min(100.0, score),
            weight=self.WEIGHTS["documentation"],
            confidence="high",
            explanation=f"Evaluated documentation artifacts: README={has_readme}, Documentation Link={has_docs_site}.",
            inputs=inputs,
        )

    def _calc_quality(self, has_license: bool, is_standard_license: bool, has_ci: bool) -> DimensionScore:
        inputs = {"has_license": has_license, "is_standard_license": is_standard_license, "has_ci": has_ci}
        score = 20.0
        if has_license:
            score += 35.0
        if is_standard_license:
            score += 15.0
        if has_ci:
            score += 30.0

        return DimensionScore(
            name="quality",
            score=min(100.0, score),
            weight=self.WEIGHTS["quality"],
            confidence="medium",
            explanation=f"License present={has_license}, Standard OSI={is_standard_license}, CI pipeline={has_ci}.",
            inputs=inputs,
        )

    def _calc_security(self, vulnerability_count: int, critical_or_high: int, has_security_policy: bool) -> DimensionScore:
        inputs = {
            "vulnerability_count": vulnerability_count,
            "critical_or_high": critical_or_high,
            "has_security_policy": has_security_policy,
        }
        if critical_or_high > 0:
            score = max(10.0, 50.0 - (critical_or_high * 20.0))
            desc = f"Contains {critical_or_high} unresolved Critical/High vulnerabilities."
            conf = "high"
        elif vulnerability_count > 0:
            score = 65.0
            desc = f"Contains {vulnerability_count} known moderate/low vulnerabilities."
            conf = "high"
        else:
            score = 90.0
            if has_security_policy:
                score += 10.0
            desc = "No known vulnerabilities reported in OSV vulnerability database."
            conf = "medium"

        return DimensionScore(
            name="security",
            score=round(score, 1),
            weight=self.WEIGHTS["security"],
            confidence=conf,
            explanation=desc,
            inputs=inputs,
        )

    def calculate_score(
        self,
        package_name: str,
        monthly_downloads: int = 0,
        stars: int = 0,
        growth_rate_pct: Optional[float] = None,
        recent_trend: str = "stable",
        confirmed_adoptions: int = 0,
        possible_usages: int = 0,
        days_since_commit: Optional[int] = None,
        days_since_release: Optional[int] = None,
        is_archived: bool = False,
        has_readme: bool = True,
        has_docs_site: bool = False,
        description: Optional[str] = None,
        has_license: bool = True,
        is_standard_license: bool = True,
        has_ci: bool = False,
        vulnerability_count: int = 0,
        critical_or_high: int = 0,
        has_security_policy: bool = False,
    ) -> ScoreResult:
        now = datetime.now(timezone.utc)

        # Calculate individual dimensions
        dim_pop = self._calc_popularity(monthly_downloads, stars)
        dim_growth = self._calc_growth(growth_rate_pct, recent_trend)
        dim_adopt = self._calc_adoption(confirmed_adoptions, possible_usages)
        dim_maint = self._calc_maintenance(days_since_commit, days_since_release, is_archived)
        dim_doc = self._calc_documentation(has_readme, has_docs_site, description)
        dim_qual = self._calc_quality(has_license, is_standard_license, has_ci)
        dim_sec = self._calc_security(vulnerability_count, critical_or_high, has_security_policy)

        dimensions = {
            "popularity": dim_pop,
            "growth": dim_growth,
            "adoption": dim_adopt,
            "maintenance": dim_maint,
            "documentation": dim_doc,
            "quality": dim_qual,
            "security": dim_sec,
        }

        # Handle missing data & confidence
        valid_dims = [d for d in dimensions.values() if d.score is not None]
        total_weight = sum(d.weight for d in valid_dims)

        # Rule: If critical signals are missing, return "Insufficient data"
        if len(valid_dims) < 4 or total_weight < 0.50 or (monthly_downloads == 0 and stars == 0 and confirmed_adoptions == 0):
            return ScoreResult(
                package_name=package_name,
                version=SCORING_MODEL_VERSION,
                calculated_at=now,
                overall_score=None,
                confidence_level="low",
                is_insufficient_data=True,
                dimensions=dimensions,
                explanation="Insufficient data. Not enough verifiable evidence to calculate an honest quality score.",
                breakdown_json=json.dumps({k: asdict(v) for k, v in dimensions.items()}),
            )

        # Weighted calculation normalized to valid weights
        weighted_sum = sum(d.score * d.weight for d in valid_dims)
        overall = round(weighted_sum / total_weight, 1)

        # Determine overall confidence
        high_conf_count = sum(1 for d in valid_dims if d.confidence == "high")
        if high_conf_count >= 4 and len(valid_dims) >= 6:
            overall_conf = "high"
        elif len(valid_dims) >= 4:
            overall_conf = "medium"
        else:
            overall_conf = "low"

        explanation = (
            f"Overall score of {overall}/100 ({overall_conf} confidence). "
            f"Adoption: {dim_adopt.score}, Maintenance: {dim_maint.score}, Security: {dim_sec.score}, "
            f"Quality: {dim_qual.score}, Documentation: {dim_doc.score}, Popularity: {dim_pop.score}."
        )

        return ScoreResult(
            package_name=package_name,
            version=SCORING_MODEL_VERSION,
            calculated_at=now,
            overall_score=overall,
            confidence_level=overall_conf,
            is_insufficient_data=False,
            dimensions=dimensions,
            explanation=explanation,
            breakdown_json=json.dumps({k: asdict(v) for k, v in dimensions.items()}),
        )
