"""
Integration tests for FastAPI REST API endpoints.
"""
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

