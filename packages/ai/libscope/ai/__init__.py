"""
LibScope AI Analyst Package powered by askai-python.
"""
from libscope.ai.client import AIClient, AskAIClient
from libscope.ai.interpreter import AIAnalysisResult, AIInterpreter
from libscope.ai.security import sanitize_untrusted_text
from libscope.ai.services import (
    AdoptionAnalysisService,
    CompetitorAnalysisService,
    HealthAnalysisService,
    MaintainerRecommendationsService,
    PackageAnalysisService,
    RepositoryAnalysisService,
    SecurityAnalysisService,
)

__all__ = [
    "AskAIClient",
    "AIClient",
    "AIInterpreter",
    "AIAnalysisResult",
    "sanitize_untrusted_text",
    "PackageAnalysisService",
    "RepositoryAnalysisService",
    "AdoptionAnalysisService",
    "HealthAnalysisService",
    "SecurityAnalysisService",
    "CompetitorAnalysisService",
    "MaintainerRecommendationsService",
]
