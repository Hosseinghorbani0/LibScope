"""
Security Intelligence Analysis Service powered by askai-python.
"""
from typing import Any

from libscope.ai.client import AskAIClient
from libscope.ai.models import SecurityAssessmentOutput
from libscope.ai.output_validator import AIOutputValidator
from libscope.ai.prompts.security_prompts import SECURITY_ANALYSIS_PROMPT
from libscope.core.logging import get_logger

logger = get_logger("ai.service.security")


class SecurityAnalysisService:
    """Synthesizes vulnerability reports and security posture."""

    def __init__(self, client: AskAIClient | None = None):
        self.client = client or AskAIClient()

    async def analyze(
        self,
        name: str,
        vulnerabilities_count: int,
        critical_high_count: int,
        has_security_policy: bool,
        advisories: list[dict[str, Any]] | None = None,
    ) -> SecurityAssessmentOutput:
        """
        Evaluate project security posture using askai-python or deterministic fallback.
        """
        if not self.client.is_available:
            return self._build_deterministic_fallback(
                name=name,
                vulnerabilities_count=vulnerabilities_count,
                critical_high_count=critical_high_count,
                has_security_policy=has_security_policy,
                advisories=advisories,
            )

        adv_lines: list[str] = []
        for adv in (advisories or [])[:5]:
            adv_id = adv.get("id") or adv.get("cve_id", "Unknown ID")
            summary = adv.get("summary", "No details")[:100]
            adv_lines.append(f"- {adv_id}: {summary}")
        adv_str = "\n".join(adv_lines) if adv_lines else "None reported in OSV database."

        prompt = SECURITY_ANALYSIS_PROMPT.format(
            name=name,
            vulnerabilities_count=vulnerabilities_count,
            critical_high_count=critical_high_count,
            has_security_policy="Published in repository" if has_security_policy else "Not published",
            advisories_summary=adv_str,
        )

        try:
            raw_output = await self.client.ask_async(
                prompt=prompt,
                response_model=SecurityAssessmentOutput,
            )
            return AIOutputValidator.validate_model(raw_output, SecurityAssessmentOutput)
        except Exception as exc:
            logger.warning(f"Security AI analysis failed for {name}: {exc}. Using deterministic fallback.")
            return self._build_deterministic_fallback(
                name=name,
                vulnerabilities_count=vulnerabilities_count,
                critical_high_count=critical_high_count,
                has_security_policy=has_security_policy,
                advisories=advisories,
                notice=f"AI service unavailable ({exc}). Deterministic evaluation provided.",
            )

    def _build_deterministic_fallback(
        self,
        name: str,
        vulnerabilities_count: int,
        critical_high_count: int,
        has_security_policy: bool,
        advisories: list[dict[str, Any]] | None,
        notice: str | None = None,
    ) -> SecurityAssessmentOutput:
        policy_status = "PUBLISHED (SECURITY.md present)" if has_security_policy else "ABSENT (No SECURITY.md discovered)"

        if critical_high_count > 0:
            posture = "ACTION_REQUIRED"
            summary = (
                f"Package '{name}' has {critical_high_count} critical or high severity vulnerabilities "
                f"(out of {vulnerabilities_count} total). Immediate remediation or patch updates are strongly advised."
            )
        elif vulnerabilities_count > 0:
            posture = "ELEVATED_RISK"
            summary = (
                f"Package '{name}' has {vulnerabilities_count} known low/medium security advisories. "
                "Review dependencies for available patched releases."
            )
        else:
            posture = "CLEAN"
            summary = f"No known vulnerabilities reported in OSV for package '{name}'. Posture appears clean."

        if notice:
            summary = f"[{notice}] {summary}"

        priority_fixes: list[str] = []
        if advisories:
            for adv in advisories[:3]:
                adv_id = adv.get("id") or adv.get("cve_id", "Advisory")
                priority_fixes.append(f"Upgrade to mitigate {adv_id}")

        if not has_security_policy:
            priority_fixes.append("Establish a clear vulnerability disclosure procedure (SECURITY.md)")

        return SecurityAssessmentOutput(
            posture=posture,
            remediation_summary=summary,
            priority_fixes=priority_fixes or ["Maintain ongoing automated vulnerability scanning in CI."],
            disclosure_policy_status=policy_status,
        )

