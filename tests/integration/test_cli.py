"""
Integration tests for Typer CLI commands.
"""
from typer.testing import CliRunner
from libscope.cli.main import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Open-Source Software Intelligence Platform" in result.output


def test_cli_demo_and_compare():
    seed_res = runner.invoke(app, ["demo"])
    assert seed_res.exit_code == 0
    assert "Seeded" in seed_res.output

    comp_res = runner.invoke(app, ["compare", "fastapi", "requests"])
    assert comp_res.exit_code == 0
    assert "fastapi" in comp_res.output
    assert "requests" in comp_res.output


def test_cli_providers():
    res = runner.invoke(app, ["providers"])
    assert res.exit_code == 0
    assert "pypi" in res.output
    assert "github" in res.output


def test_cli_config():
    res = runner.invoke(app, ["config"])
    assert res.exit_code == 0
    assert "Database URL" in res.output

