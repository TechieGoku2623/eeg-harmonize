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


def test_inspect_and_convert_cli() -> None:
    from pathlib import Path

    sample = Path(__file__).resolve().parents[2] / "data" / "sample"
    inspected = runner.invoke(app, ["inspect", str(sample / "clean.edf")])
    assert inspected.exit_code == 0, inspected.stdout
    assert "256" in inspected.stdout
    assert "10-20" in inspected.stdout
    assert "not a diagnostic" in inspected.stdout
    converted = runner.invoke(app, ["convert", "--in", str(sample / "clean.edf")])
    assert converted.exit_code == 0, converted.stdout
    assert "provenance" in converted.stdout.lower()
    bad = runner.invoke(app, ["convert", "--in", str(sample / "bad-units.edf")])
    assert bad.exit_code != 0
    assert "unit_scale" in bad.stdout
    odd = runner.invoke(app, ["convert", "--in", str(sample / "odd-channels.edf"), "--report"])
    assert odd.exit_code == 0, odd.stdout
    assert "CB1" in odd.stdout
    assert "sleepy-wiggle" in odd.stdout
    valid = runner.invoke(app, ["validate", str(sample / "clean.edf")])
    assert valid.exit_code == 0
