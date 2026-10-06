from __future__ import annotations

from pathlib import Path

import pytest

from eeg_harmonize.convert import convert_recording, validate_recording
from eeg_harmonize.inspect import inspect_recording
from eeg_harmonize.resample import DEFAULT_RESAMPLER, resample_signal
from eeg_harmonize.validate import ValidationError

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample"


def test_inspect_clean_lists_canonical_fields() -> None:
    report = inspect_recording(SAMPLE / "clean.edf")
    assert report.sfreq == 256.0
    assert report.n_channels == 8
    assert report.montage_system == "10-20"
    assert "signal_array" in report.present_fields
    assert "channel_positions_3d" in report.missing_fields
    assert "seizure" in report.annotation_vocabulary


def test_convert_clean_no_drops(tmp_path: Path) -> None:
    out = tmp_path / "clean.json"
    report = convert_recording(SAMPLE / "clean.edf", out=out)
    assert report.dropped_channels == []
    assert report.n_channels_out == 8
    assert report.resampler == DEFAULT_RESAMPLER
    assert report.provenance.operations[0].startswith("read_edf")
    assert "check_units:pass" in report.provenance.operations
    assert out.is_file()


def test_convert_bad_units_fails() -> None:
    with pytest.raises(ValidationError, match="unit_scale"):
        convert_recording(SAMPLE / "bad-units.edf")


def test_convert_odd_channels_drops_and_unmappable() -> None:
    report = convert_recording(SAMPLE / "odd-channels.edf")
    assert "CB1" in report.dropped_channels
    assert "CB2" in report.dropped_channels
    assert "sleepy-wiggle" in report.unmappable


def test_validate_clean() -> None:
    report = validate_recording(SAMPLE / "clean.edf")
    assert report.n_channels_out == 8


def test_resample_identity() -> None:
    import numpy as np

    x = np.linspace(-1.0, 1.0, 256, dtype=np.float64)
    assert resample_signal(x, 256.0, 256.0).shape == x.shape
    down = resample_signal(x, 256.0, 128.0)
    assert down.shape[0] == 128
