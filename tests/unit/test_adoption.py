"""
Unit tests for Adoption Discovery and Evidence Classification.
"""
from libscope.analyzers.adoption import (
    CLASS_CONFIRMED_DEPENDENCY,
    CLASS_CONFIRMED_USAGE,
    CLASS_MENTION_ONLY,
    CLASS_UNVERIFIED,
    AdoptionAnalyzer,
)


def test_classify_evidence_dependency_manifests():
    analyzer = AdoptionAnalyzer()

    # requirements.txt
    cls, conf = analyzer.classify_evidence("requirements.txt", 'fastapi>=0.100.0\nuvicorn\n', "fastapi")
    assert cls == CLASS_CONFIRMED_DEPENDENCY
    assert conf >= 0.85

    # pyproject.toml
    cls, conf = analyzer.classify_evidence(
        "pyproject.toml",
        '[project]\ndependencies = ["fastapi>=0.100.0"]',
        "fastapi",
    )
    assert cls == CLASS_CONFIRMED_DEPENDENCY
    assert conf == 0.99


def test_manifest_filename_or_similar_name_is_not_dependency_evidence():
    analyzer = AdoptionAnalyzer()

    cls, conf = analyzer.classify_evidence("requirements.txt", "my-fastapi-wrapper>=1.0", "fastapi")
    assert cls == CLASS_UNVERIFIED
    assert conf == 0.0

    cls, conf = analyzer.classify_evidence("pyproject.toml", "not valid toml = [", "fastapi")
    assert cls == CLASS_UNVERIFIED
    assert conf == 0.0


def test_dependency_names_are_normalized_and_unsupported_manifests_are_unverified():
    analyzer = AdoptionAnalyzer()

    cls, _ = analyzer.classify_evidence("requirements.txt", "FastAPI>=0.100", "fastapi")
    assert cls == CLASS_CONFIRMED_DEPENDENCY

    cls, conf = analyzer.classify_evidence("setup.py", "install_requires=['fastapi']", "fastapi")
    assert cls == CLASS_UNVERIFIED
    assert conf == 0.0


def test_classify_evidence_source_code_usage():
    analyzer = AdoptionAnalyzer()

    cls, conf = analyzer.classify_evidence("app/routes.py", 'from fastapi import FastAPI, Depends\n', "fastapi")
    assert cls == CLASS_CONFIRMED_USAGE
    assert conf >= 0.85

    cls, conf = analyzer.classify_evidence("main.py", 'import httpx\n', "httpx")
    assert cls == CLASS_CONFIRMED_USAGE


def test_classify_evidence_mention_only():
    analyzer = AdoptionAnalyzer()

    cls, conf = analyzer.classify_evidence("README.md", 'Special thanks to fastapi for inspiring our design.', "fastapi")
    assert cls == CLASS_MENTION_ONLY
    assert conf <= 0.40

    cls, conf = analyzer.classify_evidence("docs/index.rst", 'See fastapi documentation.', "fastapi")
    assert cls == CLASS_MENTION_ONLY


def test_process_raw_findings_filters_self_repo_and_deduplicates():
    analyzer = AdoptionAnalyzer()

    raw_items = [
        # Self-reference (MUST BE FILTERED)
        {
            "repo_full_name": "tiangolo/fastapi",
            "repo_url": "https://github.com/tiangolo/fastapi",
            "file_path": "pyproject.toml",
            "raw_match": 'name = "fastapi"',
            "stars": 75000,
        },
        # Legitimate external dependency
        {
            "repo_full_name": "huggingface/transformers",
            "repo_url": "https://github.com/huggingface/transformers",
            "file_path": "pyproject.toml",
            "raw_match": '[project]\ndependencies = ["fastapi"]',
            "stars": 130000,
        },
        # Duplicate of above
        {
            "repo_full_name": "huggingface/transformers",
            "repo_url": "https://github.com/huggingface/transformers",
            "file_path": "pyproject.toml",
            "raw_match": '[project]\ndependencies = ["fastapi"]',
            "stars": 130000,
        },
        # Second external usage
        {
            "repo_full_name": "langchain-ai/langchain",
            "repo_url": "https://github.com/langchain-ai/langchain",
            "file_path": "libs/community/pyproject.toml",
            "raw_match": '[project]\ndependencies = ["fastapi"]',
            "stars": 95000,
        },
    ]

    res = analyzer.process_raw_findings("fastapi", target_repo_full_name="tiangolo/fastapi", raw_items=raw_items)

    assert res.total_findings == 2
    assert res.confirmed_dependencies_count == 2
    # Ensure tiangolo/fastapi was NOT counted
    for item in res.findings:
        assert item.source_repo_full_name != "tiangolo/fastapi"

