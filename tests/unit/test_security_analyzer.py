"""OSV status and failure-path tests."""
import asyncio

import httpx
from libscope.analyzers.security import SecurityAnalyzer


def _run_osv_response(response: httpx.Response | Exception):
    async def exercise():
        async def handler(request: httpx.Request) -> httpx.Response:
            if isinstance(response, Exception):
                raise response
            return response

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await SecurityAnalyzer(client).check_vulnerabilities("fastapi")

    return asyncio.run(exercise())


def test_osv_empty_success_is_distinct_from_lookup_failure():
    report = _run_osv_response(httpx.Response(200, json={"vulns": []}))

    assert report.status == "checked"
    assert report.has_known_vulnerabilities is False


def test_osv_server_error_and_rate_limit_are_not_clean_results():
    server_error = _run_osv_response(httpx.Response(500, json={"error": "server"}))
    rate_limited = _run_osv_response(httpx.Response(429, json={"error": "rate limit"}))

    assert server_error.status == "failed"
    assert rate_limited.status == "rate_limited"
    assert server_error.error
    assert not server_error.has_known_vulnerabilities


def test_osv_bad_request_and_malformed_response_are_failures():
    bad_request = _run_osv_response(httpx.Response(400, json={"error": "bad request"}))
    malformed = _run_osv_response(httpx.Response(200, content=b"not-json"))
    invalid_shape = _run_osv_response(httpx.Response(200, json={"vulns": "not-a-list"}))

    assert bad_request.status == "failed"
    assert malformed.status == "failed"
    assert invalid_shape.status == "failed"


def test_osv_network_failure_and_unsupported_ecosystem_are_distinct():
    network_failure = _run_osv_response(httpx.ConnectError("network unavailable"))

    async def unsupported():
        async with httpx.AsyncClient() as client:
            return await SecurityAnalyzer(client).check_vulnerabilities("repo", "github")

    unsupported_report = asyncio.run(unsupported())

    assert network_failure.status == "failed"
    assert unsupported_report.status == "unsupported"


def test_osv_reports_partial_data_when_advisory_is_malformed():
    report = _run_osv_response(
        httpx.Response(
            200,
            json={
                "vulns": [
                    {"id": "OSV-1", "affected": "invalid"},
                    {"id": "OSV-2", "database_specific": {"severity": "HIGH"}},
                ]
            },
        )
    )

    assert report.status == "partial"
    assert len(report.vulnerabilities) == 1
    assert report.high_count == 1
