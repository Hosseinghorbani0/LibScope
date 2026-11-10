"""Tests for API authentication, rate limiting, and outbound URL enforcement."""
import asyncio

import httpx
import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from libscope.api import main as api_main
from libscope.api import security as api_security
from libscope.core import security as network_security
from libscope.core.config import Settings


def test_api_key_is_required_in_production_and_compared_safely(monkeypatch):
    settings = Settings(_env_file=None)
    settings.environment = "production"
    settings.api_key = "k" * 32
    monkeypatch.setattr(api_security, "get_settings", lambda: settings)

    assert api_security.require_api_key(f"Bearer {settings.api_key}") is None
    with pytest.raises(HTTPException) as missing:
        api_security.require_api_key(None)
    assert missing.value.status_code == 401

    settings.api_key = None
    with pytest.raises(HTTPException) as unconfigured:
        api_security.require_api_key(None)
    assert unconfigured.value.status_code == 503


def test_protected_demo_route_requires_a_valid_production_key(monkeypatch):
    settings = Settings(_env_file=None)
    settings.environment = "production"
    settings.enable_demo_mode = False
    settings.api_key = None
    monkeypatch.setattr(api_security, "get_settings", lambda: settings)
    monkeypatch.setattr(api_main, "settings", settings)
    client = TestClient(api_main.app)

    assert client.post("/api/v1/demo/seed").status_code == 503

    settings.api_key = "configured-test-key"
    assert client.post("/api/v1/demo/seed", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.post(
        "/api/v1/demo/seed",
        headers={"Authorization": "Bearer configured-test-key"},
    ).status_code == 404


def test_expensive_api_requests_are_rate_limited(monkeypatch):
    monkeypatch.setattr(api_security, "_RATE_LIMIT_PER_WINDOW", 2)
    api_security._request_times.clear()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/analyze",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
            "server": ("testserver", 80),
            "query_string": b"",
        }
    )

    api_security.rate_limit_expensive_requests(request)
    api_security.rate_limit_expensive_requests(request)
    with pytest.raises(HTTPException) as limited:
        api_security.rate_limit_expensive_requests(request)
    assert limited.value.status_code == 429
    assert limited.value.headers["Retry-After"]
    api_security._request_times.clear()


def test_outbound_http_client_validates_each_request(monkeypatch):
    monkeypatch.setattr(network_security, "validate_safe_url", lambda url: False)
    client = network_security.create_safe_httpx_client()
    request_hook = client.event_hooks["request"][0]

    async def exercise():
        with pytest.raises(httpx.RequestError):
            await request_hook(httpx.Request("GET", "https://example.com"))
        await client.aclose()

    asyncio.run(exercise())
