"""
LibScope Analysis Orchestrator.
Executes end-to-end multi-provider collection, analysis, scoring, and storage.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional
import uuid
from sqlalchemy.orm import Session
from libscope.analyzers.adoption import AdoptionAnalyzer
from libscope.analyzers.downloads import DownloadsAnalyzer
from libscope.analyzers.health import HealthAnalyzer
from libscope.analyzers.historical import HistoricalAnalyzer
from libscope.analyzers.repository import RepositoryAnalyzer
from libscope.analyzers.security import SecurityAnalyzer
from libscope.core.config import get_settings
from libscope.core.database import db_session
from libscope.core.logging import get_logger
from libscope.core.models import (
    AdoptionEvidence,
    AIAnalysis,
    AnalysisJob,
    CollectionRun,
    HealthFinding,
    MetricSnapshot,
    Package,
    Release,
    Repository,
    Score,
    SecurityFinding,
)
from libscope.providers.github import GitHubProvider
from libscope.providers.pypi import PyPIProvider
from libscope.providers.registry import get_provider_registry
from libscope.scoring.engine import ScoringEngine

logger = get_logger("api.orchestrator")


async def run_package_analysis(
    package_name: str,
    ecosystem: str = "pypi",
    enable_ai: bool = False,
    job_id: Optional[str] = None,
) -> Package:
    """
    Run complete intelligence analysis on a package and persist findings.
    """
    now = datetime.now(timezone.utc)
    settings = get_settings()
    registry = get_provider_registry()

    def update_job(status: str, progress: int, msg: str, error: Optional[str] = None, pkg_id: Optional[int] = None):
        if not job_id:
            return
        with db_session() as s:
            job = s.query(AnalysisJob).filter_by(id=job_id).first()
            if job:
                job.status = status
                job.progress = progress
                job.step_message = msg
                if error:
                    job.error_message = error
                if pkg_id:
                    job.package_id = pkg_id
                if status == "running" and not job.started_at:
                    job.started_at = datetime.now(timezone.utc)
                elif status in ("completed", "failed", "cancelled"):
                    job.completed_at = datetime.now(timezone.utc)

    update_job("running", 10, f"Resolving package '{package_name}' in {ecosystem}...")

    # 1. Fetch metadata & releases from primary provider
    provider = registry.get(ecosystem)
    if not provider:
        err = f"Unsupported ecosystem '{ecosystem}'"
        update_job("failed", 100, "Failed", error=err)
        raise ValueError(err)

    try:
        metadata = await provider.fetch_metadata(package_name)
    except Exception as exc:
        err = f"Failed to retrieve package '{package_name}' from {ecosystem}: {str(exc)}"
        logger.error(err)
        update_job("failed", 100, "Registry lookup failed", error=err)
        raise RuntimeError(err) from exc

    update_job("running", 25, "Fetching release history and download trends...")
    releases = await provider.fetch_releases(package_name)
    downloads = await provider.fetch_downloads(package_name)

    # 2. Analyze downloads
    dl_analyzer = DownloadsAnalyzer()
    dl_analytics = dl_analyzer.analyze(downloads, releases)

    # 3. Repository intelligence
    repo_data = None
    repo_intelligence = None
    community_profile = {}
    adoption_raw_findings = []

    target_repo_url = metadata.repository_url
    gh_provider = GitHubProvider()

    if target_repo_url and "github.com" in target_repo_url:
        update_job("running", 45, "Inspecting GitHub repository and community profile...")
        try:
            repo_data = await gh_provider.fetch_repository(target_repo_url)
            repo_analyzer = RepositoryAnalyzer()
            repo_intelligence = repo_analyzer.analyze(repo_data, releases)
            community_profile = await gh_provider.fetch_community_profile(repo_data.owner, repo_data.repo_name)
        except Exception as exc:
            logger.warning(f"Could not retrieve full GitHub repo metrics for {target_repo_url}: {exc}")

        # Adoption search across public codebases
        update_job("running", 60, "Scanning public manifests for independent adoption evidence...")
        try:
            adoption_raw_findings = await gh_provider.search_code_adoption(package_name, max_results=15)
        except Exception as exc:
            logger.warning(f"Adoption code search failed: {exc}")

    # 4. Process adoption discovery
    target_full_name = repo_data.full_name if repo_data else None
    adopt_analyzer = AdoptionAnalyzer()
    adopt_result = adopt_analyzer.process_raw_findings(package_name, target_full_name, adoption_raw_findings)

    # 5. Security intelligence (OSV)
    update_job("running", 75, "Checking OSV vulnerability database...")
    sec_analyzer = SecurityAnalyzer()
    sec_report = await sec_analyzer.check_vulnerabilities(package_name, ecosystem)

    # 6. Health analysis
    update_job("running", 85, "Evaluating project health and engineering discipline...")
    health_analyzer = HealthAnalyzer()
    health_report = health_analyzer.analyze(metadata, repo_data, releases, community_profile)

    # 7. Evidence-based scoring
    scoring_engine = ScoringEngine()
    days_since_commit = repo_intelligence.days_since_last_commit if repo_intelligence else None
    days_since_release = repo_intelligence.days_since_last_release if repo_intelligence else None
    is_archived = repo_data.is_archived if repo_data else False
    has_readme = any(f.check_name == "readme_present" and f.status == "pass" for f in health_report.findings)
    has_sec_policy = any(f.check_name == "security_policy_present" and f.status == "pass" for f in health_report.findings)

    score_result = scoring_engine.calculate_score(
        package_name=package_name,
        monthly_downloads=dl_analytics.monthly_downloads,
        stars=repo_data.stars if repo_data else 0,
        growth_rate_pct=dl_analytics.growth_rate_pct,
        recent_trend=dl_analytics.recent_trend_direction,
        confirmed_adoptions=adopt_result.confirmed_dependencies_count,
        possible_usages=adopt_result.possible_usage_count,
        days_since_commit=days_since_commit,
        days_since_release=days_since_release,
        is_archived=is_archived,
        has_readme=has_readme,
        has_docs_site=bool(metadata.homepage),
        description=metadata.description,
        has_license=bool(metadata.license or (repo_data and repo_data.license)),
        is_standard_license=any(f.check_name == "osi_license_detected" and f.status == "pass" for f in health_report.findings),
        has_ci=bool(community_profile.get("files", {}).get("workflows", False)),
        vulnerability_count=len(sec_report.vulnerabilities),
        critical_or_high=sec_report.critical_count + sec_report.high_count,
        has_security_policy=has_sec_policy,
    )

    # 8. AI Analyst (Optional)
    ai_result = None
    if enable_ai or settings.effective_ai_api_key:
        update_job("running", 92, "Synthesizing AI intelligence report...")
        try:
            from libscope.ai.interpreter import AIInterpreter
            interpreter = AIInterpreter()
            ai_result = await interpreter.interpret(
                package_name=package_name,
                ecosystem=ecosystem,
                latest_version=metadata.latest_version,
                license_str=metadata.license or (repo_data.license if repo_data else None),
                repo_url=metadata.repository_url,
                overall_score=score_result.overall_score,
                confidence_level=score_result.confidence_level,
                dimension_breakdown=score_result.explanation,
                monthly_downloads=dl_analytics.monthly_downloads,
                mirror_inclusive=dl_analytics.mirror_inclusive,
                growth_trend=dl_analytics.recent_trend_direction,
                stars=repo_data.stars if repo_data else 0,
                forks=repo_data.forks if repo_data else 0,
                open_issues=repo_data.open_issues if repo_data else 0,
                days_since_commit=days_since_commit,
                days_since_release=days_since_release,
                verified_adoptions_count=adopt_result.confirmed_dependencies_count,
                vulnerabilities_count=len(sec_report.vulnerabilities),
                critical_high_count=sec_report.critical_count + sec_report.high_count,
                raw_description=metadata.description,
            )
        except Exception as exc:
            logger.warning(f"AI Interpretation step failed gracefully: {exc}")

    # 9. Store results transactionally in database
    update_job("running", 97, "Saving intelligence snapshot to database...")
    package_id = None
    with db_session() as session:
        # Find or create Package
        pkg = session.query(Package).filter_by(name=metadata.name.lower(), ecosystem=ecosystem).first()
        if not pkg:
            pkg = Package(
                name=metadata.name.lower(),
                ecosystem=ecosystem,
                description=metadata.description,
                homepage=metadata.homepage,
                repository_url=metadata.repository_url,
                license=metadata.license or (repo_data.license if repo_data else None),
                latest_version=metadata.latest_version,
            )
            session.add(pkg)
            session.flush()
        else:
            pkg.description = metadata.description
            pkg.homepage = metadata.homepage
            pkg.repository_url = metadata.repository_url
            pkg.license = metadata.license or (repo_data.license if repo_data else None)
            pkg.latest_version = metadata.latest_version
            pkg.updated_at = now

        package_id = pkg.id

        # Update or create Repository
        if repo_data:
            r_obj = session.query(Repository).filter_by(package_id=pkg.id).first()
            if not r_obj:
                r_obj = Repository(
                    package_id=pkg.id,
                    owner=repo_data.owner,
                    repo_name=repo_data.repo_name,
                    full_name=repo_data.full_name,
                    url=repo_data.url,
                )
                session.add(r_obj)
            r_obj.stars = repo_data.stars
            r_obj.forks = repo_data.forks
            r_obj.open_issues = repo_data.open_issues
            r_obj.watchers = repo_data.watchers
            r_obj.default_branch = repo_data.default_branch
            r_obj.is_archived = repo_data.is_archived
            r_obj.is_fork = repo_data.is_fork
            r_obj.license = repo_data.license
            r_obj.last_commit_at = repo_data.last_commit_at
            r_obj.last_release_at = repo_data.last_release_at
            r_obj.updated_at = now

        # Add metric snapshot
        snapshot = MetricSnapshot(
            package_id=pkg.id,
            recorded_at=now,
            period="monthly",
            downloads_count=dl_analytics.monthly_downloads,
            growth_rate=dl_analytics.growth_rate_pct,
            stars_count=repo_data.stars if repo_data else None,
            forks_count=repo_data.forks if repo_data else None,
            issues_count=repo_data.open_issues if repo_data else None,
            raw_data=json.dumps({"daily": dl_analytics.daily_downloads, "weekly": dl_analytics.weekly_downloads}),
        )
        session.add(snapshot)

        # Clear old findings and add new ones
        session.query(HealthFinding).filter_by(package_id=pkg.id).delete()
        for h in health_report.findings:
            session.add(
                HealthFinding(
                    package_id=pkg.id,
                    category=h.category,
                    check_name=h.check_name,
                    status=h.status,
                    message=h.message,
                    details=json.dumps(h.details) if h.details else None,
                    detected_at=now,
                )
            )

        session.query(SecurityFinding).filter_by(package_id=pkg.id).delete()
        for s_item in sec_report.vulnerabilities:
            session.add(
                SecurityFinding(
                    package_id=pkg.id,
                    identifier=s_item.identifier,
                    severity=s_item.severity,
                    affected_range=s_item.affected_versions,
                    fixed_in=s_item.fixed_version,
                    source=s_item.source,
                    reference_url=s_item.reference_url,
                    title=s_item.title,
                    details=s_item.details,
                    remediation=s_item.remediation,
                    detected_at=now,
                )
            )

        # Store adoption evidence
        for adopt in adopt_result.findings:
            existing = session.query(AdoptionEvidence).filter_by(
                package_id=pkg.id,
                source_repo_full_name=adopt.source_repo_full_name,
                file_path=adopt.file_path,
            ).first()
            if not existing:
                session.add(
                    AdoptionEvidence(
                        package_id=pkg.id,
                        source_repo_url=adopt.source_repo_url,
                        source_repo_full_name=adopt.source_repo_full_name,
                        file_path=adopt.file_path,
                        evidence_type=adopt.evidence_type,
                        raw_match=adopt.raw_match,
                        stars=adopt.stars,
                        confidence_score=adopt.confidence_score,
                        discovered_at=now,
                    )
                )

        # Add Score
        pop_dim = score_result.dimensions.get("popularity")
        growth_dim = score_result.dimensions.get("growth")
        adopt_dim = score_result.dimensions.get("adoption")
        maint_dim = score_result.dimensions.get("maintenance")
        doc_dim = score_result.dimensions.get("documentation")
        qual_dim = score_result.dimensions.get("quality")
        sec_dim = score_result.dimensions.get("security")

        score_record = Score(
            package_id=pkg.id,
            version=score_result.version,
            calculated_at=score_result.calculated_at,
            overall_score=score_result.overall_score,
            confidence_level=score_result.confidence_level,
            popularity_score=pop_dim.score if pop_dim else None,
            growth_score=growth_dim.score if growth_dim else None,
            adoption_score=adopt_dim.score if adopt_dim else None,
            maintenance_score=maint_dim.score if maint_dim else None,
            documentation_score=doc_dim.score if doc_dim else None,
            quality_score=qual_dim.score if qual_dim else None,
            security_score=sec_dim.score if sec_dim else None,
            breakdown=score_result.breakdown_json,
            explanation=score_result.explanation,
        )
        session.add(score_record)

        # Add AI analysis if present
        if ai_result:
            ai_record = AIAnalysis(
                package_id=pkg.id,
                provider=ai_result.provider,
                model=ai_result.model,
                summary=ai_result.summary,
                risks=ai_result.risks,
                opportunities=ai_result.opportunities,
                maintainer_recommendations=ai_result.maintainer_recommendations,
                competitive_position=ai_result.competitive_position,
                raw_response=ai_result.raw_response,
                generated_at=ai_result.generated_at,
            )
            session.add(ai_record)

    update_job("completed", 100, f"Analysis for '{package_name}' completed successfully.", pkg_id=package_id)

    # Re-query package to return
    with db_session() as session:
        return session.query(Package).filter_by(id=package_id).first()

