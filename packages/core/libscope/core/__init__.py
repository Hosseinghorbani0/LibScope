"""
LibScope Core Package.
"""
from libscope.core.config import Settings, get_settings
from libscope.core.database import db_session, get_db, get_engine, init_db
from libscope.core.logging import get_logger, setup_logging
from libscope.core.models import (
    AdoptionEvidence,
    AIAnalysis,
    AnalysisJob,
    Base,
    CollectionRun,
    HealthFinding,
    MetricSnapshot,
    Package,
    Release,
    Repository,
    Score,
    SecurityFinding,
)
from libscope.core.security import create_safe_httpx_client, validate_safe_url

__all__ = [
    "Settings",
    "get_settings",
    "get_engine",
    "init_db",
    "db_session",
    "get_db",
    "get_logger",
    "setup_logging",
    "validate_safe_url",
    "create_safe_httpx_client",
    "Base",
    "Package",
    "Repository",
    "Release",
    "MetricSnapshot",
    "AdoptionEvidence",
    "HealthFinding",
    "SecurityFinding",
    "Score",
    "AnalysisJob",
    "AIAnalysis",
    "CollectionRun",
]

