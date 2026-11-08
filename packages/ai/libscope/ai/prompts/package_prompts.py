"""
Prompt templates for full package intelligence synthesis.
"""

PACKAGE_ANALYSIS_PROMPT = """Review the following verified telemetry and evidence collected by LibScope for package '{name}':

PACKAGE METRICS & IDENTITY:
- Ecosystem: {ecosystem}
- Latest Version: {latest_version}
- License: {license}
- Repository: {repo_url}
- Monthly Downloads: {monthly_downloads:,} ({mirror_note})
- Recent Growth Trend: {growth_trend}
- GitHub Stars: {stars:,} | Forks: {forks:,} | Open Issues: {open_issues:,}
- Commit Freshness: Last commit {days_since_commit} days ago, last release {days_since_release} days ago
- Verified Independent Adoptions: {verified_adoptions} confirmed declarations in public project manifests
- Known OSV Vulnerabilities: {vulnerabilities_count} ({critical_high_count} Critical/High)
- Deterministic Quality Score: {overall_score}/100 (Confidence: {confidence_level})

UNTRUSTED METADATA / README CONTENT:
{sanitized_description}

Provide an objective assessment adhering strictly to the requested schema.
"""

