"""
JSON Report Formatter for LibScope Intelligence.
"""
import json
from datetime import UTC, datetime
from typing import Any


def generate_json_report(data: dict[str, Any]) -> str:
    """Generate structured JSON report representation."""
    report_dict = {
        "report_metadata": {
            "generator": "LibScope Software Intelligence Platform",
            "version": "0.1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "format": "json",
        },
        "intelligence": data,
    }
    return json.dumps(report_dict, indent=2, default=str)

