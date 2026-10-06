from __future__ import annotations

from pathlib import Path

import numpy as np

from eeg_harmonize.edf import EdfRecording, EdfSignal, read_edf, write_edf
from eeg_harmonize.schema import AnnotationInterval


def test_roundtrip(tmp_path: Path) -> None:
    samples = np.linspace(-20.0, 20.0, 256, dtype=np.float64)
    rec = EdfRecording(
        sfreq=256.0,
        signals=[EdfSignal(name="C3", samples=samples, unit="uV")],
        annotations=[AnnotationInterval(onset_sec=0.25, duration_sec=0.1, label="seizure")],
        edf_plus=True,
    )
    path = tmp_path / "one.edf"
    write_edf(path, rec)
    back = read_edf(path)
    assert back.signals[0].name == "C3"
    assert back.signals[0].unit == "uV"
    assert abs(back.sfreq - 256.0) < 1e-6
    assert back.annotations[0].label == "seizure"
    np.testing.assert_allclose(back.signals[0].samples, samples, atol=0.05)
