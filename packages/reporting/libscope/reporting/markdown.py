"""
Markdown Report Formatter for LibScope Intelligence.
"""
from datetime import UTC, datetime
from typing import Any


def _format_metric(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return f"{value:,}"
    return str(value)


def _format_percent(value: Any, default: str = "N/A") -> str:
    if isinstance(value, (int, float)):
        return f"{value}%"
    return default


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
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    overall = score.get("overall_score")
    score_display = f"**{overall}/100**" if overall is not None else "**Insufficient Data**"
    conf = str(score.get("confidence_level", "medium")).upper()

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

- **Search Status:** `{adoption.get('status', 'not_checked')}`
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
            confidence = f.get("confidence_score")
            confidence_display = f"{round(confidence * 100)}%" if isinstance(confidence, (int, float)) else "N/A"
            md += (
                f"| [{name}]({url}) | `{f.get('evidence_type')}` | `{f.get('file_path')}` "
                f"| {_format_metric(f.get('stars'), '0')} | {confidence_display} |\n"
            )
    else:
        if adoption.get("status") == "checked":
            md += "> *No independent external adoptions discovered in the checked public manifest sample.*\n"
        else:
            md += "> *No verified result is available; adoption search was not completed successfully.*\n"
    for caveat in adoption.get("caveats", []) or []:
        md += f"> *{caveat}*\n"

    md += f"""
---

## 3. Download & Consumption Analytics
- **Monthly Downloads:** `{_format_metric(dl.get('monthly'))}`
- **Weekly Downloads:** `{_format_metric(dl.get('weekly'))}`
- **Daily Downloads:** `{_format_metric(dl.get('daily'))}`
- **Recent Growth Rate:** `{_format_percent(dl.get('growth_rate_pct'))}` (`{dl.get('recent_trend_direction', 'stable')}`)
- **7-Day Moving Average:** `{_format_metric(dl.get('moving_average_7d'))}`
- **30-Day Moving Average:** `{_format_metric(dl.get('moving_average_30d'))}`
- **Mirror Inclusive:** `{dl.get('mirror_inclusive', True)}`

> **Note on Downloads:** Downloads represent automated CI runs, build scripts, mirror servers, and automated tools. They must not be equated with unique active developers.
"""

    anomalies = dl.get("anomalies", [])
    if anomalies:
        md += "\n### Detected Anomaly Events\n"
        for a in anomalies:
            md += f"- **{a.get('date')}** ({str(a.get('anomaly_type', 'unknown')).upper()}): {a.get('message')}\n"

    md += f"""
---

## 4. Repository Intelligence
- **Repository:** [{repo.get('full_name', 'N/A')}]({repo.get('url', '#')})
- **Stars:** `{_format_metric(repo.get('stars'))}` | **Forks:** `{_format_metric(repo.get('forks'))}` | **Watchers:** `{_format_metric(repo.get('watchers'))}`
- **Open Issues / PRs:** `{_format_metric(repo.get('open_issues'))}`
- **Status:** `{str(repo.get('activity_status', 'active')).upper()}`
- **Days Since Last Commit:** `{repo.get('days_since_last_commit', 'N/A')}`
- **Days Since Last Release:** `{repo.get('days_since_last_release', 'N/A')}`
- **Is Archived:** `{repo.get('is_archived', False)}`
- **Is Fork:** `{repo.get('is_fork', False)}`

---

## 5. Security Posture
- **Check Status:** `{sec.get('status', 'not_checked')}`
- **Known Vulnerabilities (OSV):** `{sec.get('vulnerabilities_count') if sec.get('vulnerabilities_count') is not None else 'Not verified'}`
- **Critical:** `{sec.get('critical_count') if sec.get('critical_count') is not None else 'Not verified'}` | **High:** `{sec.get('high_count') if sec.get('high_count') is not None else 'Not verified'}` | **Medium:** `{sec.get('medium_count') if sec.get('medium_count') is not None else 'Not verified'}` | **Low:** `{sec.get('low_count') if sec.get('low_count') is not None else 'Not verified'}`
"""

    vulns = sec.get("vulnerabilities", [])
    if vulns:
        md += "\n| Identifier | Severity | Affected Versions | Remediation |\n"
        md += "| :--- | :---: | :--- | :--- |\n"
        for v in vulns:
            md += f"| [{v.get('identifier')}]({v.get('reference_url') or '#'}) | **{v.get('severity')}** | `{v.get('affected_versions')}` | {v.get('remediation')} |\n"
    else:
        if sec.get("status") == "checked":
            md += "> *No known vulnerabilities reported in OSV database. Note: absence of CVEs does not prove absence of zero-days.*\n"
        else:
            md += "> *No clean result is available because this security check was incomplete or not performed.*\n"

    md += f"""
---

## 6. Project Health Findings
- **Overall Rating:** `{str(health.get('overall_health_rating', 'insufficient_data')).upper()}`
"""
    h_findings = health.get("findings", [])
    if h_findings:
        md += "\n| Category | Check | Status | Finding |\n"
        md += "| :--- | :--- | :---: | :--- |\n"
        for h in h_findings:
            md += f"| `{h.get('category')}` | {h.get('check_name')} | `{str(h.get('status', 'unknown')).upper()}` | {h.get('message')} |\n"

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

