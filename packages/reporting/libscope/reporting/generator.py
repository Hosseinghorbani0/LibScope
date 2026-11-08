"""
Reporting Engine Generator.
Unifies report generation in Markdown, JSON, and HTML.
"""
from typing import Any, Dict
from libscope.reporting.html_rep import generate_html_report
from libscope.reporting.json_rep import generate_json_report
from libscope.reporting.markdown import generate_markdown_report


class ReportGenerator:
    """Orchestrates multi-format intelligence reports."""

    @staticmethod
    def generate(data: Dict[str, Any], format_type: str = "markdown") -> str:
        fmt = format_type.lower().strip()
        if fmt == "json":
            return generate_json_report(data)
        elif fmt == "html":
            return generate_html_report(data)
        elif fmt == "markdown" or fmt == "md":
            return generate_markdown_report(data)
        else:
            raise ValueError(f"Unsupported report format: '{format_type}'. Supported formats: markdown, json, html")

