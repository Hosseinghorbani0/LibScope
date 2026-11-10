from libscope.reporting.html_rep import generate_html_report
from libscope.reporting.markdown import generate_markdown_report


def test_html_report_escapes_data_and_rejects_unsafe_links():
    report = generate_html_report(
        {
            "package": {"name": '<script>alert("x")</script>'},
            "adoption": {
                "findings": [
                    {
                        "source_repo_full_name": "<img src=x onerror=alert(1)>",
                        "source_repo_url": "javascript:alert(1)",
                        "file_path": "<script>alert(2)</script>",
                        "evidence_type": "Confirmed dependency declaration",
                        "confidence_score": 0.9,
                    }
                ]
            },
            "health": {
                "overall_health_rating": "warning",
                "findings": [
                    {
                        "status": "failed",
                        "check_name": "readme",
                        "message": "<svg onload=alert(3)>",
                    }
                ],
            },
            "security": {
                "status": "rate_limited",
                "vulnerabilities_count": None,
                "caveats": ["<script>alert(4)</script>"],
            },
        }
    )

    assert "<script>" not in report
    assert "&lt;script&gt;" in report
    assert "javascript:alert" not in report
    assert "No clean result is available for this security check." in report
    assert "Known vulnerabilities: N/A" in report
    assert "Project Health: warning" in report


def test_html_report_allows_only_safe_https_links():
    report = generate_html_report(
        {
            "adoption": {
                "findings": [
                    {
                        "source_repo_full_name": "owner/repo",
                        "source_repo_url": "https://github.com/owner/repo?a=1&b=2",
                        "confidence_score": 0.8,
                    }
                ]
            },
            "security": {
                "status": "checked",
                "vulnerabilities_count": 1,
                "vulnerabilities": [
                    {
                        "identifier": "GHSA-1234",
                        "severity": "HIGH",
                        "title": "Example advisory",
                        "reference_url": "https://osv.dev/vulnerability/GHSA-1234",
                    }
                ],
            },
        }
    )

    assert 'href="https://github.com/owner/repo?a=1&amp;b=2"' in report
    assert 'href="https://osv.dev/vulnerability/GHSA-1234"' in report
    assert 'rel="noopener noreferrer"' in report
    assert "No known vulnerabilities were returned." not in report


def test_markdown_report_does_not_present_unchecked_security_as_clean():
    report = generate_markdown_report(
        {
            "security": {
                "status": "unsupported",
                "vulnerabilities_count": None,
                "critical_count": None,
                "high_count": None,
                "medium_count": None,
                "low_count": None,
            },
            "health": {"overall_health_rating": "insufficient_data"},
        }
    )

    assert "**Check Status:** `unsupported`" in report
    assert "**Known Vulnerabilities (OSV):** `Not verified`" in report
    assert "No clean result is available" in report
    assert "**Overall Rating:** `INSUFFICIENT_DATA`" in report

