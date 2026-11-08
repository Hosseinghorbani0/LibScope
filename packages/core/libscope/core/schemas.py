"""
Pydantic v2 schemas for request validation, responses, and serializations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Package Schemas ---
class PackageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Package name")
    ecosystem: str = Field(default="pypi", description="Ecosystem (e.g. pypi, github)")


class PackageRead(BaseSchema):
    id: int
    name: str
    ecosystem: str
    description: Optional[str] = None
    homepage: Optional[str] = None
    repository_url: Optional[str] = None
    license: Optional[str] = None
    latest_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RepositoryRead(BaseSchema):
    id: int
    package_id: int
    owner: str
    repo_name: str
    full_name: str
    url: str
    stars: int
    forks: int
    open_issues: int
    closed_issues: int
    watchers: int
    default_branch: str
    is_archived: bool
    is_fork: bool
    license: Optional[str] = None
    last_commit_at: Optional[datetime] = None
    last_release_at: Optional[datetime] = None


class ReleaseRead(BaseSchema):
    id: int
    package_id: int
    version: str
    release_date: Optional[datetime] = None
    is_yanked: bool
    download_url: Optional[str] = None


class MetricSnapshotRead(BaseSchema):
    id: int
    package_id: int
    recorded_at: datetime
    period: str
    downloads_count: int
    growth_rate: Optional[float] = None
    stars_count: Optional[int] = None
    forks_count: Optional[int] = None
    issues_count: Optional[int] = None
    raw_data: Optional[str] = None


class AdoptionEvidenceRead(BaseSchema):
    id: int
    package_id: int
    source_repo_url: str
    source_repo_full_name: str
    file_path: str
    evidence_type: str
    raw_match: Optional[str] = None
    discovered_at: datetime
    stars: int
    confidence_score: float


class HealthFindingRead(BaseSchema):
    id: int
    package_id: int
    category: str
    check_name: str
    status: str
    message: str
    details: Optional[str] = None
    detected_at: datetime


class SecurityFindingRead(BaseSchema):
    id: int
    package_id: int
    identifier: str
    severity: str
    affected_range: Optional[str] = None
    fixed_in: Optional[str] = None
    source: str
    reference_url: Optional[str] = None
    title: Optional[str] = None
    details: Optional[str] = None
    remediation: Optional[str] = None
    detected_at: datetime


class ScoreRead(BaseSchema):
    id: int
    package_id: int
    version: str
    calculated_at: datetime
    overall_score: Optional[float] = None
    confidence_level: str
    popularity_score: Optional[float] = None
    growth_score: Optional[float] = None
    adoption_score: Optional[float] = None
    maintenance_score: Optional[float] = None
    documentation_score: Optional[float] = None
    quality_score: Optional[float] = None
    security_score: Optional[float] = None
    breakdown: Optional[str] = None
    explanation: Optional[str] = None


class AIAnalysisRead(BaseSchema):
    id: int
    package_id: int
    provider: str
    model: str
    summary: Optional[str] = None
    risks: Optional[str] = None
    opportunities: Optional[str] = None
    maintainer_recommendations: Optional[str] = None
    competitive_position: Optional[str] = None
    generated_at: datetime


class PackageDetailRead(PackageRead):
    repository: Optional[RepositoryRead] = None
    latest_score: Optional[ScoreRead] = None
    latest_ai_analysis: Optional[AIAnalysisRead] = None
    recent_releases_count: int = 0
    total_downloads_30d: int = 0
    adoption_count: int = 0
    vulnerabilities_count: int = 0


# --- Job Schemas ---
class AnalysisJobCreate(BaseModel):
    package_name: str = Field(..., min_length=1, description="Name of the package or owner/repo to analyze")
    ecosystem: str = Field(default="pypi", description="Ecosystem (pypi or github)")
    enable_ai: bool = Field(default=False, description="Whether to run optional AI analysis")


class AnalysisJobRead(BaseSchema):
    id: str
    package_id: Optional[int] = None
    package_name: str
    ecosystem: str
    status: str
    progress: int
    step_message: str
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# --- Report Schemas ---
class ReportGenerateRequest(BaseModel):
    package_id: int
    format: str = Field(default="markdown", description="Format: markdown, json, or html")


class ReportRead(BaseSchema):
    id: str
    package_id: int
    format: str
    content: str
    generated_at: datetime


# --- Competitor Comparison Schemas ---
class CompareRequest(BaseModel):
    package_ids: Optional[List[int]] = None
    package_names: Optional[List[str]] = None
    ecosystem: str = Field(default="pypi")


class CompetitorMetricComparison(BaseModel):
    package_name: str
    ecosystem: str
    overall_score: Optional[float] = None
    confidence: str
    monthly_downloads: int
    stars: int
    forks: int
    open_issues: int
    latest_version: Optional[str] = None
    last_release_age_days: Optional[int] = None
    verified_adoptions: int
    vulnerabilities_count: int
    license: Optional[str] = None
    comparability_notes: List[str]


class CompareResponse(BaseModel):
    compared_at: datetime
    packages: List[CompetitorMetricComparison]
    summary: str

