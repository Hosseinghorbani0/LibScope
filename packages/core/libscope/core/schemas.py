"""
Pydantic v2 schemas for request validation, responses, and serializations.
"""
from datetime import datetime

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
    description: str | None = None
    homepage: str | None = None
    repository_url: str | None = None
    license: str | None = None
    latest_version: str | None = None
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
    license: str | None = None
    last_commit_at: datetime | None = None
    last_release_at: datetime | None = None


class ReleaseRead(BaseSchema):
    id: int
    package_id: int
    version: str
    release_date: datetime | None = None
    is_yanked: bool
    download_url: str | None = None


class MetricSnapshotRead(BaseSchema):
    id: int
    package_id: int
    recorded_at: datetime
    period: str
    downloads_count: int
    growth_rate: float | None = None
    stars_count: int | None = None
    forks_count: int | None = None
    issues_count: int | None = None
    raw_data: str | None = None


class AdoptionEvidenceRead(BaseSchema):
    id: int
    package_id: int
    source_repo_url: str
    source_repo_full_name: str
    file_path: str
    evidence_type: str
    raw_match: str | None = None
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
    details: str | None = None
    detected_at: datetime


class SecurityFindingRead(BaseSchema):
    id: int
    package_id: int
    identifier: str
    severity: str
    affected_range: str | None = None
    fixed_in: str | None = None
    source: str
    reference_url: str | None = None
    title: str | None = None
    details: str | None = None
    remediation: str | None = None
    detected_at: datetime


class ScoreRead(BaseSchema):
    id: int
    package_id: int
    version: str
    calculated_at: datetime
    overall_score: float | None = None
    confidence_level: str
    popularity_score: float | None = None
    growth_score: float | None = None
    adoption_score: float | None = None
    maintenance_score: float | None = None
    documentation_score: float | None = None
    quality_score: float | None = None
    security_score: float | None = None
    breakdown: str | None = None
    explanation: str | None = None


class AIAnalysisRead(BaseSchema):
    id: int
    package_id: int
    provider: str
    model: str
    summary: str | None = None
    risks: str | None = None
    opportunities: str | None = None
    maintainer_recommendations: str | None = None
    competitive_position: str | None = None
    generated_at: datetime


class PackageDetailRead(PackageRead):
    repository: RepositoryRead | None = None
    latest_score: ScoreRead | None = None
    latest_ai_analysis: AIAnalysisRead | None = None
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
    package_id: int | None = None
    package_name: str
    ecosystem: str
    status: str
    progress: int
    step_message: str
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


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
    package_ids: list[int] | None = None
    package_names: list[str] | None = None
    ecosystem: str = Field(default="pypi")


class CompetitorMetricComparison(BaseModel):
    package_name: str
    ecosystem: str
    overall_score: float | None = None
    confidence: str
    monthly_downloads: int
    stars: int
    forks: int
    open_issues: int
    latest_version: str | None = None
    last_release_age_days: int | None = None
    verified_adoptions: int
    vulnerabilities_count: int
    license: str | None = None
    comparability_notes: list[str]


class CompareResponse(BaseModel):
    compared_at: datetime
    packages: list[CompetitorMetricComparison]
    summary: str

