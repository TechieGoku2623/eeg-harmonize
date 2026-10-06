"""Silent-failure checks. Fail loud; do not coerce units or rename channels."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel

from eeg_harmonize.edf import EdfRecording
from eeg_harmonize.montage import drop_noncanonical


class ValidationError(Exception):
    def __init__(self, check: str, message: str) -> None:
        self.check = check
        super().__init__(f"{check}: {message}")


class UnitCheck(BaseModel):
    unit: str
    peak_abs: float
    passed: bool
    rationale: str


class ChannelReport(BaseModel):
    kept: list[str]
    dropped: list[str]
    kept_fraction: float


def check_units(rec: EdfRecording) -> UnitCheck:
    """Reject header unit V when the amplitude is a µV-scale recording.

    Scalp EEG in volts is on the order of 1e-5 to 1e-4. A peak of 10 or more
    with unit V is the classic 1e6 scale error (µV stored, V claimed).
    """

    peak = max(float(np.max(np.abs(signal.samples))) for signal in rec.signals)
    unit = rec.signals[0].unit.strip()
    if unit.upper() in {"V", "VOLT", "VOLTS"} and peak > 0.01:
        raise ValidationError(
            "unit_scale",
            f"header unit={unit} but peak |amplitude|={peak:.4g}; "
            "expected |V| << 0.01 for scalp EEG. Measured 1e6-scale mismatch.",
        )
    return UnitCheck(
        unit=unit,
        peak_abs=peak,
        passed=True,
        rationale="unit and amplitude are consistent with scalp EEG",
    )


def report_channels(rec: EdfRecording) -> ChannelReport:
    names = [s.name for s in rec.signals]
    kept, dropped = drop_noncanonical(names)
    return ChannelReport(
        kept=kept,
        dropped=dropped,
        kept_fraction=(len(kept) / len(names)) if names else 0.0,
    )
