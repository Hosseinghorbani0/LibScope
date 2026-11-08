"""
Prompt templates for vulnerability and security posture analysis.
"""

SECURITY_ANALYSIS_PROMPT = """Analyze the security posture for package '{name}':

SECURITY ADVISORIES & POSTURE:
- Total OSV Advisories: {vulnerabilities_count}
- Critical/High Severity: {critical_high_count}
- Published Security Policy (SECURITY.md): {has_security_policy}
- Advisories Detail:
{advisories_summary}

Synthesize an objective security assessment adhering strictly to the requested schema.
"""

