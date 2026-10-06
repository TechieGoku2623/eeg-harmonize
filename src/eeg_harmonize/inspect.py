"""Inspect an EDF: montage, rate, reference, vocab, canonical field coverage."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from eeg_harmonize.annotations import map_term
from eeg_harmonize.edf import EdfRecording, read_edf
from eeg_harmonize.montage import is_canonical, normalize_label
from eeg_harmonize.schema import CANONICAL_FIELDS
from eeg_harmonize.validate import report_channels


class FieldPresence(BaseModel):
    name: str
    present: bool
    required_candidate: bool
    note: str


class InspectReport(BaseModel):
    path: str
    sfreq: float
    n_channels: int
    duration_sec: float
    montage_system: str
    reference_scheme: str
    channel_names: list[str]
    channel_units: list[str]
    annotation_vocabulary: list[str]
    annotation_mapped: list[str]
    annotation_unmappable: list[str]
    fields: list[FieldPresence] = Field(default_factory=list)
    present_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    dropped_noncanonical: list[str] = Field(default_factory=list)


def infer_reference(rec: EdfRecording) -> str:
    names = [normalize_label(s.name) for s in rec.signals]
    for signal, name in zip(rec.signals, names, strict=True):
        if name.endswith("-REF") or "-REF" in signal.name.upper():
            return "common-ref"
    if any("-" in normalize_label(s.name) for s in rec.signals):
        return "bipolar"
    if "A1" in names and "A2" in names:
        return "linked-ear-available"
    return "unknown"


def infer_montage(rec: EdfRecording) -> str:
    names = [s.name for s in rec.signals]
    if names and all(is_canonical(n) for n in names):
        return "10-20"
    return "mixed"


def field_inventory(rec: EdfRecording, provenance_present: bool) -> list[FieldPresence]:
    patient = rec.patient.strip()
    has_subject = bool(patient) and patient != "X X X X"
    vocab = sorted({a.label for a in rec.annotations})
    values: dict[str, tuple[bool, str]] = {
        "signal_array": (True, "samples present"),
        "channel_names": (True, ",".join(s.name for s in rec.signals)),
        "channel_units": (True, ",".join(s.unit for s in rec.signals)),
        "channel_types": (False, "EDF header has no type column"),
        "sampling_rate_hz": (True, str(rec.sfreq)),
        "n_channels": (True, str(len(rec.signals))),
        "duration_sec": (True, f"{rec.duration_sec:.4g}"),
        "montage_system": (True, infer_montage(rec)),
        "reference_scheme": (True, infer_reference(rec)),
        "annotation_intervals": (True, f"n={len(rec.annotations)}"),
        "annotation_vocabulary": (True, ",".join(vocab) or "(empty)"),
        "provenance": (provenance_present, "append-only operation list after convert"),
        "subject_id": (has_subject, patient),
        "subject_age": (False, "not in designed EDF patient field"),
        "subject_sex": (False, "not in designed EDF patient field"),
        "channel_positions_3d": (False, "no electrodes.tsv"),
        "power_line_frequency": (False, "not in header"),
        "recording_datetime": (True, f"{rec.start_date} {rec.start_time}"),
        "institution": (False, "not in header"),
        "task": (False, "not a BIDS file"),
        "filter_settings": (True, rec.signals[0].prefilter if rec.signals else ""),
    }
    out: list[FieldPresence] = []
    for field in CANONICAL_FIELDS:
        present, note = values[field.name]
        out.append(
            FieldPresence(
                name=field.name,
                present=present,
                required_candidate=field.required_candidate,
                note=note,
            )
        )
    return out


def inspect_recording(path: Path) -> InspectReport:
    rec = read_edf(path)
    vocab = sorted({item.label for item in rec.annotations})
    mapped = [map_term(label) for label in vocab]
    channels = report_channels(rec)
    fields = field_inventory(rec, provenance_present=False)
    return InspectReport(
        path=str(path),
        sfreq=rec.sfreq,
        n_channels=len(rec.signals),
        duration_sec=rec.duration_sec,
        montage_system=infer_montage(rec),
        reference_scheme=infer_reference(rec),
        channel_names=[s.name for s in rec.signals],
        channel_units=[s.unit for s in rec.signals],
        annotation_vocabulary=vocab,
        annotation_mapped=[m.controlled or "" for m in mapped if not m.unmappable],
        annotation_unmappable=[m.raw for m in mapped if m.unmappable],
        fields=fields,
        present_fields=[f.name for f in fields if f.present],
        missing_fields=[f.name for f in fields if not f.present],
        dropped_noncanonical=channels.dropped,
    )
