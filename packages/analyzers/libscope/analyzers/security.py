"""
Security Intelligence and Vulnerability Analysis.
Integrates with OSV (Open Source Vulnerabilities) API for CVE and GHSA tracking.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from libscope.core.logging import get_logger
from libscope.core.security import create_safe_httpx_client

logger = get_logger("analyzer.security")


@dataclass
class VulnerabilityFinding:
    identifier: str  # GHSA or CVE ID
    severity: str    # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
    affected_package: str
    affected_versions: str
    fixed_version: Optional[str]
    source: str      # OSV / GHSA / NVD
    reference_url: Optional[str]
    title: str
    details: str
    remediation: Optional[str]
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SecurityReport:
    package_name: str
    ecosystem: str
    checked_at: datetime
    has_known_vulnerabilities: bool
    vulnerabilities: List[VulnerabilityFinding] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    caveats: List[str] = field(default_factory=list)


class SecurityAnalyzer:
    """Queries OSV vulnerability database and evaluates package security posture."""

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = create_safe_httpx_client()
        return self._client

    def _normalize_severity(self, raw_vuln: Dict[str, Any]) -> str:
        # Check database_specific or severity CVSS
        severities = raw_vuln.get("severity", [])
        for s in severities:
            score_type = s.get("type")
            score_val = s.get("score")
            # If CVSS score is available
            if score_type and "CVSS" in score_type and isinstance(score_val, str):
                if score_val.startswith("CVSS:"):
                    # We can estimate or check database_specific
                    pass

        db_spec = raw_vuln.get("database_specific", {})
        sev = db_spec.get("severity")
        if isinstance(sev, str):
            sev_upper = sev.upper()
            if sev_upper in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                return sev_upper

        # Check ecosystem_specific
        eco_spec = raw_vuln.get("ecosystem_specific", {})
        if eco_spec.get("severity"):
            return str(eco_spec["severity"]).upper()

        return "MEDIUM"

    async def check_vulnerabilities(self, package_name: str, ecosystem: str = "PyPI") -> SecurityReport:
        now = datetime.now(timezone.utc)
        caveats = [
            "Absence of reported vulnerabilities indicates no publicly known CVEs; it does not guarantee absence of zero-day vulnerabilities or security flaws."
        ]

        # OSV expects ecosystem capitalized (e.g. PyPI, npm)
        osv_eco = "PyPI" if ecosystem.lower() in ("pypi", "python") else ecosystem.capitalize()
        payload = {
            "package": {
                "name": package_name.lower().strip(),
                "ecosystem": osv_eco,
            }
        }

        vulnerabilities: List[VulnerabilityFinding] = []
        client = await self._get_client()

        try:
            url = "https://api.osv.dev/v1/query"
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_vulns = data.get("vulns", [])
                for v in raw_vulns:
                    vid = v.get("id", "UNKNOWN-VULN")
                    severity = self._normalize_severity(v)
                    summary = v.get("summary", "") or v.get("details", "")[:120]
                    details = v.get("details", "")

                    # Extract affected version range and fixed version
                    affected_ranges = []
                    fixed_ver = None
                    for aff in v.get("affected", []):
                        for r in aff.get("ranges", []):
                            events = r.get("events", [])
                            for ev in events:
                                if "fixed" in ev:
                                    fixed_ver = ev["fixed"]
                                if "introduced" in ev:
                                    affected_ranges.append(f">={ev['introduced']}")

                    # Extract reference url
                    ref_url = None
                    for ref in v.get("references", []):
                        if ref.get("url"):
                            ref_url = ref["url"]
                            break

                    remediation = f"Upgrade {package_name} to {fixed_ver} or newer." if fixed_ver else "Review advisory and restrict usage if affected."

                    vulnerabilities.append(
                        VulnerabilityFinding(
                            identifier=vid,
                            severity=severity,
                            affected_package=package_name,
                            affected_versions=", ".join(affected_ranges) if affected_ranges else "all versions",
                            fixed_version=fixed_ver,
                            source="OSV",
                            reference_url=ref_url,
                            title=summary[:200] if summary else f"Security advisory for {package_name}",
                            details=details,
                            remediation=remediation,
                        )
                    )

        except Exception as exc:
            logger.warning(f"OSV vulnerability lookup failed for {package_name}: {exc}")
            caveats.append(f"Vulnerability database check encountered network error: {str(exc)}")

        crit = sum(1 for v in vulnerabilities if v.severity == "CRITICAL")
        high = sum(1 for v in vulnerabilities if v.severity == "HIGH")
        med = sum(1 for v in vulnerabilities if v.severity == "MEDIUM")
        low = sum(1 for v in vulnerabilities if v.severity == "LOW")

        return SecurityReport(
            package_name=package_name,
            ecosystem=ecosystem,
            checked_at=now,
            has_known_vulnerabilities=bool(vulnerabilities),
            vulnerabilities=vulnerabilities,
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            caveats=caveats,
        )

