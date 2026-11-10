"""
Security Intelligence and Vulnerability Analysis.
Integrates with OSV (Open Source Vulnerabilities) API for CVE and GHSA tracking.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
from libscope.core.config import get_settings
from libscope.core.logging import get_logger
from libscope.core.security import create_safe_httpx_client

logger = get_logger("analyzer.security")


@dataclass
class VulnerabilityFinding:
    identifier: str  # GHSA or CVE ID
    severity: str    # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
    affected_package: str
    affected_versions: str
    fixed_version: str | None
    source: str      # OSV / GHSA / NVD
    reference_url: str | None
    title: str
    details: str
    remediation: str | None
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SecurityReport:
    package_name: str
    ecosystem: str
    checked_at: datetime
    has_known_vulnerabilities: bool
    vulnerabilities: list[VulnerabilityFinding] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    caveats: list[str] = field(default_factory=list)
    status: str = "checked"
    error: str | None = None


class SecurityAnalyzer:
    """Queries OSV vulnerability database and evaluates package security posture."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = create_safe_httpx_client()
        return self._client

    def _normalize_severity(self, raw_vuln: dict[str, Any]) -> str:
        db_spec = raw_vuln.get("database_specific", {})
        sev = db_spec.get("severity") if isinstance(db_spec, dict) else None
        if isinstance(sev, str):
            sev_upper = sev.upper()
            if sev_upper in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"):
                return sev_upper

        eco_spec = raw_vuln.get("ecosystem_specific", {})
        if isinstance(eco_spec, dict):
            severity = str(eco_spec.get("severity", "")).upper()
            if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"):
                return severity

        return "UNKNOWN"

    async def check_vulnerabilities(self, package_name: str, ecosystem: str = "PyPI") -> SecurityReport:
        now = datetime.now(UTC)
        caveats = [
            "Absence of reported vulnerabilities indicates no publicly known CVEs; it does not guarantee absence of zero-day vulnerabilities or security flaws."
        ]

        ecosystem_map = {
            "pypi": "PyPI",
            "python": "PyPI",
            "npm": "npm",
            "node": "npm",
            "go": "Go",
            "golang": "Go",
            "cargo": "crates.io",
            "rust": "crates.io",
            "maven": "Maven",
            "java": "Maven",
            "nuget": ".NET",
            "dotnet": ".NET",
            "rubygems": "RubyGems",
            "ruby": "RubyGems",
            "packagist": "Packagist",
            "php": "Packagist",
        }
        normalized_ecosystem = ecosystem.lower().strip()
        osv_eco = ecosystem_map.get(normalized_ecosystem)
        if not osv_eco:
            return SecurityReport(
                package_name=package_name,
                ecosystem=ecosystem,
                checked_at=now,
                has_known_vulnerabilities=False,
                caveats=[f"Security lookup is not supported for ecosystem '{ecosystem}'."],
                status="unsupported",
            )
        payload = {
            "package": {
                "name": package_name.lower().strip(),
                "ecosystem": osv_eco,
            }
        }

        vulnerabilities: list[VulnerabilityFinding] = []
        client = await self._get_client()
        status_value = "checked"
        error_message = None
        malformed_findings = False
        url = "https://api.osv.dev/v1/query"
        settings = get_settings()
        attempts = min(max(settings.max_retries + 1, 1), 3)

        for attempt in range(attempts):
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code in (429, 500, 502, 503, 504):
                    if attempt + 1 < attempts:
                        await asyncio.sleep(min(0.25 * (2**attempt), 1.0))
                        continue
                    status_value = "rate_limited" if resp.status_code == 429 else "failed"
                    error_message = f"OSV returned HTTP {resp.status_code}"
                    break
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict) or not isinstance(data.get("vulns", []), list):
                    raise ValueError("OSV response did not contain a valid vulnerability list")
                raw_vulns = data.get("vulns", [])
                for v in raw_vulns:
                    if not isinstance(v, dict):
                        malformed_findings = True
                        continue
                    try:
                        vid = v.get("id", "UNKNOWN-VULN")
                        summary = v.get("summary", "")
                        details = v.get("details", "")
                        if not isinstance(vid, str) or not isinstance(summary, str) or not isinstance(details, str):
                            raise TypeError("invalid advisory text fields")

                        affected_ranges = []
                        fixed_ver = None
                        affected = v.get("affected", [])
                        if not isinstance(affected, list):
                            raise TypeError("invalid affected package list")
                        for aff in affected:
                            if not isinstance(aff, dict):
                                raise TypeError("invalid affected package entry")
                            ranges = aff.get("ranges", [])
                            if not isinstance(ranges, list):
                                raise TypeError("invalid version range list")
                            for version_range in ranges:
                                if not isinstance(version_range, dict):
                                    raise TypeError("invalid version range")
                                events = version_range.get("events", [])
                                if not isinstance(events, list):
                                    raise TypeError("invalid version events")
                                for event in events:
                                    if not isinstance(event, dict):
                                        raise TypeError("invalid version event")
                                    if "fixed" in event and isinstance(event["fixed"], str):
                                        fixed_ver = event["fixed"]
                                    if "introduced" in event and isinstance(event["introduced"], str):
                                        affected_ranges.append(f">={event['introduced']}")

                        references = v.get("references", [])
                        if not isinstance(references, list):
                            raise TypeError("invalid advisory references")
                        ref_url = next(
                            (
                                ref["url"]
                                for ref in references
                                if isinstance(ref, dict) and isinstance(ref.get("url"), str)
                            ),
                            None,
                        )
                        severity = self._normalize_severity(v)
                        title = summary or details[:120] or f"Security advisory for {package_name}"
                        remediation = (
                            f"Upgrade {package_name} to {fixed_ver} or newer."
                            if fixed_ver
                            else "Review advisory and restrict usage if affected."
                        )
                        vulnerabilities.append(
                            VulnerabilityFinding(
                                identifier=vid,
                                severity=severity,
                                affected_package=package_name,
                                affected_versions=", ".join(affected_ranges) if affected_ranges else "all versions",
                                fixed_version=fixed_ver,
                                source="OSV",
                                reference_url=ref_url,
                                title=title[:200],
                                details=details,
                                remediation=remediation,
                            )
                        )
                    except (TypeError, AttributeError):
                        malformed_findings = True
                if malformed_findings:
                    status_value = "partial"
                    error_message = "OSV response contained malformed vulnerability entries"
                break
            except (httpx.HTTPError, ValueError) as exc:
                error_message = str(exc)
                if attempt + 1 < attempts and (
                    not isinstance(exc, httpx.HTTPStatusError)
                    or exc.response.status_code >= 500
                ):
                    await asyncio.sleep(min(0.25 * (2**attempt), 1.0))
                    continue
                status_value = "failed"
                break

        if status_value != "checked":
            logger.warning("OSV lookup %s for %s: %s", status_value, package_name, error_message)
            caveats.append(f"Vulnerability lookup {status_value}; security status is not a clean result.")

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
            status=status_value,
            error=error_message,
        )
