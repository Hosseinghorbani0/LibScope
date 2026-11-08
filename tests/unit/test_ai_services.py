"""
Unit tests for LibScope AI analysis services and deterministic fallbacks.
"""
import asyncio
from libscope.ai.client import AskAIClient
from libscope.ai.config import AIConfig
from libscope.ai.services import (
    PackageAnalysisService,
    AdoptionAnalysisService,
    HealthAnalysisService,
    SecurityAnalysisService,
    CompetitorAnalysisService,
    MaintainerRecommendationsService,
)


def _get_offline_client():
    return AskAIClient(config=AIConfig(api_key=""))


def test_package_analysis_service_deterministic_fallback():
    client = _get_offline_client()
    service = PackageAnalysisService(client=client)

    async def _run():
        res = await service.analyze(
            name="demo-pkg",
            ecosystem="pypi",
            latest_version="1.0.0",
            license_str="MIT",
            repo_url="https://github.com/demo/demo-pkg",
            monthly_downloads=500000,
            mirror_inclusive=True,
            growth_trend="accelerating",
            stars=1200,
            forks=150,
            open_issues=25,
            days_since_commit=5,
            days_since_release=14,
            verified_adoptions=42,
            vulnerabilities_count=0,
            critical_high_count=0,
            overall_score=88.5,
            confidence_level="HIGH",
            raw_description="A sample production library.",
        )
        assert "demo-pkg" in res.summary
        assert "88.5/100" in res.summary
        assert "42" in res.risks
        assert len(res.maintainer_recommendations) > 0
        assert "88.5" in res.competitive_position

    asyncio.run(_run())


def test_adoption_analysis_service_fallback_tiers():
    client = _get_offline_client()
    service = AdoptionAnalysisService(client=client)

    async def _run():
        # High genuine adoption
        res_high = await service.analyze("pkg-high", "pypi", 100000, 25)
        assert res_high.genuine_adoption_verdict == "HIGH_GENUINE"
        assert "organic adoption" in res_high.download_vs_adoption_analysis

        # Moderate adoption
        res_mod = await service.analyze("pkg-mod", "pypi", 50000, 8)
        assert res_mod.genuine_adoption_verdict == "MODERATE"

        # Low or subdependency
        res_low = await service.analyze("pkg-low", "pypi", 20000, 2)
        assert res_low.genuine_adoption_verdict == "LOW_OR_SUBDEPENDENCY"

        # Insufficient evidence
        res_none = await service.analyze("pkg-none", "pypi", 5000, 0)
        assert res_none.genuine_adoption_verdict == "INSUFFICIENT_EVIDENCE"

    asyncio.run(_run())


def test_health_analysis_service_fallback():
    client = _get_offline_client()
    service = HealthAnalysisService(client=client)

    async def _run():
        # Healthy active repository
        res_healthy = await service.analyze(
            repo_name="org/repo",
            stars=500,
            forks=50,
            watchers=20,
            open_issues=10,
            days_since_commit=12,
            days_since_release=45,
            has_readme=True,
            license_str="Apache-2.0",
            has_contributing=True,
            has_security_md=True,
            has_ci=True,
            is_archived=False,
        )
        assert res_healthy.health_rating in ("EXCELLENT", "HEALTHY")
        assert "HIGH_FREQUENCY" in res_healthy.maintenance_cadence_verdict
        assert len(res_healthy.strengths) >= 4

        # Archived repository
        res_archived = await service.analyze(
            repo_name="org/archived-repo",
            stars=1000,
            forks=200,
            watchers=50,
            open_issues=100,
            days_since_commit=400,
            days_since_release=400,
            has_readme=True,
            license_str="MIT",
            has_contributing=False,
            has_security_md=False,
            has_ci=False,
            is_archived=True,
        )
        assert res_archived.health_rating == "AT_RISK"
        assert "ARCHIVED" in res_archived.maintenance_cadence_verdict

    asyncio.run(_run())


def test_security_analysis_service_fallback():
    client = _get_offline_client()
    service = SecurityAnalysisService(client=client)

    async def _run():
        # Clean posture
        res_clean = await service.analyze("pkg-clean", 0, 0, has_security_policy=True)
        assert res_clean.posture == "CLEAN"
        assert "PUBLISHED" in res_clean.disclosure_policy_status

        # Action required
        res_crit = await service.analyze(
            "pkg-crit",
            vulnerabilities_count=3,
            critical_high_count=2,
            has_security_policy=False,
            advisories=[{"id": "GHSA-123", "summary": "Remote Code Execution"}],
        )
        assert res_crit.posture == "ACTION_REQUIRED"
        assert "ABSENT" in res_crit.disclosure_policy_status
        assert any("GHSA-123" in fix for fix in res_crit.priority_fixes)

    asyncio.run(_run())


def test_competitor_analysis_service_fallback():
    client = _get_offline_client()
    service = CompetitorAnalysisService(client=client)

    async def _run():
        records = [
            {"name": "pkg-a", "score": 92.0, "monthly_downloads": 1000000, "verified_adoptions": 150},
            {"name": "pkg-b", "score": 85.0, "monthly_downloads": 400000, "verified_adoptions": 60},
        ]
        res = await service.compare(records)
        assert res.market_leader == "pkg-a"
        assert len(res.key_differentiators) == 2
        assert len(res.recommendations_by_use_case) >= 1

    asyncio.run(_run())


def test_recommendations_service_fallback():
    client = _get_offline_client()
    service = MaintainerRecommendationsService(client=client)

    async def _run():
        res = await service.generate_recommendations(
            name="pkg-test",
            score=65.0,
            confidence="MODERATE",
            hygiene_gaps=["SECURITY.md missing", "CONTRIBUTING missing"],
            vulnerabilities_count=1,
            days_since_release=200,
        )
        assert any("vulnerabilities" in act.lower() for act in res.immediate_actions)
        assert any("security.md" in act.lower() for act in res.immediate_actions)
        assert any("contributing" in comm.lower() for comm in res.community_improvements)

    asyncio.run(_run())

