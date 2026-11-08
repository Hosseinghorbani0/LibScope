"""
Prompts module for LibScope AI tasks.
"""
from libscope.ai.prompts.system import BASE_SYSTEM_PROMPT
from libscope.ai.prompts.package_prompts import PACKAGE_ANALYSIS_PROMPT
from libscope.ai.prompts.competitor_prompts import COMPETITOR_COMPARISON_PROMPT
from libscope.ai.prompts.adoption_prompts import ADOPTION_ANALYSIS_PROMPT
from libscope.ai.prompts.health_prompts import HEALTH_ANALYSIS_PROMPT
from libscope.ai.prompts.security_prompts import SECURITY_ANALYSIS_PROMPT
from libscope.ai.prompts.recommendations_prompts import RECOMMENDATIONS_PROMPT

__all__ = [
    "BASE_SYSTEM_PROMPT",
    "PACKAGE_ANALYSIS_PROMPT",
    "COMPETITOR_COMPARISON_PROMPT",
    "ADOPTION_ANALYSIS_PROMPT",
    "HEALTH_ANALYSIS_PROMPT",
    "SECURITY_ANALYSIS_PROMPT",
    "RECOMMENDATIONS_PROMPT",
]
