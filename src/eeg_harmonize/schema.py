"""Canonical record fields. Required vs optional is a Phase 0 measurement."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Presence = Literal["always", "often", "rare", "never"]


class CanonicalField(BaseModel):
    name: str
    required_candidate: bool
    description: str


def _f(name: str, required: bool, description: str) -> CanonicalField:
    return CanonicalField(name=name, required_candidate=required, description=description)


CANONICAL_FIELDS: tuple[CanonicalField, ...] = (
    _f("signal_array", True, "Samples, channel-major"),
    _f("channel_names", True, "Label per channel"),
    _f("channel_units", True, "Physical unit string"),
    _f("channel_types", True, "eeg/eog/emg/ecg/misc"),
    _f("sampling_rate_hz", True, "Nominal sfreq"),
    _f("n_channels", True, "Count"),
    _f("duration_sec", True, "n_samples / sfreq"),
    _f("montage_system", True, "10-20, 10-10, bipolar, TCP, unknown"),
    _f("reference_scheme", True, "average, linked-ear, bipolar, unknown"),
    _f("annotation_intervals", True, "onset, duration, label"),
    _f("annotation_vocabulary", True, "Set of labels in the file"),
    _f("provenance", True, "Source URI + transform chain"),
    _f("subject_id", False, "De-identified subject key"),
    _f("subject_age", False, "Age if present in header"),
    _f("subject_sex", False, "Sex if present in header"),
    _f("channel_positions_3d", False, "xyz; BIDS electrodes.tsv"),
    _f("power_line_frequency", False, "50/60 if known"),
    _f("recording_datetime", False, "Header start time"),
    _f("institution", False, "If present"),
    _f("task", False, "BIDS TaskName"),
    _f("filter_settings", False, "Prefilter header / eeg.json"),
)


class FieldInventory(BaseModel):
    corpus: str
    source: str
    presence: dict[str, Presence]


class AnnotationInterval(BaseModel):
    onset_sec: float
    duration_sec: float
    label: str
    channel: str | None = None


class HarmonizedProvenance(BaseModel):
    source_path: str
    source_format: str
    operations: list[str] = Field(default_factory=list)
