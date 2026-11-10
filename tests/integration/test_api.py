"""
Integration tests for FastAPI REST API endpoints.
"""
import re

from fastapi.testclient import TestClient
from libscope.api.main import app
from libscope.core.database import init_db

client = TestClient(app)


def setup_module():
    init_db()


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_static_dashboard_and_native_assets_are_served():
    page = client.get("/")
    script = client.get("/dashboard-assets/app.js")
    i18n_module = client.get("/dashboard-assets/i18n.js")
    api_module = client.get("/dashboard-assets/api.js")
    stylesheet = client.get("/dashboard-assets/styles.css")
    favicon = client.get("/dashboard-assets/favicon.svg")
    locales = [
        client.get(f"/dashboard-assets/locales/{locale}.json")
        for locale in ("en", "fa", "ar")
    ]
    logos = [
        client.get(f"/dashboard-assets/{name}")
        for name in (
            "logo-light.svg",
            "logo-dark.svg",
            "logo-monochrome.svg",
            "logo-mark.svg",
            "app-icon.svg",
        )
    ]

    assert page.status_code == script.status_code == i18n_module.status_code == api_module.status_code == stylesheet.status_code == favicon.status_code == 200
    assert all(response.status_code == 200 for response in logos)
    assert all(response.status_code == 200 for response in locales)
    assert page.headers["content-type"].startswith("text/html")
    assert script.headers["content-type"].startswith(("text/javascript", "application/javascript"))
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert 'src="/dashboard-assets/app.js"' in page.text
    assert "React" not in script.text
    assert "initializeI18n" in script.text
    assert 'id="language-select"' in script.text
    assert "localStorage" not in api_module.text
    assert "libscope.theme" in script.text
    assert "Authorization" in api_module.text
    locale_dictionaries = [response.json() for response in locales]
    assert set(locale_dictionaries[0]) == set(locale_dictionaries[1]) == set(locale_dictionaries[2])
    for key in locale_dictionaries[0]:
        placeholders = set(re.findall(r"\{\{(\w+)\}\}", locale_dictionaries[0][key]))
        assert all(
            set(re.findall(r"\{\{(\w+)\}\}", dictionary[key])) == placeholders
            for dictionary in locale_dictionaries[1:]
        ), key


def test_version_endpoint():
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "LibScope"
    assert "github_token_configured" in data


def test_demo_seed_and_package_list():
    seed_resp = client.post("/api/v1/demo/seed")
    assert seed_resp.status_code == 200
    assert len(seed_resp.json()["package_ids"]) > 0

    pkgs_resp = client.get("/api/v1/packages")
    assert pkgs_resp.status_code == 200
    packages = pkgs_resp.json()
    assert len(packages) >= 3

    first_pkg_id = packages[0]["id"]
    detail_resp = client.get(f"/api/v1/packages/{first_pkg_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "latest_score" in detail
    assert "repository" in detail


def test_dashboard_summary_is_exact_bounded_and_excludes_job_errors():
    packages = client.get("/api/v1/packages?limit=100").json()
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_packages"] == len(packages)
    assert 0 <= summary["scored_packages"] <= summary["total_packages"]
    assert 0 <= summary["linked_repositories"] <= summary["total_packages"]
    assert summary["latest_package_update"] is not None
    assert len(summary["recent_jobs"]) <= 5
    assert all("error_message" not in job for job in summary["recent_jobs"])
    assert client.get("/api/v1/dashboard/summary?recent_limit=11").status_code == 422


def test_compare_endpoint():
    # Ensure demo packages exist
    client.post("/api/v1/demo/seed")

    comp_resp = client.post(
        "/api/v1/compare",
        json={"package_names": ["fastapi", "requests"]},
    )
    assert comp_resp.status_code == 200
    data = comp_resp.json()
    assert len(data["packages"]) == 2
    assert "Download volume leader" in data["summary"]
    assert all(package["last_release_age_days"] == 0 for package in data["packages"])


def test_report_generation():
    pkgs = client.get("/api/v1/packages").json()
    assert len(pkgs) > 0
    pkg_id = pkgs[0]["id"]

    # Markdown format
    md_resp = client.post("/api/v1/reports/generate", json={"package_id": pkg_id, "format": "markdown"})
    assert md_resp.status_code == 200
    rep_id = md_resp.json()["id"]

    get_rep = client.get(f"/api/v1/reports/{rep_id}")
    assert get_rep.status_code == 200
    assert "# LibScope Intelligence Report" in get_rep.text


def test_package_history_is_bounded_and_reports_snapshot_count():
    client.post("/api/v1/demo/seed")
    package_id = client.get("/api/v1/packages").json()[0]["id"]

    response = client.get(f"/api/v1/packages/{package_id}/history?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert data["returned_snapshots"] <= 1
    assert data["total_snapshots_recorded"] >= data["returned_snapshots"]
    assert isinstance(data["historical_chart_points"], list)


def test_package_history_rejects_invalid_limits():
    response = client.get("/api/v1/packages/1/history?limit=501")
    assert response.status_code == 422


def test_package_analytics_is_paginated():
    client.post("/api/v1/demo/seed")
    package_id = client.get("/api/v1/packages").json()[0]["id"]

    response = client.get(f"/api/v1/packages/{package_id}/analytics?limit=1&offset=0")

    assert response.status_code == 200
    assert len(response.json()) <= 1
    assert client.get(f"/api/v1/packages/{package_id}/analytics?limit=501").status_code == 422


def test_score_history_is_bounded_and_chronological():
    client.post("/api/v1/demo/seed")
    package_id = client.get("/api/v1/packages").json()[0]["id"]

    response = client.get(f"/api/v1/packages/{package_id}/score-history?limit=1")

    assert response.status_code == 200
    points = response.json()
    assert len(points) <= 1
    assert all(set(point) == {"calculated_at", "overall_score", "confidence_level", "version"} for point in points)
    assert client.get(f"/api/v1/packages/{package_id}/score-history?limit=201").status_code == 422
    assert client.get("/api/v1/packages/999999/score-history").status_code == 404


def test_adoption_status_endpoint_does_not_infer_a_clean_search():
    client.post("/api/v1/demo/seed")
    package_id = client.get("/api/v1/packages").json()[0]["id"]

    response = client.get(f"/api/v1/packages/{package_id}/adoption/status")

    assert response.status_code == 200
    assert response.json()["status"] == "not_checked"
