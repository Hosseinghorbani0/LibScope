"""Tests for authenticated, content-verified GitHub adoption discovery."""
import asyncio
import base64
from types import SimpleNamespace

import httpx
from libscope.analyzers.adoption import AdoptionAnalyzer
from libscope.providers import github
from libscope.providers.github import GitHubProvider


def test_search_fetches_and_returns_verified_manifest_content():
    manifest = '[project]\ndependencies = ["FastAPI>=0.100"]'

    async def exercise():
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"].startswith("Bearer ")
            if request.url.path == "/search/code":
                body = {
                    "items": [
                        {
                            "path": "pyproject.toml",
                            "repository": {
                                "full_name": "example/project",
                                "html_url": "https://github.com/example/project",
                            },
                        }
                    ]
                }
            else:
                body = {
                    "size": len(manifest.encode()),
                    "encoding": "base64",
                    "content": base64.b64encode(manifest.encode()).decode(),
                }
            return httpx.Response(200, json=body)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = GitHubProvider(token="test-token", client=client)
            return await provider.search_code_adoption("fastapi"), provider.code_search_status

    results, status = asyncio.run(exercise())

    assert len(results) == 1
    assert status == "checked"
    assert results[0]["fetch_status"] == "available"
    assert results[0]["raw_match"] == manifest
    classified = AdoptionAnalyzer().process_raw_findings("fastapi", None, results)
    assert classified.confirmed_dependencies_count == 1


def test_manifest_fetch_failure_is_not_returned_as_content():
    async def exercise():
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/search/code":
                return httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "path": "requirements.txt",
                                "repository": {
                                    "full_name": "private/project",
                                    "html_url": "https://github.com/private/project",
                                },
                            }
                        ]
                    },
                )
            return httpx.Response(404, json={"message": "Not Found"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = GitHubProvider(token="test-token", client=client)
            return await provider.search_code_adoption("fastapi"), provider.code_search_status

    results, status = asyncio.run(exercise())

    assert status == "partial"
    assert results[0]["fetch_status"] == "missing"
    assert "raw_match" not in results[0]


def test_search_without_token_is_reported_as_unavailable(monkeypatch):
    monkeypatch.setattr(
        github,
        "get_settings",
        lambda: SimpleNamespace(effective_github_token=None),
    )
    provider = GitHubProvider()

    assert asyncio.run(provider.search_code_adoption("fastapi")) == []
    assert provider.code_search_status == "unavailable"


def test_unavailable_manifest_content_does_not_create_adoption():
    result = AdoptionAnalyzer().process_raw_findings(
        "fastapi",
        None,
        [
            {
                "repo_full_name": "example/project",
                "file_path": "requirements.txt",
                "fetch_status": "inaccessible",
            }
        ],
    )

    assert result.total_findings == 0
    assert result.confirmed_dependencies_count == 0
    assert result.limitations

