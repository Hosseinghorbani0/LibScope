"""
Relational Database Models for LibScope using SQLAlchemy 2.x declarative style.
Compatible with SQLite and PostgreSQL.
"""
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ecosystem: Mapped[str] = mapped_column(String(50), nullable=False, default="pypi", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    homepage: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latest_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    repository: Mapped[Optional["Repository"]] = relationship("Repository", back_populates="package", uselist=False, cascade="all, delete-orphan")
    releases: Mapped[list["Release"]] = relationship("Release", back_populates="package", cascade="all, delete-orphan")
    snapshots: Mapped[list["MetricSnapshot"]] = relationship("MetricSnapshot", back_populates="package", cascade="all, delete-orphan")
    adoption_evidence: Mapped[list["AdoptionEvidence"]] = relationship("AdoptionEvidence", back_populates="package", cascade="all, delete-orphan")
    health_findings: Mapped[list["HealthFinding"]] = relationship("HealthFinding", back_populates="package", cascade="all, delete-orphan")
    security_findings: Mapped[list["SecurityFinding"]] = relationship("SecurityFinding", back_populates="package", cascade="all, delete-orphan")
    scores: Mapped[list["Score"]] = relationship("Score", back_populates="package", cascade="all, delete-orphan")
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship("AIAnalysis", back_populates="package", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="package", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_packages_name_ecosystem", "name", "ecosystem", unique=True),
    )


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, unique=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    closed_issues: Mapped[int] = mapped_column(Integer, default=0)
    watchers: Mapped[int] = mapped_column(Integer, default=0)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    package: Mapped["Package"] = relationship("Package", back_populates="repository")


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_yanked: Mapped[bool] = mapped_column(Boolean, default=False)
    download_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)

    package: Mapped["Package"] = relationship("Package", back_populates="releases")

    __table_args__ = (
        Index("ix_releases_pkg_ver", "package_id", "version", unique=True),
    )


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    period: Mapped[str] = mapped_column(String(50), default="daily")  # daily, weekly, monthly, cumulative
    downloads_count: Mapped[int] = mapped_column(Integer, default=0)
    growth_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    stars_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forks_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issues_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded raw observation

    package: Mapped["Package"] = relationship("Package", back_populates="snapshots")


class AdoptionEvidence(Base):
    __tablename__ = "adoption_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    source_repo_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_repo_full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    # Evidence classifications:
    # 1. Confirmed dependency declaration
    # 2. Confirmed source-code usage
    # 3. Possible usage
    # 4. Mention only
    # 5. Unverified
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_match: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)

    package: Mapped["Package"] = relationship("Package", back_populates="adoption_evidence")

    __table_args__ = (
        Index("ix_adoption_pkg_repo_file", "package_id", "source_repo_full_name", "file_path", unique=True),
    )


class HealthFinding(Base):
    __tablename__ = "health_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    # Categories: documentation, testing, ci, release_discipline, maintenance, license, security_policy
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Status: pass, warning, fail, missing
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded extra detail
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    package: Mapped["Package"] = relationship("Package", back_populates="health_findings")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # CVE or GHSA or OSV ID
    # Severity: CRITICAL, HIGH, MEDIUM, LOW
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="MEDIUM")
    affected_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fixed_in: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="OSV")
    reference_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    package: Mapped["Package"] = relationship("Package", back_populates="security_findings")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="v1.0.0")
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0 to 100, None if insufficient
    # Confidence: high, medium, low
    confidence_level: Mapped[str] = mapped_column(String(50), default="medium")
    popularity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    adoption_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    maintenance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    documentation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    package: Mapped["Package"] = relationship("Package", back_populates="scores")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    package_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("packages.id", ondelete="SET NULL"), nullable=True)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ecosystem: Mapped[str] = mapped_column(String(50), default="pypi")
    # Status: queued, running, completed, failed, cancelled
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    step_message: Mapped[str] = mapped_column(String(255), default="Job queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # markdown, json, html
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    package: Mapped["Package"] = relationship("Package", back_populates="reports")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), default="openrouter")
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)
    maintainer_recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitive_position: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    package: Mapped["Package"] = relationship("Package", back_populates="ai_analyses")


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success")
    items_collected: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

