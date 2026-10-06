"""Write the five designed EDF clips. Seeded. Re-run from `make research`."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eeg_harmonize.edf import EdfRecording, EdfSignal, write_edf
from eeg_harmonize.schema import AnnotationInterval

HERE = Path(__file__).resolve().parent
SEED = 0
SFREQ = 256.0
DURATION = 30.0
CANONICAL = ["Fp1", "Fp2", "C3", "C4", "O1", "O2", "T7", "T8"]


def _eeg(n: int, rng: np.random.Generator, hz: float = 10.0) -> np.ndarray:
    t = np.arange(n) / SFREQ
    return (20.0 * np.sin(2 * np.pi * hz * t) + 3.0 * rng.normal(size=n)).astype(np.float64)


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = int(SFREQ * DURATION)

    clean_signals = [
        EdfSignal(name=name, samples=_eeg(n, rng, hz=10.0 + i), unit="uV")
        for i, name in enumerate(CANONICAL)
    ]
    write_edf(
        HERE / "clean.edf",
        EdfRecording(
            sfreq=SFREQ,
            signals=clean_signals,
            annotations=[
                AnnotationInterval(onset_sec=5.0, duration_sec=2.0, label="seizure"),
            ],
            edf_plus=True,
        ),
    )

    bad = [EdfSignal(name=name, samples=_eeg(n, rng, hz=10.0), unit="V") for name in CANONICAL]
    write_edf(HERE / "bad-units.edf", EdfRecording(sfreq=SFREQ, signals=bad))

    odd_names = [*CANONICAL, "CB1", "CB2"]
    odd = [EdfSignal(name=name, samples=_eeg(n, rng), unit="uV") for name in odd_names]
    write_edf(
        HERE / "odd-channels.edf",
        EdfRecording(
            sfreq=SFREQ,
            signals=odd,
            annotations=[
                AnnotationInterval(onset_sec=8.0, duration_sec=1.0, label="seizure"),
                AnnotationInterval(onset_sec=12.0, duration_sec=0.5, label="sleepy-wiggle"),
            ],
            edf_plus=True,
        ),
    )

    write_edf(
        HERE / "unmapped-annots.edf",
        EdfRecording(
            sfreq=SFREQ,
            signals=[EdfSignal(name=nme, samples=_eeg(n, rng), unit="uV") for nme in CANONICAL],
            annotations=[
                AnnotationInterval(onset_sec=3.0, duration_sec=1.0, label="tech-note"),
                AnnotationInterval(onset_sec=6.0, duration_sec=1.0, label="sleepy-wiggle"),
            ],
            edf_plus=True,
        ),
    )

    write_edf(
        HERE / "offset-annots.edf",
        EdfRecording(
            sfreq=SFREQ,
            signals=[EdfSignal(name=nme, samples=_eeg(n, rng), unit="uV") for nme in CANONICAL],
            annotations=[
                AnnotationInterval(onset_sec=10.0 + 1.0 / SFREQ, duration_sec=1.0, label="seizure"),
            ],
            edf_plus=True,
        ),
    )

    manifest = {
        "seed": SEED,
        "sfreq": SFREQ,
        "duration_sec": DURATION,
        "clips": [
            {
                "file": "clean.edf",
                "path_exercised": "standard 10-20 conversion",
                "expected_behavior": "inspect + convert succeed; no channel drops",
            },
            {
                "file": "bad-units.edf",
                "path_exercised": "µV data, header claims V",
                "expected_behavior": "unit_scale validator rejects; non-zero exit",
            },
            {
                "file": "odd-channels.edf",
                "path_exercised": "CB1/CB2 have no 10-20 equivalent",
                "expected_behavior": "drop and log; never rename",
            },
            {
                "file": "unmapped-annots.edf",
                "path_exercised": "terms outside the controlled set",
                "expected_behavior": "unmappable bucket, reported",
            },
            {
                "file": "offset-annots.edf",
                "path_exercised": "off-by-one sample annotation",
                "expected_behavior": "alignment test fails on 1/256 s offset",
            },
        ],
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote 5 EDF clips under {HERE}")


if __name__ == "__main__":
    main()
