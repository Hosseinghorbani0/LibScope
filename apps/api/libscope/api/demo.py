"""
Isolated Sample Demo Data for LibScope.
Enables immediate interactive evaluation of the platform and dashboard without requiring live network access.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List
from libscope.core.database import db_session
from libscope.core.logging import get_logger
from libscope.core.models import (
    AdoptionEvidence,
    AIAnalysis,
    HealthFinding,
    MetricSnapshot,
    Package,
    Repository,
    Score,
    SecurityFinding,
)

logger = get_logger("api.demo")

DEMO_PACKAGES = [
    {
        "name": "fastapi",
        "ecosystem": "pypi",
        "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
        "homepage": "https://fastapi.tiangolo.com",
        "repository_url": "https://github.com/fastapi/fastapi",
        "license": "MIT",
        "latest_version": "0.115.0",
        "stars": 78500,
        "forks": 6500,
        "open_issues": 120,
        "monthly_downloads": 48200000,
        "overall_score": 94.5,
        "confidence": "high",
        "adoptions": [
            {"repo": "huggingface/transformers", "file": "pyproject.toml", "stars": 135000, "type": "Confirmed dependency declaration"},
            {"repo": "tiangolo/full-stack-fastapi-template", "file": "backend/requirements.txt", "stars": 24000, "type": "Confirmed dependency declaration"},
            {"repo": "langchain-ai/langchain", "file": "libs/community/pyproject.toml", "stars": 98000, "type": "Confirmed dependency declaration"},
        ],
        "vulnerabilities": [],
    },
    {
        "name": "requests",
        "ecosystem": "pypi",
        "description": "A simple, yet elegant, HTTP library for Python.",
        "homepage": "https://requests.readthedocs.io",
        "repository_url": "https://github.com/psf/requests",
        "license": "Apache-2.0",
        "latest_version": "2.32.3",
        "stars": 52000,
        "forks": 9400,
        "open_issues": 180,
        "monthly_downloads": 312000000,
        "overall_score": 92.0,
        "confidence": "high",
        "adoptions": [
            {"repo": "docker/docker-py", "file": "requirements.txt", "stars": 6800, "type": "Confirmed dependency declaration"},
            {"repo": "ansible/ansible", "file": "requirements.txt", "stars": 62000, "type": "Confirmed dependency declaration"},
            {"repo": "boto/botocore", "file": "setup.py", "stars": 1600, "type": "Confirmed dependency declaration"},
        ],
        "vulnerabilities": [],
    },
    {
        "name": "askai-python",
        "ecosystem": "pypi",
        "description": "Universal Multi-Provider AI Agent & LLM Orchestration SDK for Python",
        "homepage": "https://github.com/askai/askai-python",
        "repository_url": "https://github.com/askai/askai-python",
        "license": "Apache-2.0",
        "latest_version": "0.6.0",
        "stars": 850,
        "forks": 75,
        "open_issues": 8,
        "monthly_downloads": 18500,
        "overall_score": 86.5,
        "confidence": "high",
        "adoptions": [
            {"repo": "agentic-labs/workflow-engine", "file": "requirements.txt", "stars": 1200, "type": "Confirmed dependency declaration"},
            {"repo": "deepdev/ai-evaluator", "file": "pyproject.toml", "stars": 450, "type": "Confirmed dependency declaration"},
        ],
        "vulnerabilities": [],
    },
]


def seed_demo_data() -> List[int]:
    """Seed pre-packaged demonstration data for offline testing and presentations."""
    now = datetime.now(timezone.utc)
    created_ids = []

    with db_session() as session:
        for p in DEMO_PACKAGES:
            existing = session.query(Package).filter_by(name=p["name"], ecosystem=p["ecosystem"]).first()
            if existing:
                created_ids.append(existing.id)
                continue

            pkg = Package(
                name=p["name"],
                ecosystem=p["ecosystem"],
                description=p["description"],
                homepage=p["homepage"],
                repository_url=p["repository_url"],
                license=p["license"],
                latest_version=p["latest_version"],
                created_at=now,
                updated_at=now,
            )
            session.add(pkg)
            session.flush()
            created_ids.append(pkg.id)

            # Repository
            owner, repo_name = p["repository_url"].replace("https://github.com/", "").split("/")
            repo = Repository(
                package_id=pkg.id,
                owner=owner,
                repo_name=repo_name,
                full_name=f"{owner}/{repo_name}",
                url=p["repository_url"],
                stars=p["stars"],
                forks=p["forks"],
                open_issues=p["open_issues"],
                watchers=int(p["stars"] * 0.05),
                default_branch="main",
                is_archived=False,
                license=p["license"],
                last_commit_at=now,
                last_release_at=now,
            )
            session.add(repo)

            # Metric snapshot
            snap = MetricSnapshot(
                package_id=pkg.id,
                recorded_at=now,
                period="monthly",
                downloads_count=p["monthly_downloads"],
                growth_rate=14.5,
                stars_count=p["stars"],
                forks_count=p["forks"],
                issues_count=p["open_issues"],
            )
            session.add(snap)

            # Adoption evidence
            for adopt in p["adoptions"]:
                session.add(
                    AdoptionEvidence(
                        package_id=pkg.id,
                        source_repo_url=f"https://github.com/{adopt['repo']}",
                        source_repo_full_name=adopt["repo"],
                        file_path=adopt["file"],
                        evidence_type=adopt["type"],
                        raw_match=f'"{p["name"]}>=0.1.0"',
                        stars=adopt["stars"],
                        confidence_score=0.95,
                        discovered_at=now,
                    )
                )

            # Health findings
            session.add(
                HealthFinding(
                    package_id=pkg.id,
                    category="license",
                    check_name="osi_license_detected",
                    status="pass",
                    message=f"Standard OSI license {p['license']} declared.",
                    detected_at=now,
                )
            )
            session.add(
                HealthFinding(
                    package_id=pkg.id,
                    category="documentation",
                    check_name="readme_present",
                    status="pass",
                    message="Comprehensive README present.",
                    detected_at=now,
                )
            )
            session.add(
                HealthFinding(
                    package_id=pkg.id,
                    category="security_policy",
                    check_name="security_policy_present",
                    status="pass",
                    message="SECURITY.md policy published.",
                    detected_at=now,
                )
            )

            # Score
            session.add(
                Score(
                    package_id=pkg.id,
                    version="v1.0.0",
                    calculated_at=now,
                    overall_score=p["overall_score"],
                    confidence_level=p["confidence"],
                    popularity_score=95.0 if p["monthly_downloads"] > 1000000 else 75.0,
                    growth_score=80.0,
                    adoption_score=92.0,
                    maintenance_score=94.0,
                    documentation_score=95.0,
                    quality_score=90.0,
                    security_score=95.0,
                    explanation=f"Demonstration benchmark profile for {p['name']} with verified adoption and zero reported vulnerabilities.",
                )
            )

            # AI Analysis sample
            session.add(
                AIAnalysis(
                    package_id=pkg.id,
                    provider="libscope-demo",
                    model="sample-intelligence-model",
                    summary=f"{p['name']} demonstrates mature open-source ecosystem characteristics with verified real-world adoption across mission-critical codebases.",
                    risks="• High dependency tree depth in downstream projects requires active patch monitoring.\n• High issue velocity requires structured triage automation.",
                    opportunities="• Expand enterprise compliance badges.\n• Provide automated migration codemods between minor versions.",
                    maintainer_recommendations="• Continue strict semantic versioning cadence.\n• Document performance benchmarks against alternative architectures.",
                    competitive_position="Industry standard in its respective category.",
                    raw_response="Demo mode generated intelligence analysis.",
                    generated_at=now,
                )
            )

    logger.info(f"Seeded {len(created_ids)} demo packages successfully.")
    return created_ids

