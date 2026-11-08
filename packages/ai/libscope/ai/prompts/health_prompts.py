"""
Prompt templates for repository and project health analysis.
"""

HEALTH_ANALYSIS_PROMPT = """Analyze the engineering hygiene and community health for repository '{repo_name}':

HEALTH SIGNALS & HYGIENE:
- Stars: {stars:,} | Forks: {forks:,} | Watchers: {watchers:,}
- Open Issues: {open_issues:,}
- Days Since Last Commit: {days_since_commit}
- Days Since Last Release: {days_since_release}
- Has README: {has_readme}
- Has License: {license}
- Has CONTRIBUTING guide: {has_contributing}
- Has SECURITY policy: {has_security_md}
- Has CI Workflows: {has_ci}
- Is Archived: {is_archived}

Synthesize a project health evaluation adhering strictly to the requested schema.
"""

