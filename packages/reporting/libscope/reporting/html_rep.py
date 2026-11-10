"""
HTML Report Formatter for LibScope Intelligence.
Produces standalone, beautifully styled dark-first HTML intelligence reports.
"""
import html
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit


def _escape(value: Any, default: str = "N/A") -> str:
    return html.escape(str(value)) if value is not None else default


def _metric(value: Any) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return _escape(value)


def _safe_link(value: Any) -> str:
    if not isinstance(value, str) or any(ord(char) < 32 for char in value) or "\\" in value:
        return ""
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return ""
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password or port == 0:
        return ""
    return html.escape(value, quote=True)


def generate_html_report(data: dict[str, Any]) -> str:
    """Generate self-contained, responsive dark HTML report."""
    pkg = data.get("package", {})
    repo = data.get("repository", {})
    score = data.get("score", {})
    dl = data.get("downloads", {})
    health = data.get("health", {}) or {}
    security = data.get("security", {}) or {}
    adoption = data.get("adoption", {})
    ai = data.get("ai")
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    overall = score.get("overall_score")
    overall_display = _escape(overall)
    conf = _escape(str(score.get("confidence_level", "medium")).upper())
    pkg_name = _escape(pkg.get("name"), "Package")
    ecosystem = _escape(pkg.get("ecosystem", "pypi"))
    health_rating = _escape(health.get("overall_health_rating", "unknown"))
    adoption_status = _escape(adoption.get("status", "not_checked"))
    security_status = _escape(security.get("status", "not_checked"))

    html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LibScope Report - {pkg_name}</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #131b2e;
      --border: #1e293b;
      --accent: #38bdf8;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2rem 1rem;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 2rem;
    }}
    .report-brand {{ display: flex; align-items: center; gap: 0.75rem; }}
    .report-brand-mark {{ width: 2.8rem; height: 2.8rem; flex: 0 0 auto; }}
    .report-brand-name {{ font-size: 1.3rem; font-weight: 800; color: var(--text); letter-spacing: -0.5px; }}
    .report-brand-tagline {{ font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.12em; text-transform: uppercase; }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      background: #1e293b;
      color: #38bdf8;
      border: 1px solid #334155;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .card h2 {{
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 1rem;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .score-banner {{
      display: flex;
      align-items: center;
      gap: 2rem;
      background: linear-gradient(135deg, #131b2e 0%, #1e293b 100%);
      border: 1px solid var(--accent);
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 2rem;
    }}
    .score-circle {{
      width: 90px;
      height: 90px;
      border-radius: 50%;
      background: #0f172a;
      border: 4px solid var(--accent);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-size: 1.75rem;
      font-weight: 800;
      color: var(--accent);
    }}
    .score-circle span {{ font-size: 0.65rem; color: var(--text-muted); font-weight: 400; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
    th {{ color: var(--text-muted); font-weight: 600; background: #0f172a; }}
    .stat-row {{ display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #1e293b; font-size: 0.9rem; }}
    .stat-label {{ color: var(--text-muted); }}
    .stat-val {{ font-weight: 600; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .ai-box {{
      background: #1e1e38;
      border: 1px solid #6366f1;
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }}
    footer {{
      text-align: center;
      color: var(--text-muted);
      font-size: 0.8rem;
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <div class="report-brand">
          <svg class="report-brand-mark" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
            <path d="M20 24V14h10M44 14h10v10M54 40v10H44M30 50H20V40" fill="none" stroke="#69d5cb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="m27 27-7-7m17 7 7-7m-17 17-7 7m17-7 7 7" fill="none" stroke="#8bb4bb" stroke-width="1.7" stroke-linecap="round"/>
            <path d="M32 22 41 27v10l-9 5-9-5V27z" fill="#32b9b1" stroke="#32b9b1" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="m27 29 5 3 5-3m-5 3v6" fill="none" stroke="#09212b" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="20" cy="20" r="2.5" fill="#a2e8df"/><circle cx="44" cy="20" r="2.5" fill="#a2e8df"/>
            <circle cx="20" cy="44" r="2.5" fill="#a2e8df"/><circle cx="44" cy="44" r="2.5" fill="#a2e8df"/>
          </svg>
          <div><div class="report-brand-name">LibScope</div><div class="report-brand-tagline">Beyond Downloads</div></div>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted);">Open-Source Software Intelligence Platform</div>
      </div>
      <div>
        <span class="badge">{ecosystem}</span>
        <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 0.5rem;">{now}</span>
      </div>
    </header>

    <div class="score-banner">
      <div class="score-circle">
        {overall_display}
        <span>/100</span>
      </div>
      <div>
        <h1 style="font-size: 1.8rem; font-weight: 800;">{pkg_name}</h1>
        <p style="color: var(--text-muted); margin-top: 0.25rem;">{html.escape(str(score.get("explanation", "")))}</p>
        <div style="margin-top: 0.75rem;">
          <span class="badge">Confidence: {conf}</span>
          <span class="badge" style="margin-left: 0.5rem;">Version: {_escape(pkg.get("latest_version", "latest"))}</span>
        </div>
      </div>
    </div>

    <div class="grid">
      <!-- Adoption Card -->
      <div class="card">
        <h2>Adoption Evidence: {adoption_status}</h2>
        <p class="stat-label">{_escape("; ".join(str(item) for item in (adoption.get("caveats", []) or [])), "")}</p>
        <div class="stat-row">
          <span class="stat-label">Confirmed Dependencies:</span>
          <span class="stat-val" style="color: var(--success);">{_metric(adoption.get('confirmed_dependencies_count'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Confirmed Source Usages:</span>
          <span class="stat-val">{_metric(adoption.get('confirmed_source_usage_count'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Possible Usages:</span>
          <span class="stat-val">{_metric(adoption.get('possible_usage_count'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Total Evaluated Repos:</span>
          <span class="stat-val">{_metric(adoption.get('total_findings'))}</span>
        </div>
      </div>

      <!-- Repository Intelligence Card -->
      <div class="card">
        <h2>Repository Activity</h2>
        <div class="stat-row">
          <span class="stat-label">GitHub Stars:</span>
          <span class="stat-val">{_metric(repo.get('stars'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Forks:</span>
          <span class="stat-val">{_metric(repo.get('forks'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Open Issues:</span>
          <span class="stat-val">{_metric(repo.get('open_issues'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Last Commit Age:</span>
          <span class="stat-val">{_escape(repo.get('days_since_last_commit'))} days ago</span>
        </div>
      </div>

      <!-- Downloads Card -->
      <div class="card">
        <h2>Downloads & Consumption</h2>
        <div class="stat-row">
          <span class="stat-label">Monthly Downloads:</span>
          <span class="stat-val">{_metric(dl.get('monthly'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Weekly Downloads:</span>
          <span class="stat-val">{_metric(dl.get('weekly'))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Growth Rate:</span>
          <span class="stat-val">{_escape(dl.get('growth_rate_pct'))}%</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">30d Moving Average:</span>
          <span class="stat-val">{_escape(dl.get('moving_average_30d'))}</span>
        </div>
      </div>
    </div>
"""

    if ai:
        html_str += f"""
    <div class="ai-box">
      <h2 style="color: #a5b4fc; margin-bottom: 0.75rem;">AI Analyst Interpretation</h2>
      <p style="margin-bottom: 1rem; color: #e0e7ff;">{_escape(ai.get("summary"), "")}</p>
      <div style="font-size: 0.9rem;">
        <strong style="color: #f87171;">Key Risks:</strong>
        <p style="white-space: pre-line; margin-top: 0.25rem; color: #cbd5e1;">{_escape(ai.get("risks"), "")}</p>
      </div>
      <div style="font-size: 0.9rem; margin-top: 1rem;">
        <strong style="color: #34d399;">Maintainer Recommendations:</strong>
        <p style="white-space: pre-line; margin-top: 0.25rem; color: #cbd5e1;">{_escape(ai.get("maintainer_recommendations"), "")}</p>
      </div>
    </div>
"""

    html_str += """
    <div class="card" style="margin-bottom: 2rem;">
      <h2>Adoption Evidence Details</h2>
      <table>
        <thead>
          <tr>
            <th>Repository</th>
            <th>Classification</th>
            <th>File Path</th>
            <th>Stars</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
"""
    findings = adoption.get("findings", [])[:10]
    if findings:
        for f in findings:
            link = _safe_link(f.get("source_repo_url"))
            repo_name = _escape(f.get("source_repo_full_name"), "")
            repo_cell = (
                f'<a href="{link}" target="_blank" rel="noopener noreferrer">{repo_name}</a>'
                if link
                else repo_name
            )
            html_str += f"""
          <tr>
            <td>{repo_cell}</td>
            <td><span class="badge">{_escape(f.get('evidence_type'), '')}</span></td>
            <td><code>{_escape(f.get('file_path'), '')}</code></td>
            <td>{_metric(f.get('stars'))}</td>
            <td>{round(f.get('confidence_score', 0.0) * 100)}%</td>
          </tr>
"""
    else:
        adoption_message = (
            "No independent adoption was discovered in the checked public manifest sample."
            if adoption.get("status") == "checked"
            else "No verified adoption result is available because the search was not completed."
        )
        html_str += """
          <tr>
            <td colspan="5" style="text-align: center; color: var(--text-muted);">
              """
        html_str += _escape(adoption_message)
        html_str += """
            </td>
          </tr>
"""
    html_str += """
        </tbody>
      </table>
    </div>
"""

    html_str += f"""
    <div class="grid">
      <section class="card">
        <h2>Project Health: {health_rating}</h2>
        <ul>
"""
    health_findings = health.get("findings", []) or []
    for finding in health_findings:
        if not isinstance(finding, dict):
            continue
        html_str += (
            f"<li><strong>{_escape(finding.get('status'), '')}</strong> - "
            f"{_escape(finding.get('check_name'), '')}: {_escape(finding.get('message'), '')}</li>\n"
        )
    if not health_findings:
        html_str += '<li class="stat-label">No health findings were recorded.</li>\n'
    caveats = security.get("caveats", []) or []
    html_str += f"""
        </ul>
      </section>
      <section class="card">
        <h2>Security Check: {security_status}</h2>
        <p>Known vulnerabilities: {_metric(security.get('vulnerabilities_count'))}</p>
        <p class="stat-label">{_escape("; ".join(str(item) for item in caveats), "")}</p>
        <ul>
"""
    vulnerabilities = security.get("vulnerabilities", []) or []
    for vulnerability in vulnerabilities:
        if not isinstance(vulnerability, dict):
            continue
        link = _safe_link(vulnerability.get("reference_url"))
        identifier = _escape(vulnerability.get("identifier"), "Unknown advisory")
        rendered_identifier = (
            f'<a href="{link}" target="_blank" rel="noopener noreferrer">{identifier}</a>'
            if link
            else identifier
        )
        html_str += (
            f"<li>{rendered_identifier} - {_escape(vulnerability.get('severity'), 'UNKNOWN')}: "
            f"{_escape(vulnerability.get('title'), '')}</li>\n"
        )
    if not vulnerabilities:
        message = (
            "No known vulnerabilities were returned."
            if security.get("status") == "checked"
            else "No clean result is available for this security check."
        )
        html_str += f'<li class="stat-label">{_escape(message)}</li>\n'
    html_str += """
        </ul>
      </section>
    </div>

    <footer>
      LibScope Open-Source Intelligence Platform. Checks with incomplete data are identified by their reported status.
    </footer>
  </div>
</body>
</html>
"""
    return html_str
