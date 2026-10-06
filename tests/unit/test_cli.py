from __future__ import annotations

from typer.testing import CliRunner

from eeg_harmonize.cli import app

runner = CliRunner()


def test_demo_plan() -> None:
    result = runner.invoke(app, ["demo-plan"])
    assert result.exit_code == 0, result.stdout
    assert "clean.edf" in result.stdout
    assert "bad-units.edf" in result.stdout
    assert "not a diagnostic" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "eeg-harmonize" in result.stdout
