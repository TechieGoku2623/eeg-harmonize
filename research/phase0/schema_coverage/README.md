# schema_coverage

## What is measured

Which canonical fields exist in TUH EEG (TUEG/TUSZ), CHB-MIT, Sleep-EDF Expanded,
OpenNeuro BIDS-EEG, and TUH Artifact (TUAR), as a presence matrix.

## Why it decides something

A field that is `never` or `rare` in two or more corpora cannot be required in
the canonical schema. The matrix decides required vs optional.

## How to run

```bash
uv run python research/phase0/schema_coverage/run.py
```

Presence is coded from published format specifications and papers, not from a
scan of the full corpora. TUH requires a data-use agreement; the full-corpus
scan is the measurement that would replace this inventory after access.
