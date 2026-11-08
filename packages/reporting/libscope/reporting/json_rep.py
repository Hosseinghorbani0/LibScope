"""
JSON Report Formatter for LibScope Intelligence.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict


def generate_json_report(data: Dict[str, Any]) -> str:
    """Generate structured JSON report representation."""
    report_dict = {
        "report_metadata": {
            "generator": "LibScope Software Intelligence Platform",
            "version": "0.1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "format": "json",
        },
        "intelligence": data,
    }
    return json.dumps(report_dict, indent=2, default=str)

