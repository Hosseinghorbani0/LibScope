"""
Integration tests for askai-python provider interaction using mocked providers.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from libscope.ai.client import AskAIClient
from libscope.ai.config import AIConfig
from libscope.ai.models import PackageAnalysisOutput
from libscope.ai.services import PackageAnalysisService


def test_ask_ai_structured_response_parsing():
    # Setup mock provider response matching ask-ai Response object
    mock_parsed_output = PackageAnalysisOutput(
        summary="Synthesized by AI Engine for testing.",
        risks="Low risks detected.",
        opportunities="High adoption.",
        maintainer_recommendations="Publish security advisories.",
        competitive_position="Solid category leader.",
    )

    mock_resp = MagicMock()
    mock_resp.text = '{"summary": "..."}'
    mock_resp.parsed = mock_parsed_output

    client = AskAIClient(config=AIConfig(api_key="mock-key-12345"))
    # Inject mock provider
    mock_provider = MagicMock()
    mock_provider.ask_async = AsyncMock(return_value=mock_resp)
    client._provider_instance = mock_provider

    service = PackageAnalysisService(client=client)

    async def _run():
        res = await service.analyze(
            name="mock-package",
            ecosystem="pypi",
            latest_version="2.0.0",
            license_str="Apache-2.0",
            repo_url="https://github.com/org/mock",
            monthly_downloads=1000000,
            mirror_inclusive=True,
            growth_trend="accelerating",
            stars=5000,
            forks=400,
            open_issues=12,
            days_since_commit=2,
            days_since_release=10,
            verified_adoptions=85,
            vulnerabilities_count=0,
            critical_high_count=0,
            overall_score=94.0,
            confidence_level="HIGH",
            raw_description="A mocked library for live integration verification.",
        )
        assert res.summary == "Synthesized by AI Engine for testing."
        assert res.competitive_position == "Solid category leader."
        mock_provider.ask_async.assert_called_once()

    asyncio.run(_run())


def test_ask_ai_provider_error_graceful_fallback():
    client = AskAIClient(config=AIConfig(api_key="mock-key-12345"))

    mock_provider = MagicMock()
    # Simulate API failure / rate limit / network error
    mock_provider.ask_async = AsyncMock(side_effect=RuntimeError("Provider 500 error"))
    client._provider_instance = mock_provider

    service = PackageAnalysisService(client=client)

    async def _run():
        res = await service.analyze(
            name="fail-package",
            ecosystem="pypi",
            latest_version="1.0.0",
            license_str="MIT",
            repo_url=None,
            monthly_downloads=20000,
            mirror_inclusive=True,
            growth_trend="stable",
            stars=100,
            forks=10,
            open_issues=2,
            days_since_commit=20,
            days_since_release=30,
            verified_adoptions=5,
            vulnerabilities_count=0,
            critical_high_count=0,
            overall_score=72.0,
            confidence_level="MODERATE",
            raw_description="Fallback testing.",
        )
        # Should gracefully return deterministic fallback with notice
        assert "fail-package" in res.summary
        assert "AI provider unavailable" in res.summary
        assert "72.0/100" in res.summary

    asyncio.run(_run())

