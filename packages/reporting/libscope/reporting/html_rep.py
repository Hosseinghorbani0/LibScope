"""
HTML Report Formatter for LibScope Intelligence.
Produces standalone, beautifully styled dark-first HTML intelligence reports.
"""
from datetime import datetime, timezone
import html
from typing import Any, Dict


def generate_html_report(data: Dict[str, Any]) -> str:
    """Generate self-contained, responsive dark HTML report."""
    pkg = data.get("package", {})
    repo = data.get("repository", {})
    score = data.get("score", {})
    dl = data.get("downloads", {})
    health = data.get("health", {})
    sec = data.get("security", {})
    adoption = data.get("adoption", {})
    ai = data.get("ai")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    overall = score.get("overall_score")
    overall_display = f"{overall}" if overall is not None else "N/A"
    conf = html.escape(score.get("confidence_level", "medium").upper())
    pkg_name = html.escape(str(pkg.get("name", "Package")))

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
    .brand {{ font-size: 1.5rem; font-weight: 800; color: var(--accent); letter-spacing: -0.5px; }}
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
        <div class="brand">LibScope</div>
        <div style="font-size: 0.85rem; color: var(--text-muted);">Open-Source Software Intelligence Platform</div>
      </div>
      <div>
        <span class="badge">{pkg.get('ecosystem', 'pypi')}</span>
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
          <span class="badge" style="margin-left: 0.5rem;">Version: {html.escape(str(pkg.get("latest_version", "latest")))}</span>
        </div>
      </div>
    </div>

    <div class="grid">
      <!-- Adoption Card -->
      <div class="card">
        <h2>Adoption Evidence</h2>
        <div class="stat-row">
          <span class="stat-label">Confirmed Dependencies:</span>
          <span class="stat-val" style="color: var(--success);">{adoption.get('confirmed_dependencies_count', 0)}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Confirmed Source Usages:</span>
          <span class="stat-val">{adoption.get('confirmed_source_usage_count', 0)}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Possible Usages:</span>
          <span class="stat-val">{adoption.get('possible_usage_count', 0)}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Total Evaluated Repos:</span>
          <span class="stat-val">{adoption.get('total_findings', 0)}</span>
        </div>
      </div>

      <!-- Repository Intelligence Card -->
      <div class="card">
        <h2>Repository Activity</h2>
        <div class="stat-row">
          <span class="stat-label">GitHub Stars:</span>
          <span class="stat-val">{repo.get('stars', 0):,}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Forks:</span>
          <span class="stat-val">{repo.get('forks', 0):,}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Open Issues:</span>
          <span class="stat-val">{repo.get('open_issues', 0):,}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Last Commit Age:</span>
          <span class="stat-val">{repo.get('days_since_last_commit', 'N/A')} days ago</span>
        </div>
      </div>

      <!-- Downloads Card -->
      <div class="card">
        <h2>Downloads & Consumption</h2>
        <div class="stat-row">
          <span class="stat-label">Monthly Downloads:</span>
          <span class="stat-val">{dl.get('monthly', 0):,}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Weekly Downloads:</span>
          <span class="stat-val">{dl.get('weekly', 0):,}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Growth Rate:</span>
          <span class="stat-val">{dl.get('growth_rate_pct', 'N/A')}%</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">30d Moving Average:</span>
          <span class="stat-val">{dl.get('moving_average_30d', 'N/A')}</span>
        </div>
      </div>
    </div>
"""

    if ai:
        html_str += f"""
    <div class="ai-box">
      <h2 style="color: #a5b4fc; margin-bottom: 0.75rem;">AI Analyst Interpretation</h2>
      <p style="margin-bottom: 1rem; color: #e0e7ff;">{html.escape(ai.get("summary", ""))}</p>
      <div style="font-size: 0.9rem;">
        <strong style="color: #f87171;">Key Risks:</strong>
        <p style="white-space: pre-line; margin-top: 0.25rem; color: #cbd5e1;">{html.escape(ai.get("risks", ""))}</p>
      </div>
      <div style="font-size: 0.9rem; margin-top: 1rem;">
        <strong style="color: #34d399;">Maintainer Recommendations:</strong>
        <p style="white-space: pre-line; margin-top: 0.25rem; color: #cbd5e1;">{html.escape(ai.get("maintainer_recommendations", ""))}</p>
      </div>
    </div>
"""

    html_str += f"""
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
            html_str += f"""
          <tr>
            <td><a href="{html.escape(f.get('source_repo_url', '#'))}" target="_blank">{html.escape(f.get('source_repo_full_name', ''))}</a></td>
            <td><span class="badge">{html.escape(f.get('evidence_type', ''))}</span></td>
            <td><code>{html.escape(f.get('file_path', ''))}</code></td>
            <td>{f.get('stars', 0):,}</td>
            <td>{round(f.get('confidence_score', 0.5) * 100)}%</td>
          </tr>
"""
    else:
        html_str += """
          <tr>
            <td colspan="5" style="text-align: center; color: var(--text-muted);">No independent adoption findings discovered.</td>
          </tr>
"""
    html_str += """
        </tbody>
      </table>
    </div>

    <footer>
      LibScope Open-Source Intelligence Platform. All data verified against public registries and source repositories.
    </footer>
  </div>
</body>
</html>
"""
    return html_str

