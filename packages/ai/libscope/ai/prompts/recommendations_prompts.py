"""
Prompt templates for maintainer recommendations.
"""

RECOMMENDATIONS_PROMPT = """Based on the following LibScope diagnostics for package '{name}', suggest actionable maintainer improvements:

DIAGNOSTIC SUMMARY:
- Overall Quality Score: {score}/100 ({confidence} confidence)
- Health Sub-score: {health_score}/100
- Maintenance Sub-score: {maintenance_score}/100
- Security Sub-score: {security_score}/100
- Adoption Sub-score: {adoption_score}/100
- Community Hygiene Gaps: {hygiene_gaps}
- Days Since Last Commit: {days_since_commit}
- Days Since Last Release: {days_since_release}
- Open Security Advisories: {vulnerabilities_count}

Provide prioritized, constructive recommendations for the package maintainers adhering strictly to the requested schema.
"""

