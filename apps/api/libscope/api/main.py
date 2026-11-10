"""
FastAPI REST API Application for LibScope.
"""
import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from libscope.analyzers.competitor import CompetitorAnalyzer
from libscope.analyzers.health import normalize_health_rating
from libscope.analyzers.historical import HistoricalAnalyzer
from libscope.api.demo import seed_demo_data
from libscope.api.orchestrator import run_package_analysis
from libscope.api.security import rate_limit_expensive_requests, require_api_key
from libscope.core.config import get_settings
from libscope.core.database import get_db, init_db
from libscope.core.logging import get_logger, setup_logging
from libscope.core.models import (
    AdoptionEvidence,
    AIAnalysis,
    AnalysisJob,
    HealthFinding,
    MetricSnapshot,
    Package,
    Release,
    Report,
    Repository,
    Score,
    SecurityFinding,
)
from libscope.core.schemas import (
    AdoptionEvidenceRead,
    AIAnalysisRead,
    AnalysisJobCreate,
    AnalysisJobRead,
    CompareRequest,
    CompareResponse,
    DashboardSummaryRead,
    HealthFindingRead,
    MetricSnapshotRead,
    PackageDetailRead,
    PackageRead,
    ReleaseRead,
    ReportGenerateRequest,
    ReportRead,
    ScoreHistoryPointRead,
    ScoreRead,
    SecurityFindingRead,
)
from libscope.providers.registry import get_provider_registry
from libscope.reporting.generator import ReportGenerator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

settings = get_settings()
setup_logging(level=settings.log_level)
logger = get_logger("api.main")


def _snapshot_metadata(snapshot: MetricSnapshot | None) -> dict:
    if not snapshot or not snapshot.raw_data:
        return {}
    try:
        data = json.loads(snapshot.raw_data)
    except (TypeError, json.JSONDecodeError):
        logger.warning("Ignoring malformed metric snapshot metadata for snapshot %s", snapshot.id)
        return {}
    return data if isinstance(data, dict) else {}


def _days_since(timestamp: datetime | None, now: datetime) -> int | None:
    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return max(0, (now - timestamp).days)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    logger.info(f"LibScope API {settings.app_version} initialized successfully.")
    yield


app = FastAPI(
    title="LibScope API",
    description="Open-Source Software Intelligence Platform. Beyond Downloads.",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "libscope-api",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/v1/version", tags=["System"])
def get_version():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "ai_provider": settings.ai_provider,
        "ai_configured": bool(settings.effective_ai_api_key),
        "github_token_configured": bool(settings.effective_github_token),
    }


@app.get("/api/v1/providers", tags=["Providers"])
def list_providers():
    registry = get_provider_registry()
    return {"providers": registry.list_providers()}


# --- Analysis Jobs ---
@app.post("/api/v1/analyze", response_model=AnalysisJobRead, status_code=status.HTTP_202_ACCEPTED, tags=["Analysis"])
async def trigger_analysis(
    req: AnalysisJobCreate,
    background_tasks: BackgroundTasks,
    run_sync: bool = Query(default=False, description="Run synchronously and wait for completion (for CLI/scripts)"),
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
    _rate_limit: None = Depends(rate_limit_expensive_requests),
):
    job_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=job_id,
        package_name=req.package_name.strip(),
        ecosystem=req.ecosystem.strip().lower(),
        status="queued",
        progress=0,
        step_message="Analysis job registered",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if run_sync:
        await run_package_analysis(
            package_name=req.package_name.strip(),
            ecosystem=req.ecosystem.strip().lower(),
            enable_ai=req.enable_ai,
            job_id=job_id,
        )
        db.refresh(job)
        return job

    # Run in background
    background_tasks.add_task(
        run_package_analysis,
        package_name=req.package_name.strip(),
        ecosystem=req.ecosystem.strip().lower(),
        enable_ai=req.enable_ai,
        job_id=job_id,
    )
    return job


@app.get("/api/v1/jobs/{job_id}", response_model=AnalysisJobRead, tags=["Analysis"])
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job


# --- Package Intelligence ---
@app.get("/api/v1/packages", response_model=list[PackageRead], tags=["Packages"])
def list_packages(
    search: str | None = None,
    ecosystem: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Package)
    if search:
        query = query.filter(Package.name.ilike(f"%{search.strip()}%"))
    if ecosystem:
        query = query.filter(Package.ecosystem == ecosystem.strip().lower())
    return query.order_by(desc(Package.updated_at)).offset(offset).limit(limit).all()


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummaryRead, tags=["Dashboard"])
def get_dashboard_summary(
    recent_limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    return {
        "total_packages": db.query(func.count(Package.id)).scalar() or 0,
        "scored_packages": db.query(func.count(func.distinct(Score.package_id))).scalar() or 0,
        "linked_repositories": db.query(func.count(Repository.id)).scalar() or 0,
        "latest_package_update": db.query(func.max(Package.updated_at)).scalar(),
        "recent_jobs": (
            db.query(AnalysisJob)
            .order_by(desc(AnalysisJob.created_at), desc(AnalysisJob.id))
            .limit(recent_limit)
            .all()
        ),
    }


@app.get("/api/v1/packages/{package_id}", response_model=PackageDetailRead, tags=["Packages"])
def get_package_detail(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    latest_score = db.query(Score).filter_by(package_id=package_id).order_by(desc(Score.calculated_at)).first()
    latest_ai = db.query(AIAnalysis).filter_by(package_id=package_id).order_by(desc(AIAnalysis.generated_at)).first()
    recent_releases = db.query(Release).filter_by(package_id=package_id).count()
    adoption_count = db.query(AdoptionEvidence).filter_by(package_id=package_id).count()
    vuln_count = db.query(SecurityFinding).filter_by(package_id=package_id).count()

    latest_snap = db.query(MetricSnapshot).filter_by(package_id=package_id).order_by(desc(MetricSnapshot.recorded_at)).first()
    monthly_dl = latest_snap.downloads_count if latest_snap else None

    return PackageDetailRead(
        id=pkg.id,
        name=pkg.name,
        ecosystem=pkg.ecosystem,
        description=pkg.description,
        homepage=pkg.homepage,
        repository_url=pkg.repository_url,
        license=pkg.license,
        latest_version=pkg.latest_version,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        repository=pkg.repository,
        latest_score=latest_score,
        latest_ai_analysis=latest_ai,
        recent_releases_count=recent_releases,
        total_downloads_30d=monthly_dl,
        adoption_count=adoption_count,
        vulnerabilities_count=vuln_count,
    )


@app.get("/api/v1/packages/{package_id}/analytics", response_model=list[MetricSnapshotRead], tags=["Analytics"])
def get_package_analytics(
    package_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return (
        db.query(MetricSnapshot)
        .filter_by(package_id=package_id)
        .order_by(MetricSnapshot.recorded_at, MetricSnapshot.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/api/v1/packages/{package_id}/history", tags=["Analytics"])
def get_package_history(
    package_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    total = db.query(MetricSnapshot).filter_by(package_id=package_id).count()
    snapshots = (
        db.query(MetricSnapshot)
        .filter_by(package_id=package_id)
        .order_by(desc(MetricSnapshot.recorded_at), desc(MetricSnapshot.id))
        .limit(limit)
        .all()
    )
    snapshots.reverse()
    result = HistoricalAnalyzer().analyze_snapshots(
        pkg.name,
        [
            {
                "recorded_at": snapshot.recorded_at,
                "downloads_count": snapshot.downloads_count,
                "stars_count": snapshot.stars_count,
                "forks_count": snapshot.forks_count,
            }
            for snapshot in snapshots
        ],
    )
    return {
        "package_name": result.package_name,
        "analyzed_at": result.analyzed_at,
        "total_snapshots_recorded": total,
        "returned_snapshots": len(snapshots),
        "deltas": [delta.__dict__ for delta in result.deltas],
        "historical_chart_points": result.historical_chart_points,
        "summary": result.summary,
    }


@app.get("/api/v1/packages/{package_id}/health", response_model=list[HealthFindingRead], tags=["Health"])
def get_package_health(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(HealthFinding).filter_by(package_id=package_id).all()


@app.get("/api/v1/packages/{package_id}/adoption", response_model=list[AdoptionEvidenceRead], tags=["Adoption"])
def get_package_adoption(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(AdoptionEvidence).filter_by(package_id=package_id).order_by(desc(AdoptionEvidence.stars)).all()


@app.get("/api/v1/packages/{package_id}/adoption/status", tags=["Adoption"])
def get_package_adoption_status(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    snapshot = (
        db.query(MetricSnapshot)
        .filter_by(package_id=package_id)
        .order_by(desc(MetricSnapshot.recorded_at))
        .first()
    )
    metadata = _snapshot_metadata(snapshot)
    return {
        "status": metadata.get("adoption_status", "not_checked"),
        "caveats": metadata.get("adoption_caveats", []),
    }


@app.get("/api/v1/packages/{package_id}/security", response_model=list[SecurityFindingRead], tags=["Security"])
def get_package_security(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(SecurityFinding).filter_by(package_id=package_id).all()


@app.get("/api/v1/packages/{package_id}/security/status", tags=["Security"])
def get_package_security_status(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    snapshot = (
        db.query(MetricSnapshot)
        .filter_by(package_id=package_id)
        .order_by(desc(MetricSnapshot.recorded_at))
        .first()
    )
    metadata = _snapshot_metadata(snapshot)
    return {
        "status": metadata.get("security_status", "not_checked"),
        "checked_at": metadata.get("security_checked_at"),
        "caveats": metadata.get("security_caveats", []),
    }


@app.get("/api/v1/packages/{package_id}/releases", response_model=list[ReleaseRead], tags=["Releases"])
def get_package_releases(
    package_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return (
        db.query(Release)
        .filter_by(package_id=package_id)
        .order_by(desc(Release.release_date), desc(Release.id))
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/api/v1/packages/{package_id}/score", response_model=ScoreRead | None, tags=["Scoring"])
def get_package_score(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(Score).filter_by(package_id=package_id).order_by(desc(Score.calculated_at)).first()


@app.get(
    "/api/v1/packages/{package_id}/score-history",
    response_model=list[ScoreHistoryPointRead],
    tags=["Scoring"],
)
def get_package_score_history(
    package_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    history = (
        db.query(Score)
        .filter_by(package_id=package_id)
        .order_by(desc(Score.calculated_at), desc(Score.id))
        .limit(limit)
        .all()
    )
    history.reverse()
    return history


@app.get("/api/v1/packages/{package_id}/ai", response_model=AIAnalysisRead | None, tags=["AI"])
def get_package_ai_analysis(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(AIAnalysis).filter_by(package_id=package_id).order_by(desc(AIAnalysis.generated_at)).first()


# --- Competitor Comparison ---
@app.post("/api/v1/compare", response_model=CompareResponse, tags=["Comparison"])
def compare_packages(
    req: CompareRequest,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_expensive_requests),
):
    comparison_time = datetime.now(UTC)
    packages: list[Package] = []
    if req.package_ids:
        packages = db.query(Package).filter(Package.id.in_(req.package_ids)).all()
    elif req.package_names:
        clean_names = [n.strip().lower() for n in req.package_names]
        packages = db.query(Package).filter(Package.name.in_(clean_names)).all()

    if len(packages) < 2:
        raise HTTPException(
            status_code=400,
            detail="Comparison requires at least 2 analyzed packages in database. Please run analysis on them first.",
        )

    analyzer = CompetitorAnalyzer()
    pkg_data_list = []
    for p in packages:
        latest_score = db.query(Score).filter_by(package_id=p.id).order_by(desc(Score.calculated_at)).first()
        latest_snap = db.query(MetricSnapshot).filter_by(package_id=p.id).order_by(desc(MetricSnapshot.recorded_at)).first()
        repo = p.repository
        adoptions = db.query(AdoptionEvidence).filter_by(package_id=p.id).count()
        vulns = db.query(SecurityFinding).filter_by(package_id=p.id).count()
        snapshot_metadata = _snapshot_metadata(latest_snap)
        adoption_status = snapshot_metadata.get("adoption_status", "not_checked")
        security_status = snapshot_metadata.get("security_status", "not_checked")

        pkg_data_list.append({
            "name": p.name,
            "ecosystem": p.ecosystem,
            "overall_score": latest_score.overall_score if latest_score else None,
            "confidence": latest_score.confidence_level if latest_score else "low",
            "monthly_downloads": latest_snap.downloads_count if latest_snap else None,
            "weekly_downloads": 0,
            "stars": repo.stars if repo else None,
            "forks": repo.forks if repo else None,
            "open_issues": repo.open_issues if repo else None,
            "latest_version": p.latest_version,
            "days_since_last_release": _days_since(repo.last_release_at if repo else None, comparison_time),
            "days_since_last_commit": _days_since(repo.last_commit_at if repo else None, comparison_time),
            "confirmed_adoptions_count": adoptions if adoption_status == "checked" else None,
            "vulnerabilities_count": vulns if security_status == "checked" else None,
            "license": p.license,
        })

    report = analyzer.compare(pkg_data_list)
    return CompareResponse(
        compared_at=report.compared_at,
        packages=[
            {
                "package_name": it.package_name,
                "ecosystem": it.ecosystem,
                "overall_score": it.overall_score,
                "confidence": it.confidence,
                "monthly_downloads": it.monthly_downloads,
                "stars": it.stars,
                "forks": it.forks,
                "open_issues": it.open_issues,
                "latest_version": it.latest_version,
                "last_release_age_days": it.days_since_last_release,
                "verified_adoptions": it.confirmed_adoptions_count,
                "vulnerabilities_count": it.vulnerabilities_count,
                "license": it.license,
                "comparability_notes": it.comparability_notes,
            }
            for it in report.packages
        ],
        summary=report.comparative_summary,
    )


# --- Reports ---
@app.post("/api/v1/reports/generate", response_model=ReportRead, tags=["Reports"])
def generate_report(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
    _rate_limit: None = Depends(rate_limit_expensive_requests),
):
    pkg = db.query(Package).filter_by(id=req.package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    score = db.query(Score).filter_by(package_id=pkg.id).order_by(desc(Score.calculated_at)).first()
    repo = pkg.repository
    snap = db.query(MetricSnapshot).filter_by(package_id=pkg.id).order_by(desc(MetricSnapshot.recorded_at)).first()
    snapshot_metadata = _snapshot_metadata(snap)
    health_findings = db.query(HealthFinding).filter_by(package_id=pkg.id).all()
    sec_findings = db.query(SecurityFinding).filter_by(package_id=pkg.id).all()
    security_status = snapshot_metadata.get("security_status", "not_checked")
    security_counts_available = security_status in ("checked", "partial") or bool(sec_findings)
    adoptions = db.query(AdoptionEvidence).filter_by(package_id=pkg.id).order_by(desc(AdoptionEvidence.stars)).all()
    ai_item = db.query(AIAnalysis).filter_by(package_id=pkg.id).order_by(desc(AIAnalysis.generated_at)).first()

    data_payload = {
        "package": {
            "name": pkg.name,
            "ecosystem": pkg.ecosystem,
            "description": pkg.description,
            "homepage": pkg.homepage,
            "repository_url": pkg.repository_url,
            "license": pkg.license,
            "latest_version": pkg.latest_version,
        },
        "score": {
            "overall_score": score.overall_score if score else None,
            "confidence_level": score.confidence_level if score else "low",
            "version": score.version if score else "v1.0.0",
            "explanation": score.explanation if score else "No score calculated",
            "breakdown": json.loads(score.breakdown) if (score and score.breakdown) else {},
        },
        "repository": {
            "full_name": repo.full_name if repo else "N/A",
            "url": repo.url if repo else "#",
            "stars": repo.stars if repo else None,
            "forks": repo.forks if repo else None,
            "open_issues": repo.open_issues if repo else None,
            "watchers": repo.watchers if repo else None,
            "is_archived": repo.is_archived if repo else False,
            "is_fork": repo.is_fork if repo else False,
        },
        "downloads": {
            "monthly": snap.downloads_count if snap else None,
            "weekly": snapshot_metadata.get("weekly"),
            "daily": snapshot_metadata.get("daily"),
            "growth_rate_pct": snap.growth_rate if snap else None,
            "mirror_inclusive": snapshot_metadata.get("mirror_inclusive"),
        },
        "adoption": {
            "status": snapshot_metadata.get("adoption_status", "not_checked"),
            "caveats": snapshot_metadata.get("adoption_caveats", []),
            "confirmed_dependencies_count": sum(1 for a in adoptions if "dependency" in a.evidence_type.lower()),
            "confirmed_source_usage_count": sum(1 for a in adoptions if "source-code" in a.evidence_type.lower()),
            "possible_usage_count": sum(1 for a in adoptions if "possible" in a.evidence_type.lower()),
            "mention_only_count": sum(1 for a in adoptions if "mention" in a.evidence_type.lower()),
            "total_findings": len(adoptions),
            "findings": [
                {
                    "source_repo_full_name": a.source_repo_full_name,
                    "source_repo_url": a.source_repo_url,
                    "file_path": a.file_path,
                    "evidence_type": a.evidence_type,
                    "stars": a.stars,
                    "confidence_score": a.confidence_score,
                }
                for a in adoptions[:20]
            ],
        },
        "security": {
            "status": security_status,
            "checked_at": snapshot_metadata.get("security_checked_at"),
            "caveats": snapshot_metadata.get("security_caveats", []),
            "vulnerabilities_count": (
                len(sec_findings)
                if snapshot_metadata.get("security_status") in ("checked", "partial") or sec_findings
                else None
            ),
            "critical_count": sum(1 for s in sec_findings if s.severity == "CRITICAL") if security_counts_available else None,
            "high_count": sum(1 for s in sec_findings if s.severity == "HIGH") if security_counts_available else None,
            "medium_count": sum(1 for s in sec_findings if s.severity == "MEDIUM") if security_counts_available else None,
            "low_count": sum(1 for s in sec_findings if s.severity == "LOW") if security_counts_available else None,
            "vulnerabilities": [
                {
                    "identifier": s.identifier,
                    "severity": s.severity,
                    "affected_versions": s.affected_range,
                    "remediation": s.remediation,
                    "reference_url": s.reference_url,
                    "title": s.title,
                }
                for s in sec_findings
            ],
        },
        "health": {
            "overall_health_rating": normalize_health_rating(findings=health_findings),
            "findings": [
                {
                    "category": h.category,
                    "check_name": h.check_name,
                    "status": h.status,
                    "message": h.message,
                }
                for h in health_findings
            ],
        },
        "ai": {
            "model": ai_item.model if ai_item else "N/A",
            "summary": ai_item.summary if ai_item else None,
            "risks": ai_item.risks if ai_item else None,
            "opportunities": ai_item.opportunities if ai_item else None,
            "maintainer_recommendations": ai_item.maintainer_recommendations if ai_item else None,
            "generated_at": ai_item.generated_at.isoformat() if ai_item else None,
        } if ai_item else None,
    }

    content = ReportGenerator.generate(data_payload, format_type=req.format)
    rep_id = str(uuid.uuid4())
    rep = Report(
        id=rep_id,
        package_id=pkg.id,
        format=req.format.lower(),
        content=content,
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return rep


@app.get("/api/v1/reports/{report_id}", tags=["Reports"])
def get_report(report_id: str, db: Session = Depends(get_db)):
    rep = db.query(Report).filter_by(id=report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
    if rep.format == "html":
        return HTMLResponse(content=rep.content)
    elif rep.format == "json":
        return JSONResponse(content=json.loads(rep.content))
    return PlainTextResponse(content=rep.content)


# --- Demo Mode ---
@app.post("/api/v1/demo/seed", tags=["Demo Mode"])
def seed_demo(
    _auth: None = Depends(require_api_key),
    _rate_limit: None = Depends(rate_limit_expensive_requests),
):
    if settings.environment.lower() == "production" and not settings.enable_demo_mode:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")
    ids = seed_demo_data()
    return {"message": "Demo data seeded successfully", "package_ids": ids}


# Serve the framework-free dashboard bundled with the API package.
_dashboard_dir = Path(__file__).resolve().parent / "dashboard_static"
app.mount(
    "/dashboard-assets",
    StaticFiles(directory=str(_dashboard_dir)),
    name="dashboard-assets",
)


@app.get("/", include_in_schema=False)
def dashboard_index():
    return FileResponse(_dashboard_dir / "index.html")

