"""Minimal EDF / EDF+ writer and reader used by sample clips and harnesses.

This is not EDFlib. It implements the 256-byte header plus optional EDF+C
Annotations so Phase 0 can commit designed clips without a native dependency.
It does not read EDF+ discontinued files, BDF 24-bit files, or overlapping
annotation channels beyond one TAL stream.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from eeg_harmonize.schema import AnnotationInterval


class EdfSignal(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str
    samples: NDArray[np.float64]
    unit: str = "uV"
    transducer: str = "AgAgCl"
    prefilter: str = "HP:0.1Hz LP:70Hz"


class EdfRecording(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    patient: str = "X X X X"
    recording: str = "Startdate 01-JAN-2020 X X X"
    start_date: str = "01.01.20"
    start_time: str = "00.00.00"
    sfreq: float
    signals: list[EdfSignal]
    annotations: list[AnnotationInterval] = Field(default_factory=list)
    edf_plus: bool = False

    @property
    def n_samples(self) -> int:
        return int(self.signals[0].samples.shape[0])

    @property
    def duration_sec(self) -> float:
        return self.n_samples / self.sfreq


def _pad(text: str, width: int) -> bytes:
    raw = text.encode("ascii", errors="replace")[:width]
    return raw + b" " * (width - len(raw))


def _fmt_num(value: float, width: int) -> bytes:
    text = f"{value:.8g}"
    return _pad(text, width)


def _scale_to_digital(
    samples: NDArray[np.float64], phys_min: float, phys_max: float
) -> NDArray[np.int16]:
    dig_min, dig_max = -32768.0, 32767.0
    if phys_max == phys_min:
        phys_max = phys_min + 1.0
    scaled = (samples - phys_min) / (phys_max - phys_min) * (dig_max - dig_min) + dig_min
    return np.clip(np.rint(scaled), dig_min, dig_max).astype(np.int16)


def _from_digital(
    digital: NDArray[np.int16], phys_min: float, phys_max: float, dig_min: float, dig_max: float
) -> NDArray[np.float64]:
    if dig_max == dig_min:
        return np.zeros(digital.shape[0], dtype=np.float64)
    scale = (phys_max - phys_min) / (dig_max - dig_min)
    return (digital.astype(np.float64) - dig_min) * scale + phys_min


def _tal_bytes(annotations: list[AnnotationInterval], n_samples: int) -> bytes:
    parts = [b"+0\x14\x14\x00"]
    for item in annotations:
        token = f"+{item.onset_sec:.4f}\x15{item.duration_sec:.4f}\x14{item.label}\x14\x00"
        parts.append(token.encode("ascii", errors="replace"))
    blob = b"".join(parts)
    width = n_samples * 2
    if len(blob) > width:
        raise ValueError(f"TAL ({len(blob)} bytes) exceeds record width {width}")
    return blob + b"\x00" * (width - len(blob))


def write_edf(path: Path, rec: EdfRecording) -> None:
    """Write a single-record EDF or EDF+ file."""

    n_eeg = len(rec.signals)
    use_plus = rec.edf_plus or bool(rec.annotations)
    n_signals = n_eeg + (1 if use_plus else 0)
    n_samples = rec.n_samples
    header_bytes = 256 + 256 * n_signals
    reserved = "EDF+C" if use_plus else ""

    header = bytearray()
    header += _pad("0", 8)
    header += _pad(rec.patient, 80)
    header += _pad(rec.recording, 80)
    header += _pad(rec.start_date, 8)
    header += _pad(rec.start_time, 8)
    header += _pad(str(header_bytes), 8)
    header += _pad(reserved, 44)
    header += _pad("1", 8)
    header += _fmt_num(rec.duration_sec, 8)
    header += _pad(str(n_signals), 4)

    names = [s.name for s in rec.signals]
    transducers = [s.transducer for s in rec.signals]
    units = [s.unit for s in rec.signals]
    phys_mins: list[float] = []
    phys_maxs: list[float] = []
    for signal in rec.signals:
        peak = float(max(np.max(np.abs(signal.samples)), 1.0))
        phys_mins.append(-peak)
        phys_maxs.append(peak)
    prefilters = [s.prefilter for s in rec.signals]
    nsamp = [n_samples] * n_eeg

    if use_plus:
        names.append("EDF Annotations")
        transducers.append("")
        units.append("")
        phys_mins.append(-1.0)
        phys_maxs.append(1.0)
        prefilters.append("")
        nsamp.append(n_samples)

    for name in names:
        header += _pad(name, 16)
    for transducer in transducers:
        header += _pad(transducer, 80)
    for unit in units:
        header += _pad(unit, 8)
    for value in phys_mins:
        header += _fmt_num(value, 8)
    for value in phys_maxs:
        header += _fmt_num(value, 8)
    for _ in names:
        header += _pad("-32768", 8)
    for _ in names:
        header += _pad("32767", 8)
    for prefilter in prefilters:
        header += _pad(prefilter, 80)
    for count in nsamp:
        header += _pad(str(count), 8)
    for _ in names:
        header += _pad("", 32)

    if len(header) != header_bytes:
        raise RuntimeError(f"header length {len(header)} != {header_bytes}")

    records = bytearray()
    for signal, pmin, pmax in zip(rec.signals, phys_mins[:n_eeg], phys_maxs[:n_eeg], strict=True):
        records += _scale_to_digital(signal.samples, pmin, pmax).tobytes()
    if use_plus:
        records += _tal_bytes(rec.annotations, n_samples)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + bytes(records))


def _ascii_field(buf: bytes) -> str:
    return buf.decode("ascii", errors="replace").strip()


def _header_fields(header: bytes, offset: int, width: int, n_signals: int) -> list[str]:
    return [
        _ascii_field(header[offset + i * width : offset + (i + 1) * width])
        for i in range(n_signals)
    ]


def read_edf(path: Path) -> EdfRecording:
    raw = path.read_bytes()
    n_header = int(_ascii_field(raw[184:192]))
    n_signals = int(_ascii_field(raw[252:256]))
    sfreq_duration = float(_ascii_field(raw[244:252]))
    header = raw[:n_header]
    offset = 256
    names = _header_fields(header, offset, 16, n_signals)
    offset = 256 + 16 * n_signals
    offset += 80 * n_signals  # transducer
    units = _header_fields(header, offset, 8, n_signals)
    offset += 8 * n_signals
    phys_mins = [float(x) for x in _header_fields(header, offset, 8, n_signals)]
    offset += 8 * n_signals
    phys_maxs = [float(x) for x in _header_fields(header, offset, 8, n_signals)]
    offset += 8 * n_signals
    dig_mins = [float(x) for x in _header_fields(header, offset, 8, n_signals)]
    offset += 8 * n_signals
    dig_maxs = [float(x) for x in _header_fields(header, offset, 8, n_signals)]
    offset += 8 * n_signals
    offset += 80 * n_signals  # prefilter
    nsamp = [int(x) for x in _header_fields(header, offset, 8, n_signals)]
    body = raw[n_header:]
    cursor = 0
    signals: list[EdfSignal] = []
    annotations: list[AnnotationInterval] = []
    eeg_nsamp = next(n for name, n in zip(names, nsamp, strict=True) if name != "EDF Annotations")
    sfreq = eeg_nsamp / sfreq_duration
    for name, unit, pmin, pmax, dmin, dmax, count in zip(
        names, units, phys_mins, phys_maxs, dig_mins, dig_maxs, nsamp, strict=True
    ):
        chunk = body[cursor : cursor + count * 2]
        cursor += count * 2
        digital = np.frombuffer(chunk, dtype=np.int16)
        if name == "EDF Annotations":
            annotations = _parse_tal(chunk)
            continue
        samples = _from_digital(digital, pmin, pmax, dmin, dmax)
        signals.append(EdfSignal(name=name, samples=samples, unit=unit or "uV"))
    reserved = _ascii_field(raw[192:236])
    return EdfRecording(
        patient=_ascii_field(raw[8:88]),
        recording=_ascii_field(raw[88:168]),
        start_date=_ascii_field(raw[168:176]),
        start_time=_ascii_field(raw[176:184]),
        sfreq=sfreq,
        signals=signals,
        annotations=annotations,
        edf_plus=reserved.startswith("EDF+"),
    )


def _parse_tal(blob: bytes) -> list[AnnotationInterval]:
    text = blob.split(b"\x00")
    out: list[AnnotationInterval] = []
    for part in text:
        if not part or part == b"+0\x14\x14":
            continue
        if b"\x14" not in part:
            continue
        onset_block, *rest = part.split(b"\x14")
        if b"\x15" in onset_block:
            onset_s, dur_s = onset_block.split(b"\x15", 1)
            duration = float(dur_s.decode("ascii"))
        else:
            onset_s = onset_block
            duration = 0.0
        onset = float(onset_s.decode("ascii"))
        labels = [piece.decode("ascii", errors="replace") for piece in rest if piece]
        for label in labels:
            out.append(AnnotationInterval(onset_sec=onset, duration_sec=duration, label=label))
    return out
