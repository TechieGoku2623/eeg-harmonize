from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

from eeg_harmonize.annotations import map_term
from eeg_harmonize.config import get_settings
from eeg_harmonize.edf import read_edf
from eeg_harmonize.logging import configure_logging
from eeg_harmonize.montage import drop_noncanonical, is_canonical
from eeg_harmonize.validate import ValidationError, check_units, report_channels

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample"


@pytest.fixture(scope="session", autouse=True)
def built_samples() -> None:
    runpy.run_path(str(SAMPLE / "build.py"), run_name="__main__")


def test_clean_units_pass() -> None:
    check_units(read_edf(SAMPLE / "clean.edf"))


def test_bad_units_rejected() -> None:
    with pytest.raises(ValidationError, match="unit_scale"):
        check_units(read_edf(SAMPLE / "bad-units.edf"))


def test_odd_channels_dropped_not_renamed() -> None:
    report = report_channels(read_edf(SAMPLE / "odd-channels.edf"))
    assert "CB1" in report.dropped
    assert "CB2" in report.dropped
    assert all(is_canonical(name) for name in report.kept)


def test_unmapped_terms() -> None:
    rec = read_edf(SAMPLE / "unmapped-annots.edf")
    mapped = [map_term(item.label) for item in rec.annotations]
    assert any(item.unmappable for item in mapped)
    assert map_term("seizure").unmappable is False


def test_offset_annotation_is_one_sample_late() -> None:
    rec = read_edf(SAMPLE / "offset-annots.edf")
    onset = rec.annotations[0].onset_sec
    assert abs(onset - (10.0 + 1.0 / rec.sfreq)) < 1e-3


def test_canonical_drop_helper() -> None:
    kept, dropped = drop_noncanonical(["C3", "CB1", "EEG FP1-REF"])
    assert "C3" in kept
    assert "EEG FP1-REF" in kept
    assert dropped == ["CB1"]


def test_settings_and_logging() -> None:
    settings = get_settings()
    assert (settings.sample_dir / "README.md").is_file()
    configure_logging()


def test_manifest_names_five_paths() -> None:
    manifest = json.loads((SAMPLE / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["clips"]) == 5
