"""
LibScope Command Line Interface.
Built with Typer and Rich.
"""
import asyncio
import json

import typer
from libscope.analyzers.competitor import CompetitorAnalyzer
from libscope.api.demo import seed_demo_data
from libscope.api.orchestrator import run_package_analysis
from libscope.core.config import get_settings
from libscope.core.database import db_session, init_db
from libscope.core.models import (
    AdoptionEvidence,
    AIAnalysis,
    HealthFinding,
    MetricSnapshot,
    Package,
    Score,
    SecurityFinding,
)
from libscope.providers.registry import get_provider_registry
from libscope.reporting.generator import ReportGenerator
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="libscope",
    help="LibScope: Open-Source Software Intelligence Platform. Beyond Downloads.",
    add_completion=False,
)
console = Console()


def format_score(score: float | None) -> str:
    if score is None:
        return "[dim]Insufficient data[/dim]"
    if score >= 85:
        return f"[bold green]{score:.1f}[/bold green]"
    elif score >= 65:
        return f"[bold yellow]{score:.1f}[/bold yellow]"
    return f"[bold red]{score:.1f}[/bold red]"


@app.command()
def analyze(
    package: str = typer.Argument(..., help="Package name or GitHub owner/repo to analyze"),
    provider: str = typer.Option("pypi", "--provider", "-p", help="Ecosystem provider: 'pypi' or 'github'"),
    ai: bool = typer.Option(False, "--ai", help="Enable AI intelligence interpretation"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON instead of tables"),
):
    """Analyze a software package or public GitHub repository."""
    init_db()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        transient=True,
    ) as progress:
        progress.add_task(f"Analyzing {package} ({provider})...", total=None)
        try:
            pkg = asyncio.run(run_package_analysis(package, ecosystem=provider, enable_ai=ai))
        except Exception as exc:
            console.print(f"[bold red]Analysis failed:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc

    with db_session() as session:
        pkg = session.query(Package).filter_by(id=pkg.id).first()
        latest_score = session.query(Score).filter_by(package_id=pkg.id).order_by(Score.calculated_at.desc()).first()
        repo = pkg.repository
        snap = session.query(MetricSnapshot).filter_by(package_id=pkg.id).order_by(MetricSnapshot.recorded_at.desc()).first()
        adoptions = session.query(AdoptionEvidence).filter_by(package_id=pkg.id).all()
        vulns = session.query(SecurityFinding).filter_by(package_id=pkg.id).all()
        ai_analysis = session.query(AIAnalysis).filter_by(package_id=pkg.id).order_by(AIAnalysis.generated_at.desc()).first()

        if as_json:
            out = {
                "package": pkg.name,
                "ecosystem": pkg.ecosystem,
                "version": pkg.latest_version,
                "license": pkg.license,
                "score": latest_score.overall_score if latest_score else None,
                "confidence": latest_score.confidence_level if latest_score else "low",
                "monthly_downloads": snap.downloads_count if snap else 0,
                "stars": repo.stars if repo else 0,
                "verified_adoptions": len(adoptions),
                "vulnerabilities": len(vulns),
            }
            console.print_json(json.dumps(out))
            return

        # Human-readable Rich output
        score_val = latest_score.overall_score if latest_score else None
        conf_str = latest_score.confidence_level.upper() if latest_score else "LOW"

        header_panel = Panel(
            f"[bold white]{pkg.name}[/bold white] ([cyan]{pkg.ecosystem}[/cyan])  "
            f"v{pkg.latest_version or 'unknown'}  |  "
            f"License: [green]{pkg.license or 'Unspecified'}[/green]\n"
            f"Score: {format_score(score_val)}/100 (Confidence: [bold]{conf_str}[/bold])\n"
            f"[dim]{pkg.description or ''}[/dim]",
            title="LibScope Intelligence Overview",
            border_style="cyan",
        )
        console.print(header_panel)

        # Overview Table
        table = Table(title="Core Metrics & Adoption Signals", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Observed Value", style="white")
        table.add_column("Provenance / Note", style="dim")

        table.add_row(
            "Monthly Downloads",
            f"{snap.downloads_count:,}" if snap else "0",
            "pypistats (automated CI/mirrors included)",
        )
        table.add_row(
            "GitHub Stars / Forks",
            f"{repo.stars:,} ★ / {repo.forks:,} ⑂" if repo else "N/A",
            repo.url if repo else "No repository linked",
        )
        table.add_row(
            "Verified Independent Adoptions",
            f"[bold green]{len(adoptions)}[/bold green] confirmed repos",
            "Public dependency manifests (requirements.txt, pyproject.toml)",
        )
        table.add_row(
            "Known Security Advisories",
            f"[bold red]{len(vulns)}[/bold red]" if vulns else "[bold green]0[/bold green]",
            "OSV vulnerability database",
        )
        console.print(table)

        # Sample Adoption Evidence
        if adoptions:
            adopt_table = Table(title="Sample Verified Adoption Evidence", show_header=True, header_style="bold green")
            adopt_table.add_column("Repository", style="cyan")
            adopt_table.add_column("Classification", style="yellow")
            adopt_table.add_column("Manifest File", style="white")
            adopt_table.add_column("Stars", justify="right")

            for a in adoptions[:5]:
                adopt_table.add_row(a.source_repo_full_name, a.evidence_type, a.file_path, f"{a.stars:,}")
            console.print(adopt_table)

        # AI Analyst Summary
        if ai_analysis and ai_analysis.summary:
            ai_panel = Panel(
                f"[bold cyan]AI Executive Summary:[/bold cyan]\n{ai_analysis.summary}\n\n"
                f"[bold red]Key Risks:[/bold red]\n{ai_analysis.risks or 'None identified'}\n\n"
                f"[bold green]Maintainer Recommendations:[/bold green]\n{ai_analysis.maintainer_recommendations or 'None'}",
                title=f"AI Analyst Interpretation ({ai_analysis.model})",
                border_style="magenta",
            )
            console.print(ai_panel)


@app.command()
def compare(
    packages: list[str] = typer.Argument(..., help="Two or more package names to compare"),
):
    """Compare multiple software packages side-by-side."""
    init_db()

    with db_session() as session:
        pkg_objs = session.query(Package).filter(Package.name.in_([p.lower().strip() for p in packages])).all()
        if len(pkg_objs) < 2:
            console.print("[bold yellow]Not enough packages analyzed yet for comparison.[/bold yellow]")
            console.print("Run 'libscope analyze <pkg>' on each package first, or seed demo data with 'libscope demo'.")
            raise typer.Exit(code=1)

        analyzer = CompetitorAnalyzer()
        pkg_data_list = []
        for p in pkg_objs:
            latest_score = session.query(Score).filter_by(package_id=p.id).order_by(Score.calculated_at.desc()).first()
            snap = session.query(MetricSnapshot).filter_by(package_id=p.id).order_by(MetricSnapshot.recorded_at.desc()).first()
            repo = p.repository
            adoptions = session.query(AdoptionEvidence).filter_by(package_id=p.id).count()
            vulns = session.query(SecurityFinding).filter_by(package_id=p.id).count()

            pkg_data_list.append({
                "name": p.name,
                "ecosystem": p.ecosystem,
                "overall_score": latest_score.overall_score if latest_score else None,
                "confidence": latest_score.confidence_level if latest_score else "low",
                "monthly_downloads": snap.downloads_count if snap else 0,
                "stars": repo.stars if repo else 0,
                "forks": repo.forks if repo else 0,
                "open_issues": repo.open_issues if repo else 0,
                "latest_version": p.latest_version,
                "confirmed_adoptions_count": adoptions,
                "vulnerabilities_count": vulns,
                "license": p.license,
            })

        res = analyzer.compare(pkg_data_list)

        table = Table(title="Competitor Intelligence Comparison", show_header=True, header_style="bold cyan")
        table.add_column("Package", style="bold white")
        table.add_column("Score", justify="center")
        table.add_column("Monthly Downloads", justify="right")
        table.add_column("GitHub Stars", justify="right")
        table.add_column("Verified Adoptions", justify="right")
        table.add_column("Vulnerabilities", justify="center")
        table.add_column("License")

        for item in res.packages:
            table.add_row(
                item.package_name,
                format_score(item.overall_score),
                f"{item.monthly_downloads:,}",
                f"{item.stars:,}",
                f"{item.confirmed_adoptions_count}",
                f"[red]{item.vulnerabilities_count}[/red]" if item.vulnerabilities_count > 0 else "[green]0[/green]",
                item.license or "N/A",
            )
        console.print(table)
        console.print(f"\n[bold]Summary:[/bold] {res.comparative_summary}")


@app.command()
def report(
    package: str = typer.Argument(..., help="Package name"),
    format_type: str = typer.Option("markdown", "--format", "-f", help="Format: markdown, json, or html"),
    output: str | None = typer.Option(None, "--output", "-o", help="File path to write report to"),
):
    """Generate and export a reproducible intelligence report."""
    init_db()

    with db_session() as session:
        pkg = session.query(Package).filter_by(name=package.lower().strip()).first()
        if not pkg:
            console.print(f"[bold red]Package '{package}' not found in local database.[/bold red]")
            console.print(f"Run 'libscope analyze {package}' first.")
            raise typer.Exit(code=1)

        score = session.query(Score).filter_by(package_id=pkg.id).order_by(Score.calculated_at.desc()).first()
        repo = pkg.repository
        snap = session.query(MetricSnapshot).filter_by(package_id=pkg.id).order_by(MetricSnapshot.recorded_at.desc()).first()
        health_findings = session.query(HealthFinding).filter_by(package_id=pkg.id).all()
        sec_findings = session.query(SecurityFinding).filter_by(package_id=pkg.id).all()
        adoptions = session.query(AdoptionEvidence).filter_by(package_id=pkg.id).order_by(AdoptionEvidence.stars.desc()).all()
        ai_item = session.query(AIAnalysis).filter_by(package_id=pkg.id).order_by(AIAnalysis.generated_at.desc()).first()

        data_payload = {
            "package": {
                "name": pkg.name,
                "ecosystem": pkg.ecosystem,
                "description": pkg.description,
                "homepage": pkg.homepage,
                "repository_url": pkg.repository_url,
                "license": pkg.license,
                "latest_version": pkg.latest_version,
            },
            "score": {
                "overall_score": score.overall_score if score else None,
                "confidence_level": score.confidence_level if score else "low",
                "version": score.version if score else "v1.0.0",
                "explanation": score.explanation if score else "N/A",
                "breakdown": json.loads(score.breakdown) if (score and score.breakdown) else {},
            },
            "repository": {
                "full_name": repo.full_name if repo else "N/A",
                "url": repo.url if repo else "#",
                "stars": repo.stars if repo else 0,
                "forks": repo.forks if repo else 0,
                "open_issues": repo.open_issues if repo else 0,
                "watchers": repo.watchers if repo else 0,
                "is_archived": repo.is_archived if repo else False,
                "is_fork": repo.is_fork if repo else False,
            },
            "downloads": {
                "monthly": snap.downloads_count if snap else 0,
                "growth_rate_pct": snap.growth_rate if snap else None,
                "mirror_inclusive": True,
            },
            "adoption": {
                "confirmed_dependencies_count": sum(1 for a in adoptions if "dependency" in a.evidence_type.lower()),
                "confirmed_source_usage_count": sum(1 for a in adoptions if "source-code" in a.evidence_type.lower()),
                "possible_usage_count": sum(1 for a in adoptions if "possible" in a.evidence_type.lower()),
                "mention_only_count": sum(1 for a in adoptions if "mention" in a.evidence_type.lower()),
                "total_findings": len(adoptions),
                "findings": [
                    {
                        "source_repo_full_name": a.source_repo_full_name,
                        "source_repo_url": a.source_repo_url,
                        "file_path": a.file_path,
                        "evidence_type": a.evidence_type,
                        "stars": a.stars,
                        "confidence_score": a.confidence_score,
                    }
                    for a in adoptions[:20]
                ],
            },
            "security": {
                "vulnerabilities_count": len(sec_findings),
                "critical_count": sum(1 for s in sec_findings if s.severity == "CRITICAL"),
                "high_count": sum(1 for s in sec_findings if s.severity == "HIGH"),
                "medium_count": sum(1 for s in sec_findings if s.severity == "MEDIUM"),
                "low_count": sum(1 for s in sec_findings if s.severity == "LOW"),
                "vulnerabilities": [
                    {
                        "identifier": s.identifier,
                        "severity": s.severity,
                        "affected_versions": s.affected_range,
                        "remediation": s.remediation,
                        "reference_url": s.reference_url,
                    }
                    for s in sec_findings
                ],
            },
            "health": {
                "overall_health_rating": "healthy",
                "findings": [
                    {
                        "category": h.category,
                        "check_name": h.check_name,
                        "status": h.status,
                        "message": h.message,
                    }
                    for h in health_findings
                ],
            },
            "ai": {
                "model": ai_item.model if ai_item else "N/A",
                "summary": ai_item.summary if ai_item else None,
                "risks": ai_item.risks if ai_item else None,
                "opportunities": ai_item.opportunities if ai_item else None,
                "maintainer_recommendations": ai_item.maintainer_recommendations if ai_item else None,
            } if ai_item else None,
        }

        content = ReportGenerator.generate(data_payload, format_type=format_type)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[bold green]Report saved to:[/bold green] {output}")
        else:
            console.print(content)


@app.command()
def history(
    package: str = typer.Argument(..., help="Package name"),
):
    """View historical snapshots and metrics over time."""
    init_db()

    with db_session() as session:
        pkg = session.query(Package).filter_by(name=package.lower().strip()).first()
        if not pkg:
            console.print(f"[bold red]Package '{package}' not found in database.[/bold red]")
            raise typer.Exit(code=1)

        snaps = session.query(MetricSnapshot).filter_by(package_id=pkg.id).order_by(MetricSnapshot.recorded_at.desc()).all()
        table = Table(title=f"Historical Snapshots: {pkg.name}", show_header=True, header_style="bold blue")
        table.add_column("Recorded Date", style="cyan")
        table.add_column("Period")
        table.add_column("Downloads", justify="right")
        table.add_column("Growth Rate", justify="right")
        table.add_column("Stars", justify="right")

        for s in snaps:
            table.add_row(
                s.recorded_at.strftime("%Y-%m-%d %H:%M"),
                s.period,
                f"{s.downloads_count:,}",
                f"{s.growth_rate:+.1f}%" if s.growth_rate is not None else "N/A",
                f"{s.stars_count:,}" if s.stars_count is not None else "N/A",
            )
        console.print(table)


@app.command()
def providers():
    """List supported ecosystem providers and explicit capabilities."""
    registry = get_provider_registry()
    table = Table(title="LibScope Ecosystem Providers", show_header=True, header_style="bold green")
    table.add_column("Provider", style="bold white")
    table.add_column("Supported Ecosystems", style="cyan")
    table.add_column("Explicit Capabilities", style="dim")

    for p in registry.list_providers():
        caps = [k for k, v in p["capabilities"].items() if v]
        table.add_row(
            p["name"],
            ", ".join(p["supported_ecosystems"]),
            ", ".join(caps[:4]) + ("..." if len(caps) > 4 else ""),
        )
    console.print(table)


@app.command()
def config():
    """Display active configuration status (secrets redacted)."""
    settings = get_settings()
    table = Table(title="LibScope Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="white")
    table.add_column("Value", style="green")

    table.add_row("Database URL", settings.database_url.split("@")[-1])
    table.add_row("GitHub Token Active", "Yes (Configured)" if settings.effective_github_token else "No (Unauthenticated, 60 req/hr)")
    table.add_row("AI Provider", settings.ai_provider)
    table.add_row("AI API Key Active", "Yes (Configured)" if settings.effective_ai_api_key else "No (Deterministic Fallback Mode)")
    table.add_row("AI Model", settings.ai_model)
    table.add_row("SSRF Protection", "Enforced (Strict)" if settings.enforce_ssrf_protection else "Disabled")
    table.add_row("Environment", settings.environment)
    console.print(table)


@app.command()
def demo():
    """Seed sample benchmark packages for offline exploration."""
    init_db()
    ids = seed_demo_data()
    console.print(f"[bold green]Seeded {len(ids)} demo packages successfully![/bold green]")
    console.print("Run 'libscope analyze fastapi' or 'libscope compare fastapi requests askai-python' to inspect.")


if __name__ == "__main__":
    app()

