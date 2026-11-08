"""
AI analysis services powered by askai-python.
"""
from libscope.ai.services.adoption_service import AdoptionAnalysisService
from libscope.ai.services.competitor_service import CompetitorAnalysisService
from libscope.ai.services.health_service import HealthAnalysisService
from libscope.ai.services.package_service import PackageAnalysisService
from libscope.ai.services.recommendations_service import MaintainerRecommendationsService
from libscope.ai.services.repository_service import RepositoryAnalysisService
from libscope.ai.services.security_service import SecurityAnalysisService

__all__ = [
    "PackageAnalysisService",
    "RepositoryAnalysisService",
    "AdoptionAnalysisService",
    "HealthAnalysisService",
    "SecurityAnalysisService",
    "CompetitorAnalysisService",
    "MaintainerRecommendationsService",
]

