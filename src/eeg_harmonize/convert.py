"""Convert an EDF into a canonical record with an append-only provenance chain."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
from pydantic import BaseModel, Field

from eeg_harmonize.annotations import MappedTerm, map_term
from eeg_harmonize.edf import EdfRecording, EdfSignal, read_edf
from eeg_harmonize.inspect import field_inventory, infer_montage, infer_reference
from eeg_harmonize.montage import drop_noncanonical, is_canonical
from eeg_harmonize.resample import DEFAULT_RESAMPLER, resample_signal
from eeg_harmonize.schema import HarmonizedProvenance
from eeg_harmonize.validate import check_units, report_channels


class MappedAnnotation(BaseModel):
    onset_sec: float
    duration_sec: float
    raw: str
    controlled: str | None
    unmappable: bool


class ConvertReport(BaseModel):
    source_path: str
    sfreq: float
    n_channels_in: int
    n_channels_out: int
    kept_channels: list[str]
    dropped_channels: list[str]
    annotations: list[MappedAnnotation] = Field(default_factory=list)
    unmappable: list[str] = Field(default_factory=list)
    provenance: HarmonizedProvenance
    present_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    output_path: str | None = None
    resampler: str = DEFAULT_RESAMPLER


def _map_annotations(rec: EdfRecording) -> list[MappedAnnotation]:
    out: list[MappedAnnotation] = []
    for item in rec.annotations:
        mapped: MappedTerm = map_term(item.label)
        out.append(
            MappedAnnotation(
                onset_sec=item.onset_sec,
                duration_sec=item.duration_sec,
                raw=mapped.raw,
                controlled=mapped.controlled,
                unmappable=mapped.unmappable,
            )
        )
    return out


def convert_recording(
    path: Path,
    *,
    out: Path | None = None,
    target_sfreq: float | None = None,
) -> ConvertReport:
    """Apply unit check, drop non-10-20 channels, map annotations, optional resample."""

    operations: list[str] = [f"read_edf:{path}"]
    rec = read_edf(path)
    n_in = len(rec.signals)
    check_units(rec)
    operations.append("check_units:pass")

    names = [s.name for s in rec.signals]
    kept_names, dropped = drop_noncanonical(names)
    if dropped:
        operations.append(f"drop_noncanonical:{','.join(dropped)}")
    kept_signals = [s for s in rec.signals if is_canonical(s.name)]
    rec = rec.model_copy(update={"signals": kept_signals})

    mapped = _map_annotations(rec)
    unmappable = sorted({item.raw for item in mapped if item.unmappable})
    if mapped:
        mapped_summary = ",".join(
            f"{item.raw}->{'unmappable' if item.unmappable else item.controlled}" for item in mapped
        )
        operations.append(f"map_annotations:{mapped_summary}")

    sfreq = rec.sfreq
    if target_sfreq is not None and target_sfreq != rec.sfreq:
        resampled: list[EdfSignal] = []
        for signal in rec.signals:
            samples = resample_signal(signal.samples, rec.sfreq, target_sfreq)
            resampled.append(signal.model_copy(update={"samples": samples}))
        rec = rec.model_copy(update={"signals": resampled, "sfreq": target_sfreq})
        operations.append(f"{DEFAULT_RESAMPLER}:{sfreq}->{target_sfreq}")
        sfreq = target_sfreq
    else:
        operations.append(f"{DEFAULT_RESAMPLER}:identity({rec.sfreq} Hz)")

    provenance = HarmonizedProvenance(
        source_path=str(path),
        source_format="edf",
        operations=operations,
    )
    fields = field_inventory(rec, provenance_present=True)
    output_path: str | None = None
    if out is not None:
        output_path = str(_write_output(out, rec, mapped, provenance, dropped))
        operations.append(f"write:{output_path}")
        provenance = HarmonizedProvenance(
            source_path=str(path),
            source_format="edf",
            operations=operations,
        )

    return ConvertReport(
        source_path=str(path),
        sfreq=sfreq,
        n_channels_in=n_in,
        n_channels_out=len(rec.signals),
        kept_channels=kept_names,
        dropped_channels=dropped,
        annotations=mapped,
        unmappable=unmappable,
        provenance=provenance,
        present_fields=[f.name for f in fields if f.present],
        missing_fields=[f.name for f in fields if not f.present],
        output_path=output_path,
        resampler=DEFAULT_RESAMPLER,
    )


def _write_output(
    out: Path,
    rec: EdfRecording,
    mapped: list[MappedAnnotation],
    provenance: HarmonizedProvenance,
    dropped: list[str],
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "sfreq": rec.sfreq,
        "n_samples": rec.n_samples if rec.signals else 0,
        "channel_names": [s.name for s in rec.signals],
        "channel_units": [s.unit for s in rec.signals],
        "dropped_channels": dropped,
        "annotations": [item.model_dump() for item in mapped],
        "provenance": provenance.model_dump(),
        "montage_system": infer_montage(rec),
        "reference_scheme": infer_reference(rec),
        "disclaimer": (
            "Research infrastructure. Harmonized EEG is not a diagnostic and is not "
            "clinical advice. Sample clips in this repository are designed, not patient records."
        ),
    }
    if out.suffix != ".parquet":
        out.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        return out

    sidecar = out.with_suffix(".meta.json")
    sidecar.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE rec (
            source VARCHAR,
            sfreq DOUBLE,
            n_channels INTEGER,
            n_samples INTEGER,
            dropped VARCHAR,
            resampler VARCHAR
        )
        """
    )
    con.execute(
        "INSERT INTO rec VALUES (?, ?, ?, ?, ?, ?)",
        [
            provenance.source_path,
            rec.sfreq,
            len(rec.signals),
            rec.n_samples if rec.signals else 0,
            ",".join(dropped),
            DEFAULT_RESAMPLER,
        ],
    )
    con.execute(f"COPY rec TO '{out}' (FORMAT PARQUET)")
    return out


def validate_recording(path: Path) -> ConvertReport:
    """Validate units and channel policy. Same hard fail as convert."""

    rec = read_edf(path)
    check_units(rec)
    report_channels(rec)
    return convert_recording(path)
