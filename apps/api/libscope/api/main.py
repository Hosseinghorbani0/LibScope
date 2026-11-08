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
from libscope.api.demo import seed_demo_data
from libscope.api.orchestrator import run_package_analysis
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
    HealthFindingRead,
    MetricSnapshotRead,
    PackageDetailRead,
    PackageRead,
    ReleaseRead,
    ReportGenerateRequest,
    ReportRead,
    ScoreRead,
    SecurityFindingRead,
)
from libscope.providers.registry import get_provider_registry
from libscope.reporting.generator import ReportGenerator
from sqlalchemy import desc
from sqlalchemy.orm import Session

settings = get_settings()
setup_logging(level=settings.log_level)
logger = get_logger("api.main")


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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    monthly_dl = latest_snap.downloads_count if latest_snap else 0

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
def get_package_analytics(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(MetricSnapshot).filter_by(package_id=package_id).order_by(MetricSnapshot.recorded_at).all()


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


@app.get("/api/v1/packages/{package_id}/security", response_model=list[SecurityFindingRead], tags=["Security"])
def get_package_security(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(SecurityFinding).filter_by(package_id=package_id).all()


@app.get("/api/v1/packages/{package_id}/releases", response_model=list[ReleaseRead], tags=["Releases"])
def get_package_releases(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(Release).filter_by(package_id=package_id).order_by(desc(Release.release_date)).all()


@app.get("/api/v1/packages/{package_id}/score", response_model=ScoreRead | None, tags=["Scoring"])
def get_package_score(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(Score).filter_by(package_id=package_id).order_by(desc(Score.calculated_at)).first()


@app.get("/api/v1/packages/{package_id}/ai", response_model=AIAnalysisRead | None, tags=["AI"])
def get_package_ai_analysis(package_id: int, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return db.query(AIAnalysis).filter_by(package_id=package_id).order_by(desc(AIAnalysis.generated_at)).first()


# --- Competitor Comparison ---
@app.post("/api/v1/compare", response_model=CompareResponse, tags=["Comparison"])
def compare_packages(req: CompareRequest, db: Session = Depends(get_db)):
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

        pkg_data_list.append({
            "name": p.name,
            "ecosystem": p.ecosystem,
            "overall_score": latest_score.overall_score if latest_score else None,
            "confidence": latest_score.confidence_level if latest_score else "low",
            "monthly_downloads": latest_snap.downloads_count if latest_snap else 0,
            "weekly_downloads": 0,
            "stars": repo.stars if repo else 0,
            "forks": repo.forks if repo else 0,
            "open_issues": repo.open_issues if repo else 0,
            "latest_version": p.latest_version,
            "days_since_last_release": None,
            "days_since_last_commit": None,
            "confirmed_adoptions_count": adoptions,
            "vulnerabilities_count": vulns,
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
def generate_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    pkg = db.query(Package).filter_by(id=req.package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    score = db.query(Score).filter_by(package_id=pkg.id).order_by(desc(Score.calculated_at)).first()
    repo = pkg.repository
    snap = db.query(MetricSnapshot).filter_by(package_id=pkg.id).order_by(desc(MetricSnapshot.recorded_at)).first()
    health_findings = db.query(HealthFinding).filter_by(package_id=pkg.id).all()
    sec_findings = db.query(SecurityFinding).filter_by(package_id=pkg.id).all()
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
            "stars": repo.stars if repo else 0,
            "forks": repo.forks if repo else 0,
            "open_issues": repo.open_issues if repo else 0,
            "watchers": repo.watchers if repo else 0,
            "is_archived": repo.is_archived if repo else False,
            "is_fork": repo.is_fork if repo else False,
        },
        "downloads": {
            "monthly": snap.downloads_count if snap else 0,
            "weekly": 0,
            "daily": 0,
            "growth_rate_pct": snap.growth_rate if snap else None,
            "mirror_inclusive": True,
        },
        "adoption": {
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
            "vulnerabilities_count": len(sec_findings),
            "critical_count": sum(1 for s in sec_findings if s.severity == "CRITICAL"),
            "high_count": sum(1 for s in sec_findings if s.severity == "HIGH"),
            "medium_count": sum(1 for s in sec_findings if s.severity == "MEDIUM"),
            "low_count": sum(1 for s in sec_findings if s.severity == "LOW"),
            "vulnerabilities": [
                {
                    "identifier": s.identifier,
                    "severity": s.severity,
                    "affected_versions": s.affected_range,
                    "remediation": s.remediation,
                    "reference_url": s.reference_url,
                }
                for s in sec_findings
            ],
        },
        "health": {
            "overall_health_rating": "healthy",
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
def seed_demo():
    ids = seed_demo_data()
    return {"message": "Demo data seeded successfully", "package_ids": ids}


# Serve React Frontend Build if present
_dist_dir = Path(__file__).resolve().parent.parent.parent / "dashboard" / "dist"
if _dist_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = _dist_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_dist_dir / "index.html")

