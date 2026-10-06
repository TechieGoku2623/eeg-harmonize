"""10-20 canonical names. Unknown channels are dropped and logged, never renamed."""

from __future__ import annotations

CANONICAL_1020: frozenset[str] = frozenset(
    {
        "FP1",
        "FP2",
        "FPZ",
        "F7",
        "F3",
        "FZ",
        "F4",
        "F8",
        "T3",
        "T7",
        "C3",
        "CZ",
        "C4",
        "T4",
        "T8",
        "T5",
        "T9",
        "P3",
        "PZ",
        "P4",
        "T6",
        "T10",
        "O1",
        "OZ",
        "O2",
        "A1",
        "A2",
        "T1",
        "T2",
    }
)

# Bipolar CHB-MIT-style pairs are 10-20 positions joined by a hyphen.
ALIASES: dict[str, str] = {
    "T7": "T7",
    "T8": "T8",
    "P7": "T5",
    "P8": "T6",
}


def normalize_label(raw: str) -> str:
    """Strip EDF prefixes. Does not invent a 10-20 name for an unknown label."""

    label = raw.strip().upper()
    for prefix in ("EEG ", "EEG"):
        if label.startswith(prefix):
            label = label[len(prefix) :].strip()
    if label.endswith("-REF") or label.endswith("-LE"):
        label = label.rsplit("-", 1)[0]
    return ALIASES.get(label, label)


def is_canonical(raw: str) -> bool:
    label = normalize_label(raw)
    if label in CANONICAL_1020:
        return True
    if "-" in label:
        left, right = label.split("-", 1)
        return left in CANONICAL_1020 and right in CANONICAL_1020
    return False


def drop_noncanonical(names: list[str]) -> tuple[list[str], list[str]]:
    kept = [n for n in names if is_canonical(n)]
    dropped = [n for n in names if not is_canonical(n)]
    return kept, dropped
