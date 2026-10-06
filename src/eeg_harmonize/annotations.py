"""Controlled vocabulary plus the unmappable bucket."""

from __future__ import annotations

from pydantic import BaseModel

CONTROLLED = frozenset(
    {
        "seizure",
        "background",
        "artifact",
        "sleep_wake",
        "sleep_n1",
        "sleep_n2",
        "sleep_n3",
        "sleep_rem",
        "movement",
    }
)

DEFAULT_MAP = {
    "seizure": "seizure",
    "sez": "seizure",
    "bckg": "background",
    "interictal": "background",
    "eyem": "artifact",
    "chew": "artifact",
    "shiv": "artifact",
    "elpp": "artifact",
    "musc": "artifact",
}


class MappedTerm(BaseModel):
    raw: str
    controlled: str | None
    unmappable: bool


def map_term(raw: str) -> MappedTerm:
    key = raw.strip().lower()
    if raw in CONTROLLED:
        return MappedTerm(raw=raw, controlled=raw, unmappable=False)
    target = DEFAULT_MAP.get(key)
    if target is None:
        return MappedTerm(raw=raw, controlled=None, unmappable=True)
    return MappedTerm(raw=raw, controlled=target, unmappable=False)
