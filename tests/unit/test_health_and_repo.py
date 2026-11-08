"""
Unit tests for Project Health and Repository Intelligence Analyzers.
"""
from datetime import datetime, timezone, timedelta
from libscope.analyzers.health import HealthAnalyzer
from libscope.analyzers.repository import RepositoryAnalyzer
from libscope.providers.base import NormalizedMetadata, NormalizedRelease, NormalizedRepository


def test_repository_analyzer_detects_archival_and_dormancy():
    now = datetime.now(timezone.utc)
    old_date = now - timedelta(days=400)

    repo = NormalizedRepository(
        owner="test-owner",
        repo_name="old-repo",
        full_name="test-owner/old-repo",
        url="https://github.com/test-owner/old-repo",
        stars=500,
        forks=50,
        is_archived=True,
        last_commit_at=old_date,
    )

    analyzer = RepositoryAnalyzer()
    res = analyzer.analyze(repo)

    assert res.is_archived is True
    assert res.activity_status == "archived"
    assert any("ARCHIVED" in w for w in res.warnings)


def test_health_analyzer_evaluates_license_and_community_files():
    metadata = NormalizedMetadata(
        name="good-pkg",
        ecosystem="pypi",
        license="MIT",
        latest_version="1.0.0",
    )
    repo = NormalizedRepository(
        owner="good",
        repo_name="good-pkg",
        full_name="good/good-pkg",
        url="https://github.com/good/good-pkg",
        license="MIT",
        last_commit_at=datetime.now(timezone.utc),
    )
    community = {
        "files": {
            "readme": {"url": "https://..."},
            "contributing": {"url": "https://..."},
            "security": {"url": "https://..."},
        }
    }

    analyzer = HealthAnalyzer()
    res = analyzer.analyze(metadata, repo, community_profile=community)

    assert res.overall_health_rating in ("excellent", "healthy")
    check_names = [f.check_name for f in res.findings]
    assert "osi_license_detected" in check_names
    assert "readme_present" in check_names
    assert "security_policy_present" in check_names

