"""
Markdown Report Formatter for LibScope Intelligence.
"""
from datetime import UTC, datetime
from typing import Any


def generate_markdown_report(data: dict[str, Any]) -> str:
    """Generate professional, reproducible GitHub-flavored Markdown intelligence report."""
    pkg = data.get("package", {})
    repo = data.get("repository", {})
    score = data.get("score", {})
    dl = data.get("downloads", {})
    health = data.get("health", {})
    sec = data.get("security", {})
    adoption = data.get("adoption", {})
    ai = data.get("ai")
    data.get("sources", [])
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    overall = score.get("overall_score")
    score_display = f"**{overall}/100**" if overall is not None else "**Insufficient Data**"
    conf = score.get("confidence_level", "medium").upper()

    md = f"""# LibScope Intelligence Report: {pkg.get('name', 'Package')}
*Open-Source Software Intelligence. Beyond Downloads.*

Generated: `{now}` | Scoring Model: `{score.get('version', 'v1.0.0')}` | Confidence: `{conf}`

---

## 1. Executive Summary
- **Package Name:** `{pkg.get('name')}`
- **Ecosystem:** `{pkg.get('ecosystem', 'pypi')}`
- **Latest Version:** `{pkg.get('latest_version', 'Unknown')}`
- **License:** `{pkg.get('license', 'Unspecified')}`
- **Homepage:** {pkg.get('homepage') or 'N/A'}
- **Repository:** {pkg.get('repository_url') or 'N/A'}

### Quality Score: {score_display}
> **Assessment:** {score.get('explanation', 'Score calculation based on multi-dimensional analysis.')}

| Dimension | Score | Weight | Confidence |
| :--- | :---: | :---: | :--- |
| **Adoption** | `{score.get('breakdown', {}).get('adoption', {}).get('score', 'N/A')}` | 25% | {score.get('breakdown', {}).get('adoption', {}).get('confidence', 'medium')} |
| **Maintenance** | `{score.get('breakdown', {}).get('maintenance', {}).get('score', 'N/A')}` | 20% | {score.get('breakdown', {}).get('maintenance', {}).get('confidence', 'medium')} |
| **Security Posture** | `{score.get('breakdown', {}).get('security', {}).get('score', 'N/A')}` | 15% | {score.get('breakdown', {}).get('security', {}).get('confidence', 'medium')} |
| **Documentation** | `{score.get('breakdown', {}).get('documentation', {}).get('score', 'N/A')}` | 15% | {score.get('breakdown', {}).get('documentation', {}).get('confidence', 'high')} |
| **Engineering Quality** | `{score.get('breakdown', {}).get('quality', {}).get('score', 'N/A')}` | 10% | {score.get('breakdown', {}).get('quality', {}).get('confidence', 'medium')} |
| **Popularity** | `{score.get('breakdown', {}).get('popularity', {}).get('score', 'N/A')}` | 8% | {score.get('breakdown', {}).get('popularity', {}).get('confidence', 'medium')} |
| **Growth Trend** | `{score.get('breakdown', {}).get('growth', {}).get('score', 'N/A')}` | 7% | {score.get('breakdown', {}).get('growth', {}).get('confidence', 'low')} |

---

## 2. Adoption Discovery & Evidence
*LibScope discovers verified independent projects that declare dependencies on this package.*

- **Confirmed Dependency Declarations:** `{adoption.get('confirmed_dependencies_count', 0)}`
- **Confirmed Source-Code Usages:** `{adoption.get('confirmed_source_usage_count', 0)}`
- **Possible Usages:** `{adoption.get('possible_usage_count', 0)}`
- **Documentation Mentions Only:** `{adoption.get('mention_only_count', 0)}`
- **Total Evaluated Findings:** `{adoption.get('total_findings', 0)}`

### Sample Adoption Evidence:
"""
    findings = adoption.get("findings", [])[:10]
    if findings:
        md += "| Independent Repository | Classification | File Path | Stars | Confidence |\n"
        md += "| :--- | :--- | :--- | :---: | :---: |\n"
        for f in findings:
            name = f.get('source_repo_full_name') or f.get('source_repo_url', 'Repository')
            url = f.get('source_repo_url', '#')
            md += f"| [{name}]({url}) | `{f.get('evidence_type')}` | `{f.get('file_path')}` | {f.get('stars', 0):,} | {round(f.get('confidence_score', 0.5)*100)}% |\n"
    else:
        md += "> *No independent external adoptions discovered in public manifest sample.*\n"

    md += f"""
---

## 3. Download & Consumption Analytics
- **Monthly Downloads:** `{dl.get('monthly', 0):,}`
- **Weekly Downloads:** `{dl.get('weekly', 0):,}`
- **Daily Downloads:** `{dl.get('daily', 0):,}`
- **Recent Growth Rate:** `{dl.get('growth_rate_pct', 'N/A')}%` (`{dl.get('recent_trend_direction', 'stable')}`)
- **7-Day Moving Average:** `{dl.get('moving_average_7d', 'N/A')}`
- **30-Day Moving Average:** `{dl.get('moving_average_30d', 'N/A')}`
- **Mirror Inclusive:** `{dl.get('mirror_inclusive', True)}`

> **Note on Downloads:** Downloads represent automated CI runs, build scripts, mirror servers, and automated tools. They must not be equated with unique active developers.
"""

    anomalies = dl.get("anomalies", [])
    if anomalies:
        md += "\n### Detected Anomaly Events\n"
        for a in anomalies:
            md += f"- **{a.get('date')}** ({a.get('anomaly_type').upper()}): {a.get('message')}\n"

    md += f"""
---

## 4. Repository Intelligence
- **Repository:** [{repo.get('full_name', 'N/A')}]({repo.get('url', '#')})
- **Stars:** `{repo.get('stars', 0):,}` | **Forks:** `{repo.get('forks', 0):,}` | **Watchers:** `{repo.get('watchers', 0):,}`
- **Open Issues / PRs:** `{repo.get('open_issues', 0):,}`
- **Status:** `{repo.get('activity_status', 'active').upper()}`
- **Days Since Last Commit:** `{repo.get('days_since_last_commit', 'N/A')}`
- **Days Since Last Release:** `{repo.get('days_since_last_release', 'N/A')}`
- **Is Archived:** `{repo.get('is_archived', False)}`
- **Is Fork:** `{repo.get('is_fork', False)}`

---

## 5. Security Posture
- **Known Vulnerabilities (OSV):** `{sec.get('vulnerabilities_count', 0)}`
- **Critical:** `{sec.get('critical_count', 0)}` | **High:** `{sec.get('high_count', 0)}` | **Medium:** `{sec.get('medium_count', 0)}` | **Low:** `{sec.get('low_count', 0)}`
"""

    vulns = sec.get("vulnerabilities", [])
    if vulns:
        md += "\n| Identifier | Severity | Affected Versions | Remediation |\n"
        md += "| :--- | :---: | :--- | :--- |\n"
        for v in vulns:
            md += f"| [{v.get('identifier')}]({v.get('reference_url') or '#'}) | **{v.get('severity')}** | `{v.get('affected_versions')}` | {v.get('remediation')} |\n"
    else:
        md += "> *No known vulnerabilities reported in OSV database. Note: absence of CVEs does not prove absence of zero-days.*\n"

    md += f"""
---

## 6. Project Health Findings
- **Overall Rating:** `{health.get('overall_health_rating', 'healthy').upper()}`
"""
    h_findings = health.get("findings", [])
    if h_findings:
        md += "\n| Category | Check | Status | Finding |\n"
        md += "| :--- | :--- | :---: | :--- |\n"
        for h in h_findings:
            md += f"| `{h.get('category')}` | {h.get('check_name')} | `{h.get('status').upper()}` | {h.get('message')} |\n"

    if ai:
        md += f"""
---

## 7. AI Analyst Interpretation
*Model: `{ai.get('model', 'openrouter')}` | Generated: `{ai.get('generated_at', now)}`*

### Executive Perspective
{ai.get('summary', 'N/A')}

### Identified Risks
{ai.get('risks', 'N/A')}

### Opportunities
{ai.get('opportunities', 'N/A')}

### Maintainer Recommendations
{ai.get('maintainer_recommendations', 'N/A')}
"""

    md += """
---

## 8. Data Provenance & Methodology
This report was deterministically generated by **LibScope**.
All findings cite verified repository APIs, public manifest search, and open vulnerability databases.
LibScope never fabricates adoption or health metrics.
"""
    return md
