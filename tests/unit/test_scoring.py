"""
Unit tests for the evidence-based scoring engine.
"""
from libscope.scoring.engine import ScoringEngine


def test_scoring_returns_insufficient_data_when_evidence_is_lacking():
    engine = ScoringEngine()
    # No downloads, no stars, no commits, no license, etc.
    res = engine.calculate_score(
        package_name="ghost-pkg",
        monthly_downloads=0,
        stars=0,
        days_since_commit=None,
        has_readme=False,
        has_license=False,
    )
    assert res.is_insufficient_data is True
    assert res.overall_score is None
    assert "Insufficient data" in res.explanation
    assert res.confidence_level == "low"


def test_scoring_weights_verified_adoption_and_maintenance():
    engine = ScoringEngine()
    res = engine.calculate_score(
        package_name="healthy-pkg",
        monthly_downloads=50000,
        stars=1200,
        growth_rate_pct=15.0,
        recent_trend="growing",
        confirmed_adoptions=8,
        possible_usages=2,
        days_since_commit=10,
        days_since_release=30,
        is_archived=False,
        has_readme=True,
        has_docs_site=True,
        description="A well-maintained open source package",
        has_license=True,
        is_standard_license=True,
        has_ci=True,
        vulnerability_count=0,
        critical_or_high=0,
        has_security_policy=True,
    )

    assert res.is_insufficient_data is False
    assert res.overall_score is not None
    assert res.overall_score >= 80.0
    assert res.confidence_level == "high"
    assert res.dimensions["adoption"].score >= 70.0
    assert res.dimensions["maintenance"].score >= 80.0
    assert res.dimensions["security"].score == 100.0


def test_scoring_penalizes_archived_projects():
    engine = ScoringEngine()
    res = engine.calculate_score(
        package_name="archived-pkg",
        monthly_downloads=100000,
        stars=5000,
        days_since_commit=400,
        is_archived=True,
        has_readme=True,
        has_license=True,
    )
    assert res.dimensions["maintenance"].score == 0.0
    assert "ARCHIVED" in res.dimensions["maintenance"].explanation


def test_scoring_penalizes_critical_vulnerabilities():
    engine = ScoringEngine()
    res = engine.calculate_score(
        package_name="vulnerable-pkg",
        monthly_downloads=20000,
        stars=500,
        days_since_commit=20,
        has_license=True,
        vulnerability_count=3,
        critical_or_high=2,
    )
    assert res.dimensions["security"].score <= 30.0
    assert "Critical/High" in res.dimensions["security"].explanation


def test_failed_security_lookup_is_not_scored_as_clean():
    res = ScoringEngine().calculate_score(
        package_name="unknown-security-status",
        monthly_downloads=20000,
        stars=500,
        days_since_commit=20,
        has_license=True,
        security_lookup_status="failed",
    )

    assert res.dimensions["security"].score is None
    assert "inferred" in res.dimensions["security"].explanation
